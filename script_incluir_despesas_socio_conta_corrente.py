#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para incluir despesas de sócio como débitos no extrato da conta corrente.
Evita duplicações verificando se a despesa já foi incluída.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import (
    DespesaSocio, 
    MovimentacaoContaCorrente, 
    DescricaoMovimentacaoFinanceira,
    MeioPagamento,
    Socio,
    Empresa
)
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

def obter_ou_criar_descricao_movimentacao(empresa):
    """Obtém ou cria a descrição padrão para despesas de sócio"""
    descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
        empresa=empresa,
        descricao="Despesa de Sócio",
        defaults={
            'empresa': empresa,
            'descricao': "Despesa de Sócio",
            'codigo_contabil': '3.0.0.00.00',
            'observacoes': 'Descrição criada automaticamente para despesas de sócio'
        }
    )
    if created:
        print(f"✓ Criada nova descrição de movimentação: {descricao.descricao}")
    return descricao

def obter_meio_pagamento_padrao(empresa):
    """Obtém o meio de pagamento padrão ou cria um se necessário"""
    try:
        meio_pagamento = MeioPagamento.objects.filter(empresa=empresa, ativo=True).first()
        if not meio_pagamento:
            meio_pagamento = MeioPagamento.objects.create(
                empresa=empresa,
                codigo="DEBITO_AUTO",
                nome="Débito Automático",
                observacoes="Débito automático para despesas de sócio",
                ativo=True
            )
            print(f"✓ Criado novo meio de pagamento: {meio_pagamento.nome}")
        return meio_pagamento
    except Exception as e:
        print(f"⚠ Erro ao obter meio de pagamento: {e}")
        return None

def verificar_despesa_ja_incluida(despesa_socio):
    """Verifica se a despesa já foi incluída no extrato da conta corrente"""
    existe = MovimentacaoContaCorrente.objects.filter(
        socio=despesa_socio.socio,
        data_movimentacao=despesa_socio.data,
        valor=-abs(despesa_socio.valor),  # Negativo para débito (saída da conta)
        historico_complementar__icontains=f"Despesa ID: {despesa_socio.id}"
    ).exists()
    return existe

def incluir_despesa_no_extrato(despesa_socio, descricao_movimentacao, meio_pagamento):
    """Inclui uma despesa de sócio como débito no extrato da conta corrente"""
    try:
        # Verifica se já existe
        if verificar_despesa_ja_incluida(despesa_socio):
            return False, f"Despesa ID {despesa_socio.id} já incluída no extrato"
        
        # Cria a movimentação como débito (valor negativo = saída da conta)
        movimentacao = MovimentacaoContaCorrente.objects.create(
            descricao_movimentacao=descricao_movimentacao,
            instrumento_bancario=meio_pagamento,
            socio=despesa_socio.socio,
            data_movimentacao=despesa_socio.data,
            valor=-abs(despesa_socio.valor),  # Negativo para débito (saída da conta)
            numero_documento_bancario="",
            historico_complementar=f"Despesa de Sócio - {despesa_socio.item_despesa.descricao if despesa_socio.item_despesa else 'N/A'} - Despesa ID: {despesa_socio.id}",
            conciliado=False,
            data_conciliacao=None
        )
        
        return True, f"Despesa ID {despesa_socio.id} incluída como movimentação ID {movimentacao.id}"
        
    except Exception as e:
        return False, f"Erro ao incluir despesa ID {despesa_socio.id}: {str(e)}"

