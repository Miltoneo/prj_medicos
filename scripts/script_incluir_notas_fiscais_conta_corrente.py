#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para incluir receitas de notas fiscais recebidas como créditos no extrato da conta corrente.
Considera apenas notas fiscais efetivamente recebidas (status='recebido' e dtRecebimento preenchida).
Usa o meio de pagamento específico da nota fiscal.
Evita duplicações verificando se o rateio já foi incluído.
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
    NotaFiscalRateioMedico,
    MovimentacaoContaCorrente, 
    DescricaoMovimentacaoFinanceira,
    MeioPagamento,
    Socio,
    Empresa
)
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

def obter_ou_criar_descricao_movimentacao(empresa):
    """Obtém ou cria a descrição padrão para receitas de notas fiscais"""
    descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
        empresa=empresa,
        descricao="Receita de Nota Fiscal",
        defaults={
            'empresa': empresa,
            'descricao': "Receita de Nota Fiscal",
            'codigo_contabil': '1.1.0.00.00',
            'observacoes': 'Descrição criada automaticamente para receitas de notas fiscais'
        }
    )
    if created:
        print(f"✓ Criada nova descrição de movimentação: {descricao.descricao}")
    return descricao

def obter_meio_pagamento_da_nota_fiscal(nota_fiscal, empresa):
    """Obtém o meio de pagamento específico da nota fiscal ou usa padrão"""
    try:
        # Usar o meio de pagamento específico da nota fiscal se existir
        if hasattr(nota_fiscal, 'meio_pagamento') and nota_fiscal.meio_pagamento:
            return nota_fiscal.meio_pagamento
        
        # Buscar meio de pagamento padrão da empresa
        meio_pagamento = MeioPagamento.objects.filter(empresa=empresa, ativo=True).first()
        
        if not meio_pagamento:
            # Criar meio de pagamento padrão se não existir
            meio_pagamento = MeioPagamento.objects.create(
                empresa=empresa,
                codigo="PIX",
                nome="PIX",
                observacoes="Meio de pagamento padrão para notas fiscais",
                ativo=True
            )
            print(f"✓ Criado novo meio de pagamento padrão: {meio_pagamento.nome}")
        
        return meio_pagamento
        
    except Exception as e:
        print(f"⚠ Erro ao obter meio de pagamento: {e}")
        return None

def verificar_rateio_ja_incluido(rateio):
    """Verifica se o rateio da nota fiscal já foi incluído no extrato da conta corrente"""
    existe = MovimentacaoContaCorrente.objects.filter(
        socio=rateio.medico,
        data_movimentacao=rateio.nota_fiscal.dtRecebimento,
        valor=abs(rateio.valor_liquido_medico),
        historico_complementar__icontains=f"Rateio NF ID: {rateio.id}"
    ).exists()
    return existe

def incluir_rateio_no_extrato(rateio, descricao_movimentacao, empresa):
    """Inclui um rateio de nota fiscal como crédito no extrato da conta corrente"""
    try:
        # Verifica se já existe
        if verificar_rateio_ja_incluido(rateio):
            return False, f"Rateio NF ID {rateio.id} já incluído no extrato"
        
        # Verifica se tem valor válido
        if not rateio.valor_liquido_medico or rateio.valor_liquido_medico <= 0:
            return False, f"Rateio NF ID {rateio.id} sem valor líquido válido"
        
        # Verifica se a nota fiscal foi efetivamente recebida
        if not rateio.nota_fiscal.dtRecebimento:
            return False, f"Rateio NF ID {rateio.id} - Nota fiscal ainda não recebida"
        
        if rateio.nota_fiscal.status_recebimento != 'recebido':
            return False, f"Rateio NF ID {rateio.id} - Status: {rateio.nota_fiscal.status_recebimento}"
        
        # Obter meio de pagamento específico da nota fiscal
        meio_pagamento = obter_meio_pagamento_da_nota_fiscal(rateio.nota_fiscal, empresa)
        if not meio_pagamento:
            return False, f"Rateio NF ID {rateio.id} - Não foi possível obter meio de pagamento"
        
        # Cria a movimentação como crédito (valor positivo = entrada na conta)
        movimentacao = MovimentacaoContaCorrente.objects.create(
            descricao_movimentacao=descricao_movimentacao,
            instrumento_bancario=meio_pagamento,
            nota_fiscal=rateio.nota_fiscal,
            socio=rateio.medico,
            data_movimentacao=rateio.nota_fiscal.dtRecebimento,
            valor=abs(rateio.valor_liquido_medico),  # Positivo para crédito (entrada na conta)
            numero_documento_bancario=rateio.nota_fiscal.numero or "",
            historico_complementar=f"Receita de Nota Fiscal - NF {rateio.nota_fiscal.numero} - Valor Rateado: R$ {rateio.valor_liquido_medico} - Rateio NF ID: {rateio.id}",
            conciliado=False,
            data_conciliacao=None
        )
        
        return True, f"Rateio NF ID {rateio.id} incluído como movimentação ID {movimentacao.id} com {meio_pagamento.nome}"
        
    except Exception as e:
        return False, f"Erro ao incluir Rateio NF ID {rateio.id}: {str(e)}"

