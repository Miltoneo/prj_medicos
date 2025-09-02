#!/usr/bin/env python3
"""
Script para incluir despesas de sócio como lançamentos bancários na conta corrente.

Características:
- Evita duplicações verificando se já existe lançamento para a despesa
- Descrição do lançamento: "Débito: " + descrição da despesa
- Filtra apenas despesas apropriadas para sócio
- Gera relatório detalhado das operações

Autor: Sistema prj_medicos
Data: Setembro 2025
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import (
    DespesaSocio, 
    MovimentacaoContaCorrente, 
    DescricaoMovimentacaoFinanceira,
    MeioPagamento,
    Socio,
    Empresa,
    ItemDespesa,
    GrupoDespesa
)
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist


def obter_ou_criar_descricao_movimentacao(empresa):
    """Obtém ou cria a descrição padrão para lançamentos de despesas de sócio"""
    descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
        empresa=empresa,
        descricao="Despesa de Sócio",
        defaults={
            'empresa': empresa,
            'descricao': "Despesa de Sócio",
            'codigo_contabil': '3.1.0.00.00',  # Código para despesas de sócio
            'observacoes': 'Lançamentos automáticos de despesas de sócio na conta corrente'
        }
    )
    if created:
        print(f"✓ Criada nova descrição de movimentação: {descricao.descricao}")
    else:
        print(f"✓ Usando descrição existente: {descricao.descricao}")
    return descricao


def obter_meio_pagamento_padrao(empresa):
    """Obtém o meio de pagamento padrão ou cria um se necessário"""
    try:
        # Tentar encontrar um meio de pagamento ativo
        meio_pagamento = MeioPagamento.objects.filter(
            empresa=empresa, 
            ativo=True
        ).first()
        
        if not meio_pagamento:
            meio_pagamento = MeioPagamento.objects.create(
                empresa=empresa,
                codigo="DEBITO_SOCIO",
                nome="Débito Sócio",
                observacoes="Meio de pagamento automático para despesas de sócio",
                ativo=True
            )
            print(f"✓ Criado novo meio de pagamento: {meio_pagamento.nome}")
        else:
            print(f"✓ Usando meio de pagamento existente: {meio_pagamento.nome}")
        
        return meio_pagamento
        
    except Exception as e:
        print(f"❌ Erro ao obter meio de pagamento: {e}")
        return None


def verificar_lancamento_ja_existe(despesa_socio):
    """
    Verifica se já existe um lançamento bancário para esta despesa específica.
    Usa múltiplos critérios para evitar duplicações.
    """
    # Verificar por ID da despesa no histórico complementar
    existe_por_id = MovimentacaoContaCorrente.objects.filter(
        socio=despesa_socio.socio,
        historico_complementar__icontains=f"Despesa ID: {despesa_socio.id}"
    ).exists()
    
    if existe_por_id:
        return True, "ID da despesa encontrado no histórico"
    
    # Verificar por combinação única (sócio + data + valor + descrição)
    item_desc = despesa_socio.item_despesa.descricao if despesa_socio.item_despesa else 'N/A'
    existe_por_combinacao = MovimentacaoContaCorrente.objects.filter(
        socio=despesa_socio.socio,
        data_movimentacao=despesa_socio.data,
        valor=-abs(despesa_socio.valor),  # Valor negativo (débito = saída)
        historico_complementar__icontains=item_desc
    ).exists()
    
    if existe_por_combinacao:
        return True, "Combinação sócio+data+valor+descrição já existe"
    
    return False, "Não existe lançamento para esta despesa"


def criar_lancamento_bancario(despesa_socio, descricao_movimentacao, meio_pagamento):
    """
    Cria um lançamento bancário para a despesa de sócio.
    Descrição: "Débito: " + descrição da despesa
    """
    try:
        # Verificar se já existe
        ja_existe, motivo = verificar_lancamento_ja_existe(despesa_socio)
        if ja_existe:
            return False, f"Despesa ID {despesa_socio.id} já possui lançamento: {motivo}"
        
        # Preparar a descrição conforme solicitado
        item_desc = despesa_socio.item_despesa.descricao if despesa_socio.item_despesa else 'Despesa de Sócio'
        descricao_debito = f"Débito: {item_desc}"
        
        # Criar o lançamento bancário
        movimentacao = MovimentacaoContaCorrente.objects.create(
            descricao_movimentacao=descricao_movimentacao,
            instrumento_bancario=meio_pagamento,
            socio=despesa_socio.socio,
            data_movimentacao=despesa_socio.data,
            valor=-abs(despesa_socio.valor),  # Negativo = débito = saída da conta
            numero_documento_bancario="",
            historico_complementar=f"{descricao_debito} - Despesa ID: {despesa_socio.id}",
            conciliado=False,
            data_conciliacao=None
        )
        
        return True, f"Lançamento criado: ID {movimentacao.id}, Valor: R$ {abs(despesa_socio.valor):,.2f}"
        
    except Exception as e:
        return False, f"Erro ao criar lançamento para despesa ID {despesa_socio.id}: {str(e)}"


def filtrar_despesas_apropriadas():
    """
    Filtra apenas as despesas apropriadas para inclusão como lançamentos bancários.
    Considera apenas despesas de sócio válidas e ativas.
    """
    print("🔍 Filtrando despesas apropriadas para inclusão...")
    
    # Filtrar despesas de sócio válidas
    despesas = DespesaSocio.objects.select_related(
        'socio', 
        'socio__pessoa', 
        'socio__empresa',
        'item_despesa',
        'item_despesa__grupo_despesa'
    ).filter(
        socio__ativo=True,  # Apenas sócios ativos
        item_despesa__isnull=False,  # Deve ter item de despesa
        valor__gt=0  # Valor positivo
    ).order_by('socio__empresa', 'socio', 'data')
    
    total_despesas = despesas.count()
    
    if total_despesas == 0:
        print("⚠️  Nenhuma despesa apropriada encontrada")
        return despesas
    
    print(f"📊 Total de despesas encontradas: {total_despesas}")
    
    # Agrupar por empresa
    empresas = {}
    for despesa in despesas:
        empresa_nome = despesa.socio.empresa.nome_fantasia or f"Empresa ID {despesa.socio.empresa.id}"
        if empresa_nome not in empresas:
            empresas[empresa_nome] = 0
        empresas[empresa_nome] += 1
    
    print("📋 Resumo por empresa:")
    for empresa_nome, quantidade in empresas.items():
        print(f"   • {empresa_nome}: {quantidade} despesas")
    
    return despesas


def processar_despesas_para_lancamentos():
    """
    Processa todas as despesas apropriadas e cria lançamentos bancários.
    """
    print("=" * 80)
    print("SCRIPT: Incluir Despesas de Sócio como Lançamentos Bancários")
    print("=" * 80)
    print(f"📅 Data/Hora de execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # 1. Filtrar despesas apropriadas
    despesas = filtrar_despesas_apropriadas()
    
    if not despesas.exists():
        print("✅ Script finalizado: Nenhuma despesa para processar")
        return
    
    # 2. Processar por empresa
    empresas_processadas = set()
    sucessos = 0
    ja_existentes = 0
    erros = 0
    
    print("\n🔄 Iniciando processamento...")
    print("-" * 80)
    
    with transaction.atomic():
        for i, despesa in enumerate(despesas, 1):
            empresa = despesa.socio.empresa
            socio_nome = getattr(getattr(despesa.socio, 'pessoa', None), 'name', str(despesa.socio))
            item_desc = despesa.item_despesa.descricao if despesa.item_despesa else 'N/A'
            
            # Obter configurações para esta empresa (uma vez por empresa)
            if empresa.id not in empresas_processadas:
                descricao_movimentacao = obter_ou_criar_descricao_movimentacao(empresa)
                meio_pagamento = obter_meio_pagamento_padrao(empresa)
                
                if not meio_pagamento:
                    print(f"❌ Erro: Não foi possível obter meio de pagamento para empresa {empresa.nome_fantasia}")
                    continue
                
                empresas_processadas.add(empresa.id)
                print(f"✓ Configurações obtidas para empresa: {empresa.nome_fantasia or f'ID {empresa.id}'}")
            
            # Criar o lançamento bancário
            sucesso, mensagem = criar_lancamento_bancario(despesa, descricao_movimentacao, meio_pagamento)
            
            if sucesso:
                sucessos += 1
                status = "✅"
            elif "já possui lançamento" in mensagem:
                ja_existentes += 1
                status = "⚠️ "
            else:
                erros += 1
                status = "❌"
            
            # Mostrar progresso
            print(f"{status} [{i:4d}/{len(despesas)}] {despesa.data} | {socio_nome} | R$ {despesa.valor:,.2f} | {item_desc}")
            
            # Mostrar detalhes dos erros
            if not sucesso and "já possui lançamento" not in mensagem:
                print(f"      └─ {mensagem}")
    
    # 3. Resumo final
    print("-" * 80)
    print("📊 RESUMO FINAL:")
    print(f"✅ Lançamentos criados: {sucessos}")
    print(f"⚠️  Já existiam: {ja_existentes}")
    print(f"❌ Erros: {erros}")
    print(f"📈 Total processado: {sucessos + ja_existentes + erros}")
    print(f"📅 Data/Hora de conclusão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)


def main():
    """Função principal do script"""
    try:
        processar_despesas_para_lancamentos()
    except Exception as e:
        print(f"❌ Erro crítico durante a execução: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
