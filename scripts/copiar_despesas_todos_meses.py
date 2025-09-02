#!/usr/bin/env python3
"""
Script para copiar despesas apropriadas de TODOS OS MESES para lançamentos bancários.
Processa todas as empresas, todos os sócios, todos os meses disponíveis.
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

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


def obter_ou_criar_descricao_especifica(empresa, nome_descricao):
    """Obtém ou cria uma descrição específica para a empresa."""
    descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
        empresa=empresa,
        descricao=nome_descricao,
        defaults={
            'codigo_contabil': '999',
            'observacoes': f'Criado automaticamente para {nome_descricao}'
        }
    )
    return descricao


def obter_meio_pagamento_conta_corrente(empresa):
    """Obtém o meio de pagamento CONTA CORRENTE da empresa."""
    meio_pagamento = MeioPagamento.objects.filter(
        empresa=empresa,
        nome__icontains='CONTA CORRENTE'
    ).first()
    
    if not meio_pagamento:
        # Criar se não existir
        meio_pagamento = MeioPagamento.objects.create(
            empresa=empresa,
            nome='CONTA CORRENTE',
            codigo='CC001',
            ativo=True
        )
    
    return meio_pagamento


def obter_meses_com_despesas():
    """Obtém todos os meses que têm despesas no sistema."""
    print("=== BUSCANDO MESES COM DESPESAS ===")
    
    # Buscar meses únicos de DespesaSocio
    meses_socio = DespesaSocio.objects.dates('data', 'month', order='ASC')
    
    # Buscar meses únicos de DespesaRateada
    meses_rateada = DespesaRateada.objects.dates('data', 'month', order='ASC')
    
    # Combinar e remover duplicatas
    meses_unicos = set()
    for data in meses_socio:
        meses_unicos.add((data.year, data.month))
    for data in meses_rateada:
        meses_unicos.add((data.year, data.month))
    
    # Converter para lista ordenada
    meses_ordenados = sorted(list(meses_unicos))
    
    print(f"Meses com despesas encontrados: {len(meses_ordenados)}")
    for ano, mes in meses_ordenados:
        print(f"  -> {ano}-{mes:02d}")
    
    return meses_ordenados


def processar_despesas_mes_empresa(empresa_id, ano, mes):
    """Processa despesas de um mês específico de uma empresa."""
    print(f"\n--- Processando {ano}-{mes:02d} - Empresa {empresa_id} ---")
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, ativo=True)
    except Empresa.DoesNotExist:
        print(f"Empresa {empresa_id} não encontrada ou inativa")
        return 0
    
    # Buscar sócios ativos da empresa
    socios = Socio.objects.filter(empresa=empresa, ativo=True)
    if not socios.exists():
        print(f"Nenhum sócio ativo na empresa {empresa.name}")
        return 0
    
    print(f"Socios ativos: {socios.count()}")
    
    lancamentos_criados = 0
    meio_pagamento = obter_meio_pagamento_conta_corrente(empresa)
    
    for socio in socios:
        print(f"  Processando socio: {socio}")
        
        # 1. DESPESAS INDIVIDUAIS (DespesaSocio)
        despesas_individuais = DespesaSocio.objects.filter(
            socio=socio,
            data__year=ano,
            data__month=mes
        ).select_related('item_despesa')
        
        for despesa in despesas_individuais:
            if despesa.valor <= 0:
                continue
            
            # Verificar se já existe lançamento
            nome_descricao = f"Débito {despesa.item_despesa.descricao}"
            
            lancamento_existente = MovimentacaoContaCorrente.objects.filter(
                socio=socio,
                data_movimentacao=despesa.data,
                valor=-abs(despesa.valor),
                historico_complementar__contains=nome_descricao
            ).first()
            
            if lancamento_existente:
                print(f"    - Lançamento já existe (individual): {nome_descricao}")
                continue
            
            # Criar lançamento
            descricao_obj = obter_ou_criar_descricao_especifica(empresa, nome_descricao)
            
            MovimentacaoContaCorrente.objects.create(
                descricao_movimentacao=descricao_obj,
                socio=socio,
                data_movimentacao=despesa.data,
                valor=-abs(despesa.valor),  # Negativo = saída da conta
                instrumento_bancario=meio_pagamento,
                numero_documento_bancario='',
                historico_complementar=nome_descricao,
                created_by=None
            )
            
            lancamentos_criados += 1
            print(f"    + Criado (individual): {nome_descricao} - R$ {despesa.valor}")
        
        # 2. DESPESAS RATEADAS (DespesaRateada)
        despesas_rateadas = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa=empresa,
            data__year=ano,
            data__month=mes
        ).select_related('item_despesa')
        
        for despesa in despesas_rateadas:
            if despesa.valor <= 0:
                continue
            
            # Buscar rateio do sócio para esta despesa
            rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                despesa.item_despesa, socio, despesa.data
            )
            
            if not rateio or rateio.percentual_rateio <= 0:
                continue
            
            valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
            if valor_apropriado <= 0:
                continue
            
            # Verificar se já existe lançamento
            nome_descricao = f"Débito {despesa.item_despesa.descricao}"
            
            lancamento_existente = MovimentacaoContaCorrente.objects.filter(
                socio=socio,
                data_movimentacao=despesa.data,
                valor=-abs(valor_apropriado),
                historico_complementar__contains=nome_descricao
            ).first()
            
            if lancamento_existente:
                print(f"    - Lançamento já existe (rateada): {nome_descricao}")
                continue
            
            # Criar lançamento
            descricao_obj = obter_ou_criar_descricao_especifica(empresa, nome_descricao)
            
            MovimentacaoContaCorrente.objects.create(
                descricao_movimentacao=descricao_obj,
                socio=socio,
                data_movimentacao=despesa.data,
                valor=-abs(valor_apropriado),  # Negativo = saída da conta
                instrumento_bancario=meio_pagamento,
                numero_documento_bancario='',
                historico_complementar=f"{nome_descricao} (Rateio {rateio.percentual_rateio}%)",
                created_by=None
            )
            
            lancamentos_criados += 1
            print(f"    + Criado (rateada): {nome_descricao} - R$ {valor_apropriado} ({rateio.percentual_rateio}%)")
    
    print(f"Total de lançamentos criados no mes {ano}-{mes:02d}: {lancamentos_criados}")
    return lancamentos_criados


def main():
    """Função principal."""
    print("=" * 80)
    print("CÓPIA DE DESPESAS APROPRIADAS - TODOS OS MESES")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now()}")
    
    try:
        # 1. Buscar todas as empresas ativas
        empresas = Empresa.objects.filter(ativo=True).order_by('id')
        
        if not empresas.exists():
            print("Nenhuma empresa ativa encontrada")
            return
        
        print(f"\nEmpresas ativas: {empresas.count()}")
        for empresa in empresas:
            print(f"  -> {empresa.id}: {empresa.name}")
        
        # 2. Buscar todos os meses com despesas
        meses_com_despesas = obter_meses_com_despesas()
        
        if not meses_com_despesas:
            print("Nenhum mês com despesas encontrado")
            return
        
        # 3. Processar cada combinação empresa + mês
        total_geral = 0
        total_processamentos = len(empresas) * len(meses_com_despesas)
        processamento_atual = 0
        
        print(f"\n=== INICIANDO PROCESSAMENTO ===")
        print(f"Total de processamentos: {total_processamentos}")
        print(f"({len(empresas)} empresas × {len(meses_com_despesas)} meses)")
        
        for empresa in empresas:
            print(f"\n{'=' * 60}")
            print(f"EMPRESA: {empresa.id} - {empresa.name}")
            print(f"{'=' * 60}")
            
            total_empresa = 0
            
            for ano, mes in meses_com_despesas:
                processamento_atual += 1
                print(f"\nProgresso: {processamento_atual}/{total_processamentos}")
                
                with transaction.atomic():
                    lancamentos_mes = processar_despesas_mes_empresa(empresa.id, ano, mes)
                    total_empresa += lancamentos_mes
            
            print(f"\nTotal da empresa {empresa.name}: {total_empresa} lançamentos")
            total_geral += total_empresa
        
        # 4. Resultado final
        print(f"\n{'=' * 80}")
        print("RESULTADO FINAL")
        print(f"{'=' * 80}")
        print(f"Total de empresas processadas: {len(empresas)}")
        print(f"Total de meses processados: {len(meses_com_despesas)}")
        print(f"Total de lançamentos criados: {total_geral}")
        
        if total_geral > 0:
            print("\nSUCESSO: Despesas apropriadas copiadas para lançamentos bancários!")
        else:
            print("\nINFO: Nenhum lançamento novo foi necessário (já existem ou sem despesas)")
            
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