def processar_receitas_notas_fiscais(empresa_id=None, socio_id=None, mes=None, ano=None):
    """Processa as receitas de notas fiscais e inclui no extrato da conta corrente"""
    
    print("=" * 80)
    print("SCRIPT: Incluir Receitas de Notas Fiscais no Extrato da Conta Corrente")
    print("=" * 80)
    
    # Filtros para os rateios
    filtros = {}
    empresa = None
    
    if empresa_id:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            filtros['medico__empresa'] = empresa
            print(f"📊 Filtro: Empresa {empresa.nome_fantasia or f'ID {empresa.id}'}")
        except Empresa.DoesNotExist:
            print(f"❌ Empresa ID {empresa_id} não encontrada")
            return
    
    if socio_id:
        try:
            socio = Socio.objects.get(id=socio_id)
            filtros['medico'] = socio
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
        filtros['nota_fiscal__dtRecebimento__month'] = mes
        filtros['nota_fiscal__dtRecebimento__year'] = ano
        print(f"📅 Filtro: {mes:02d}/{ano}")
    elif ano:
        filtros['nota_fiscal__dtRecebimento__year'] = ano
        print(f"📅 Filtro: Ano {ano}")
    
    # Buscar rateios de notas fiscais EFETIVAMENTE RECEBIDAS
    filtros['nota_fiscal__status_recebimento'] = 'recebido'
    filtros['nota_fiscal__dtRecebimento__isnull'] = False
    
    rateios = NotaFiscalRateioMedico.objects.filter(**filtros).select_related(
        'nota_fiscal', 'nota_fiscal__meio_pagamento', 'medico__pessoa'
    ).order_by('nota_fiscal__dtRecebimento', 'medico__id')
    total_rateios = rateios.count()
    
    if total_rateios == 0:
        print("⚠ Nenhum rateio de nota fiscal RECEBIDA encontrado com os filtros especificados")
        return
    
    print(f"📋 Total de rateios de notas fiscais recebidas encontrados: {total_rateios}")
    print(f"📄 IMPORTANTE: Considerando apenas notas com status='recebido' e data de recebimento preenchida")
    print()
    
    # Obter configurações necessárias
    descricao_movimentacao = obter_ou_criar_descricao_movimentacao(empresa)
    
    # Processar cada rateio
    sucessos = 0
    ja_incluidas = 0
    erros = 0
    sem_valor = 0
    nao_recebidas = 0
    
    print("Processando rateios de notas fiscais...")
    print("-" * 80)
    
    with transaction.atomic():
        for i, rateio in enumerate(rateios, 1):
            socio_nome = getattr(getattr(rateio.medico, 'pessoa', None), 'name', str(rateio.medico))
            numero_nf = rateio.nota_fiscal.numero or 'S/N'
            valor_liquido = rateio.valor_liquido_medico or 0
            data_recebimento = rateio.nota_fiscal.dtRecebimento
            meio_pagamento_nf = getattr(rateio.nota_fiscal, 'meio_pagamento', None)
            meio_pagamento_nome = meio_pagamento_nf.nome if meio_pagamento_nf else 'Padrão'
            
            if valor_liquido <= 0:
                sem_valor += 1
                status = "⚠"
                print(f"{status} [{i:3d}/{total_rateios}] {data_recebimento} | {socio_nome} | NF {numero_nf} | Sem valor líquido válido")
                continue
            
            sucesso, mensagem = incluir_rateio_no_extrato(rateio, descricao_movimentacao, empresa)
            
            if sucesso:
                sucessos += 1
                status = "✓"
            elif "já incluído" in mensagem:
                ja_incluidas += 1
                status = "⚠"
            elif "não recebida" in mensagem or "Status:" in mensagem:
                nao_recebidas += 1
                status = "⏳"
            else:
                erros += 1
                status = "❌"
            
            print(f"{status} [{i:3d}/{total_rateios}] {data_recebimento} | {socio_nome} | NF {numero_nf} | R$ {valor_liquido:,.2f} | {meio_pagamento_nome}")
            if not sucesso and "já incluído" not in mensagem:
                print(f"    └─ {mensagem}")
    
    # Resumo final
    print("-" * 80)
    print("RESUMO:")
    print(f"✓ Incluídas com sucesso: {sucessos}")
    print(f"⚠ Já existiam no extrato: {ja_incluidas}")
    print(f"⚠ Sem valor líquido válido: {sem_valor}")
    print(f"⏳ Notas ainda não recebidas: {nao_recebidas}")
    print(f"❌ Erros: {erros}")
    print(f"📊 Total processadas: {sucessos + ja_incluidas + sem_valor + nao_recebidas + erros}")
    print("=" * 80)

if __name__ == "__main__":
    import argparse
    
    print("🚀 Iniciando script...")
    
    parser = argparse.ArgumentParser(description="Inclui receitas de notas fiscais no extrato da conta corrente")
    parser.add_argument("--empresa-id", type=int, help="ID da empresa (opcional)")
    parser.add_argument("--socio-id", type=int, help="ID do sócio (opcional)")
    parser.add_argument("--mes", type=int, help="Mês (1-12) (opcional)")
    parser.add_argument("--ano", type=int, help="Ano (opcional)")
    parser.add_argument("--todos", action="store_true", help="Processar todos os rateios (sem filtros)")
    
    args = parser.parse_args()
    
    if not any([args.empresa_id, args.socio_id, args.mes, args.ano, args.todos]):
        print("⚠ Especifique pelo menos um filtro ou use --todos para processar todos os rateios")
        print("Exemplos:")
        print("  python script_incluir_notas_fiscais_conta_corrente.py --empresa-id 1")
        print("  python script_incluir_notas_fiscais_conta_corrente.py --socio-id 5")
        print("  python script_incluir_notas_fiscais_conta_corrente.py --mes 7 --ano 2025")
        print("  python script_incluir_notas_fiscais_conta_corrente.py --todos")
        sys.exit(1)
    
    try:
        processar_receitas_notas_fiscais(
            empresa_id=args.empresa_id,
            socio_id=args.socio_id,
            mes=args.mes,
            ano=args.ano
        )
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        sys.exit(1)
