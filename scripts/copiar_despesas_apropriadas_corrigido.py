#!/usr/bin/env python3
"""
Script para copiar despesas apropriadas de todas as empresas para lançamentos bancários.
Versão simplificada sem emojis para compatibilidade com Windows.
"""

import os
import sys
import django
from datetime import datetime

# Adicionar o diretório pai ao PYTHONPATH para encontrar o módulo prj_medicos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.base import Empresa, Socio
from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento

def obter_ou_criar_descricao_especifica(empresa, descricao_texto):
    """
    Obtém ou cria uma descrição específica para movimentação financeira.
    """
    try:
        # Buscar primeiro por código único para evitar duplicatas
        codigo_base = f"DEB-{descricao_texto.replace(' ', '').replace('-', '').upper()}"
        
        descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
            empresa=empresa,
            nome=descricao_texto,  # Campo correto é 'nome'
            defaults={
                'codigo_contabil': codigo_base,
                'ativo': True
            }
        )
        return descricao
    except Exception as e:
        print(f"Erro ao criar/obter descrição '{descricao_texto}': {e}")
        # Fallback: buscar uma descrição genérica
        return DescricaoMovimentacaoFinanceira.objects.filter(
            empresa=empresa,
            ativo=True
        ).first()

def obter_conta_corrente_instrumento(empresa):
    """
    Obtém o instrumento bancário padrão (Conta Corrente).
    """
    try:
        # Buscar meio de pagamento "Conta Corrente"
        conta_corrente = MeioPagamento.objects.filter(
            empresa=empresa,
            nome__icontains='conta corrente'
        ).first()
        
        if not conta_corrente:
            # Criar se não existir
            conta_corrente = MeioPagamento.objects.create(
                empresa=empresa,
                nome='CONTA CORRENTE',
                codigo='CC001',
                ativo=True
            )
            
        return conta_corrente
    except Exception as e:
        print(f"Erro ao obter conta corrente: {e}")
        return None

def processar_despesas_socio(empresa, competencia_ano, competencia_mes):
    """
    Processa despesas individuais de sócios.
    """
    print(f"  Processando despesas de socio...")
    
    despesas_socio = DespesaSocio.objects.filter(
        socio__empresa=empresa,
        socio__ativo=True,
        data__year=competencia_ano,
        data__month=competencia_mes,
        valor__gt=0
    ).select_related('socio', 'item_despesa')
    
    count_socio = despesas_socio.count()
    print(f"    Despesas de socio encontradas: {count_socio}")
    
    lancamentos_criados = 0
    
    for despesa in despesas_socio:
        try:
            # Verificar se já existe lançamento
            descricao_busca = f"Debito {despesa.item_despesa.nome}"
            
            lancamento_existente = MovimentacaoContaCorrente.objects.filter(
                socio=despesa.socio,
                data_movimentacao=despesa.data,
                historico_complementar__contains=descricao_busca,
                valor=-abs(despesa.valor)
            ).first()
            
            if lancamento_existente:
                continue  # Já existe
            
            # Criar descrição específica
            descricao_obj = obter_ou_criar_descricao_especifica(
                empresa, f"Debito {despesa.item_despesa.nome}"
            )
            
            # Obter instrumento bancário
            instrumento = obter_conta_corrente_instrumento(empresa)
            
            # Criar lançamento
            MovimentacaoContaCorrente.objects.create(
                descricao_movimentacao=descricao_obj,
                socio=despesa.socio,
                data_movimentacao=despesa.data,
                valor=-abs(despesa.valor),  # Negativo = saída
                instrumento_bancario=instrumento,
                historico_complementar=f"Debito {despesa.item_despesa.nome}",
                created_by=None
            )
            
            lancamentos_criados += 1
            
        except Exception as e:
            print(f"    Erro ao processar despesa socio ID {despesa.id}: {e}")
            continue
    
    return lancamentos_criados

