#!/usr/bin/env python3
"""
Script simples para copiar despesas apropriadas sem emojis Unicode.
Evita problemas de encoding no terminal Windows.
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.base import Empresa, Socio
from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento

def copiar_despesas_apropriadas(empresa_id, competencia="2025-08"):
    """Copia despesas apropriadas para conta corrente (sem emojis)."""
    print(f"=== PROCESSANDO EMPRESA {empresa_id} ===")
    
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        print(f"Empresa: {empresa.name}")
        
        # Parse da competência
        ano, mes = competencia.split('-')
        ano, mes = int(ano), int(mes)
        
        # Buscar todos os sócios ativos da empresa
        socios = Socio.objects.filter(empresa=empresa, ativo=True)
        print(f"Socios ativos: {socios.count()}")
        
        if not socios.exists():
            print("Nenhum socio ativo encontrado")
            return 0
        
        # Buscar instrumento CONTA CORRENTE
        conta_corrente = MeioPagamento.objects.filter(
            empresa=empresa,
            descricao__icontains='CONTA CORRENTE'
        ).first()
        
        if not conta_corrente:
            print("ERRO: Instrumento CONTA CORRENTE nao encontrado")
            return 0
        
        total_criados = 0
        
        for socio in socios:
            print(f"\n--- Processando socio: {socio} ---")
            
            # 1. Despesas individuais (DespesaSocio)
            despesas_individuais = DespesaSocio.objects.filter(
                socio=socio,
                data__year=ano,
                data__month=mes
            ).select_related('item_despesa')
            
            print(f"Despesas individuais: {despesas_individuais.count()}")
            
            for despesa in despesas_individuais:
                # Verificar se já existe lançamento
                historico_busca = f"Debito {despesa.item_despesa.descricao}"
                lancamento_existe = MovimentacaoContaCorrente.objects.filter(
                    socio=socio,
                    data_movimentacao=despesa.data,
                    historico_complementar__contains=historico_busca,
                    valor=-abs(despesa.valor)
                ).exists()
                
                if lancamento_existe:
                    print(f"  Ja existe: {historico_busca}")
                    continue
                
                # Criar descrição específica
                descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
                    empresa=empresa,
                    descricao=f"Debito {despesa.item_despesa.descricao}",
                    defaults={'created_by': None}
                )
                
                # Criar lançamento
                with transaction.atomic():
                    MovimentacaoContaCorrente.objects.create(
                        descricao_movimentacao=descricao,
                        socio=socio,
                        data_movimentacao=despesa.data,
                        valor=-abs(despesa.valor),  # Negativo = saída
                        instrumento_bancario=conta_corrente,
                        numero_documento_bancario='',
                        historico_complementar=historico_busca,
                        created_by=None
                    )
                
                print(f"  CRIADO: {historico_busca} - R$ {despesa.valor}")
                total_criados += 1
            
            # 2. Despesas rateadas (DespesaRateada + rateio)
            despesas_rateadas = DespesaRateada.objects.filter(
                item_despesa__grupo_despesa__empresa=empresa,
                data__year=ano,
                data__month=mes
            ).select_related('item_despesa')
            
            print(f"Despesas rateadas a verificar: {despesas_rateadas.count()}")
            
            for despesa in despesas_rateadas:
                # Buscar rateio do sócio para esta despesa
                rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                    despesa.item_despesa, socio, despesa.data
                )
                
                if not rateio or rateio.percentual_rateio <= 0:
                    continue
                
                # Calcular valor apropriado
                valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
                
                # Verificar se já existe lançamento
                historico_busca = f"Debito {despesa.item_despesa.descricao}"
                lancamento_existe = MovimentacaoContaCorrente.objects.filter(
                    socio=socio,
                    data_movimentacao=despesa.data,
                    historico_complementar__contains=historico_busca,
                    valor=-abs(valor_apropriado)
                ).exists()
                
                if lancamento_existe:
                    print(f"  Ja existe: {historico_busca} (rateado)")
                    continue
                
                # Criar descrição específica
                descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
                    empresa=empresa,
                    descricao=f"Debito {despesa.item_despesa.descricao}",
                    defaults={'created_by': None}
                )
                
                # Criar lançamento
                with transaction.atomic():
                    MovimentacaoContaCorrente.objects.create(
                        descricao_movimentacao=descricao,
                        socio=socio,
                        data_movimentacao=despesa.data,
                        valor=-abs(valor_apropriado),  # Negativo = saída
                        instrumento_bancario=conta_corrente,
                        numero_documento_bancario='',
                        historico_complementar=f"{historico_busca} (Rateio {rateio.percentual_rateio}%)",
                        created_by=None
                    )
                
                print(f"  CRIADO: {historico_busca} - R$ {valor_apropriado} ({rateio.percentual_rateio}%)")
                total_criados += 1
        
        print(f"\n=== EMPRESA {empresa_id} CONCLUIDA ===")
        print(f"Total de lancamentos criados: {total_criados}")
        return total_criados
        
    except Exception as e:
        print(f"ERRO na empresa {empresa_id}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Executa para todas as empresas ativas."""
    print("=== COPIANDO DESPESAS APROPRIADAS - TODAS AS EMPRESAS ===")
    print(f"Data/Hora: {datetime.now()}")
    
    # Buscar empresas ativas
    empresas = Empresa.objects.filter(ativo=True).order_by('id')
    print(f"Empresas ativas: {empresas.count()}")
    
    if not empresas.exists():
        print("Nenhuma empresa ativa encontrada")
        return
    
    total_geral = 0
    
    for empresa in empresas:
        criados = copiar_despesas_apropriadas(empresa.id, "2025-08")
        total_geral += criados
    
    print(f"\n=== RESULTADO FINAL ===")
    print(f"Total de lancamentos criados: {total_geral}")

if __name__ == "__main__":
    main()