def processar_despesas_socio(empresa_id=None, socio_id=None, mes=None, ano=None):
    """Processa as despesas de sócio e inclui no extrato da conta corrente"""
    
    print("=" * 80)
    print("SCRIPT: Incluir Despesas de Sócio no Extrato da Conta Corrente")
    print("=" * 80)
    
    # Filtros para as despesas
    filtros = {}
    empresa = None
    
    if empresa_id:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            filtros['socio__empresa'] = empresa
            print(f"📊 Filtro: Empresa {empresa.nome_fantasia or f'ID {empresa.id}'}")
        except Empresa.DoesNotExist:
            print(f"❌ Empresa ID {empresa_id} não encontrada")
            return
    
    if socio_id:
        try:
            socio = Socio.objects.get(id=socio_id)
            filtros['socio'] = socio
            # Se não foi especificada empresa, usar a empresa do sócio
            if not empresa:
                empresa = socio.empresa
            socio_nome = getattr(getattr(socio, 'pessoa', None), 'name', str(socio))
            print(f"👤 Filtro: Sócio {socio_nome}")
        except Socio.DoesNotExist:
            print(f"❌ Sócio ID {socio_id} não encontrado")
            return
    
    # Se não especificou empresa, tentar usar a primeira empresa disponível
    if not empresa:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada no sistema")
            return
    
    if mes and ano:
        filtros['data__month'] = mes
        filtros['data__year'] = ano
        print(f"📅 Filtro: {mes:02d}/{ano}")
    elif ano:
        filtros['data__year'] = ano
        print(f"📅 Filtro: Ano {ano}")
    
    # Buscar despesas de sócio
    despesas = DespesaSocio.objects.filter(**filtros).order_by('data', 'socio__id')
    total_despesas = despesas.count()
    
    if total_despesas == 0:
        print("⚠ Nenhuma despesa de sócio encontrada com os filtros especificados")
        return
    
    print(f"📋 Total de despesas encontradas: {total_despesas}")
    print()
    
    # Obter configurações necessárias
    descricao_movimentacao = obter_ou_criar_descricao_movimentacao(empresa)
    meio_pagamento = obter_meio_pagamento_padrao(empresa)
    
    if not meio_pagamento:
        print("❌ Não foi possível obter/criar meio de pagamento")
        return
    
    # Processar cada despesa
    sucessos = 0
    ja_incluidas = 0
    erros = 0
    
    print("Processando despesas...")
    print("-" * 80)
    
    with transaction.atomic():
        for i, despesa in enumerate(despesas, 1):
            socio_nome = getattr(getattr(despesa.socio, 'pessoa', None), 'name', str(despesa.socio))
            item_desc = despesa.item_despesa.descricao if despesa.item_despesa else 'N/A'
            
            sucesso, mensagem = incluir_despesa_no_extrato(despesa, descricao_movimentacao, meio_pagamento)
            
            if sucesso:
                sucessos += 1
                status = "✓"
            elif "já incluída" in mensagem:
                ja_incluidas += 1
                status = "⚠"
            else:
                erros += 1
                status = "❌"
            
            print(f"{status} [{i:3d}/{total_despesas}] {despesa.data} | {socio_nome} | R$ {despesa.valor:,.2f} | {item_desc}")
            if not sucesso and "já incluída" not in mensagem:
                print(f"    └─ {mensagem}")
    
    # Resumo final
    print("-" * 80)
    print("RESUMO:")
    print(f"✓ Incluídas com sucesso: {sucessos}")
    print(f"⚠ Já existiam no extrato: {ja_incluidas}")
    print(f"❌ Erros: {erros}")
    print(f"📊 Total processadas: {sucessos + ja_incluidas + erros}")
    print("=" * 80)

if __name__ == "__main__":
    import argparse
    
    print("🚀 Iniciando script...")
    
    parser = argparse.ArgumentParser(description="Inclui despesas de sócio no extrato da conta corrente")
    parser.add_argument("--empresa-id", type=int, help="ID da empresa (opcional)")
    parser.add_argument("--socio-id", type=int, help="ID do sócio (opcional)")
    parser.add_argument("--mes", type=int, help="Mês (1-12) (opcional)")
    parser.add_argument("--ano", type=int, help="Ano (opcional)")
    parser.add_argument("--todos", action="store_true", help="Processar todas as despesas (sem filtros)")
    
    args = parser.parse_args()
    
    if not any([args.empresa_id, args.socio_id, args.mes, args.ano, args.todos]):
        print("⚠ Especifique pelo menos um filtro ou use --todos para processar todas as despesas")
        print("Exemplos:")
        print("  python script_incluir_despesas_socio_conta_corrente.py --empresa-id 1")
        print("  python script_incluir_despesas_socio_conta_corrente.py --socio-id 5")
        print("  python script_incluir_despesas_socio_conta_corrente.py --mes 7 --ano 2025")
        print("  python script_incluir_despesas_socio_conta_corrente.py --todos")
        sys.exit(1)
    
    try:
        processar_despesas_socio(
            empresa_id=args.empresa_id,
            socio_id=args.socio_id,
            mes=args.mes,
            ano=args.ano
        )
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        sys.exit(1)