def processar_despesas_rateadas(empresa, competencia_ano, competencia_mes):
    """
    Processa despesas rateadas.
    """
    print(f"  Processando despesas rateadas...")
    
    # Buscar despesas rateadas do período
    despesas_rateadas = DespesaRateada.objects.filter(
        item_despesa__grupo_despesa__empresa=empresa,
        data__year=competencia_ano,
        data__month=competencia_mes,
        valor__gt=0
    ).select_related('item_despesa')
    
    count_rateadas = despesas_rateadas.count()
    print(f"    Despesas rateadas encontradas: {count_rateadas}")
    
    lancamentos_criados = 0
    
    for despesa in despesas_rateadas:
        try:
            # Buscar configurações de rateio para o período
            data_ref = despesa.data.replace(day=1)
            
            rateios = ItemDespesaRateioMensal.objects.filter(
                item_despesa=despesa.item_despesa,
                data_referencia=data_ref,
                ativo=True,
                percentual_rateio__gt=0,
                socio__ativo=True
            ).select_related('socio')
            
            for rateio in rateios:
                # Calcular valor apropriado
                valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
                
                if valor_apropriado <= 0:
                    continue
                
                # Verificar se já existe lançamento
                descricao_busca = f"Debito {despesa.item_despesa.nome}"
                
                lancamento_existente = MovimentacaoContaCorrente.objects.filter(
                    socio=rateio.socio,
                    data_movimentacao=despesa.data,
                    historico_complementar__contains=descricao_busca,
                    valor=-abs(valor_apropriado)
                ).first()
                
                if lancamento_existente:
                    continue  # Já existe
                
                # Criar descrição específica
                descricao_obj = obter_ou_criar_descricao_especifica(
                    empresa, f"Debito {despesa.item_despesa.nome}"
                )
                
                # Obter instrumento bancário
                instrumento = obter_conta_corrente_instrumento(empresa)
                
                # Criar lançamento
                MovimentacaoContaCorrente.objects.create(
                    descricao_movimentacao=descricao_obj,
                    socio=rateio.socio,
                    data_movimentacao=despesa.data,
                    valor=-abs(valor_apropriado),  # Negativo = saída
                    instrumento_bancario=instrumento,
                    historico_complementar=f"Debito {despesa.item_despesa.nome} (Rateio {rateio.percentual_rateio}%)",
                    created_by=None
                )
                
                lancamentos_criados += 1
                
        except Exception as e:
            print(f"    Erro ao processar despesa rateada ID {despesa.id}: {e}")
            continue
    
    return lancamentos_criados

def processar_empresa(empresa, competencia="2025-08"):
    """
    Processa uma empresa específica.
    """
    try:
        # Parse da competência
        competencia_ano, competencia_mes = competencia.split('-')
        competencia_ano = int(competencia_ano)
        competencia_mes = int(competencia_mes)
        
        print(f"\nProcessando Empresa ID {empresa.id}: {empresa.name}")
        print(f"Competencia: {competencia_mes:02d}/{competencia_ano}")
        
        total_lancamentos = 0
        
        with transaction.atomic():
            # Processar despesas de sócio
            count_socio = processar_despesas_socio(empresa, competencia_ano, competencia_mes)
            total_lancamentos += count_socio
            
            # Processar despesas rateadas
            count_rateadas = processar_despesas_rateadas(empresa, competencia_ano, competencia_mes)
            total_lancamentos += count_rateadas
        
        print(f"  Total de lancamentos criados: {total_lancamentos}")
        return total_lancamentos
        
    except Exception as e:
        print(f"  Erro ao processar empresa {empresa.id}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """
    Função principal.
    """
    print("=" * 80)
    print("SCRIPT: Copiar Despesas Apropriadas para Conta Corrente")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    try:
        # Buscar todas as empresas ativas
        empresas = Empresa.objects.filter(ativo=True).order_by('id')
        
        if not empresas.exists():
            print("Nenhuma empresa ativa encontrada")
            return
        
        print(f"Empresas ativas encontradas: {empresas.count()}")
        for empresa in empresas:
            print(f"  ID {empresa.id}: {empresa.name}")
        
        # Processar cada empresa
        total_geral = 0
        sucessos = 0
        falhas = 0
        
        for empresa in empresas:
            try:
                count = processar_empresa(empresa, "2025-08")
                total_geral += count
                sucessos += 1
            except Exception as e:
                print(f"Falha na empresa {empresa.id}: {e}")
                falhas += 1
        
        # Resultado final
        print("\n" + "=" * 80)
        print("RESULTADO FINAL")
        print("=" * 80)
        print(f"Empresas processadas: {sucessos}")
        print(f"Empresas com falha: {falhas}")
        print(f"Total de lancamentos criados: {total_geral}")
        
        if falhas == 0:
            print("SUCESSO: Todas as empresas processadas!")
        else:
            print(f"ATENCAO: {falhas} empresas falharam")
            
    except Exception as e:
        print(f"Erro critico: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
