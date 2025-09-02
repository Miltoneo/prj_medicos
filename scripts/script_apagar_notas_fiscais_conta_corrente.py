#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para APAGAR todos os lançamentos de notas fiscais recebidas da movimentação de conta corrente.
ATENÇÃO: Este script remove permanentemente os dados!
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente
from django.db import transaction

def apagar_lancamentos_notas_fiscais():
    """Apaga todos os lançamentos de notas fiscais recebidas da conta corrente"""
    
    print("=" * 80)
    print("⚠️  SCRIPT: APAGAR Lançamentos de Notas Fiscais da Conta Corrente")
    print("=" * 80)
    print("🚨 ATENÇÃO: Esta operação é IRREVERSÍVEL!")
    print()
    
    # Buscar movimentações relacionadas a notas fiscais
    movimentacoes_nf = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Nota Fiscal"
    )
    
    # Buscar movimentações relacionadas a rateios de NF
    movimentacoes_rateio = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Rateio NF ID:"
    )
    
    # Buscar movimentações relacionadas a receitas de NF
    movimentacoes_receita = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Receita de Nota Fiscal"
    )
    
    # Unir todas as movimentações (sem duplicatas)
    todas_movimentacoes = MovimentacaoContaCorrente.objects.filter(
        id__in=list(movimentacoes_nf.values_list('id', flat=True)) +
               list(movimentacoes_rateio.values_list('id', flat=True)) +
               list(movimentacoes_receita.values_list('id', flat=True))
    ).distinct()
    
    total_movimentacoes = todas_movimentacoes.count()
    
    if total_movimentacoes == 0:
        print("✅ Nenhuma movimentação de nota fiscal encontrada para apagar")
        return
    
    print(f"📊 Total de movimentações de notas fiscais encontradas: {total_movimentacoes}")
    print()
    
    # Mostrar algumas movimentações como exemplo
    print("📋 Exemplos de movimentações que serão apagadas:")
    print("-" * 80)
    
    for i, movimentacao in enumerate(todas_movimentacoes[:10], 1):  # Mostrar até 10 exemplos
        socio_nome = getattr(getattr(movimentacao.socio, 'pessoa', None), 'name', 'N/A') if movimentacao.socio else 'N/A'
        print(f"{i:2d}. ID: {movimentacao.id} | {movimentacao.data_movimentacao} | {socio_nome} | R$ {movimentacao.valor:,.2f}")
        print(f"    └─ {movimentacao.historico_complementar[:100]}...")
    
    if total_movimentacoes > 10:
        print(f"    ... e mais {total_movimentacoes - 10} movimentações")
    
    print("-" * 80)
    print()
    
    # Solicitar confirmação
    print("🚨 CONFIRMAÇÃO NECESSÁRIA:")
    print("Esta operação irá APAGAR PERMANENTEMENTE todas as movimentações listadas!")
    print()
    confirmacao = input("Digite 'CONFIRMAR' para prosseguir com a exclusão: ")
    
    if confirmacao.upper() != 'CONFIRMAR':
        print("❌ Operação cancelada pelo usuário")
        return
    
    print()
    print("🗑️  Iniciando exclusão...")
    
    # Executar exclusão em transação
    try:
        with transaction.atomic():
            # Contar por tipo antes de apagar
            count_nf = movimentacoes_nf.count()
            count_rateio = movimentacoes_rateio.count()
            count_receita = movimentacoes_receita.count()
            
            # Apagar todas as movimentações
            deleted_count, deleted_details = todas_movimentacoes.delete()
            
            print("✅ Exclusão concluída com sucesso!")
            print()
            print("📊 RESUMO DA EXCLUSÃO:")
            print(f"   🗑️  Total de registros apagados: {deleted_count}")
            print(f"   📄 Movimentações gerais de NF: {count_nf}")
            print(f"   📋 Movimentações de Rateio NF: {count_rateio}")
            print(f"   💰 Movimentações de Receita NF: {count_receita}")
            
            if deleted_details:
                print()
                print("📋 Detalhes por modelo:")
                for model, count in deleted_details.items():
                    if count > 0:
                        print(f"   • {model}: {count} registros")
    
    except Exception as e:
        print(f"❌ Erro durante a exclusão: {e}")
        return
    
    print()
    print("✅ OPERAÇÃO CONCLUÍDA!")
    print("Todas as movimentações de notas fiscais foram removidas da conta corrente")
    print("=" * 80)

def verificar_movimentacoes_restantes():
    """Verifica se ainda existem movimentações de notas fiscais"""
    
    print()
    print("🔍 VERIFICAÇÃO PÓS-EXCLUSÃO:")
    print("-" * 80)
    
    # Verificar se ainda existem movimentações relacionadas a NF
    movimentacoes_nf = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Nota Fiscal"
    ).count()
    
    movimentacoes_rateio = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Rateio NF"
    ).count()
    
    movimentacoes_receita = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Receita de Nota Fiscal"
    ).count()
    
    total_restantes = movimentacoes_nf + movimentacoes_rateio + movimentacoes_receita
    
    print(f"📊 Movimentações restantes:")
    print(f"   📄 Notas Fiscais gerais: {movimentacoes_nf}")
    print(f"   📋 Rateios de NF: {movimentacoes_rateio}")
    print(f"   💰 Receitas de NF: {movimentacoes_receita}")
    print(f"   📊 Total restante: {total_restantes}")
    
    if total_restantes == 0:
        print("✅ Perfeito! Nenhuma movimentação de nota fiscal restante")
    else:
        print("⚠️  Ainda existem movimentações relacionadas a notas fiscais")
    
    print("-" * 80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Apaga lançamentos de notas fiscais da conta corrente")
    parser.add_argument("--confirmar", action="store_true", help="Pula a confirmação interativa")
    
    args = parser.parse_args()
    
    try:
        if args.confirmar:
            # Modo não interativo - para automação
            print("🤖 Modo automático ativado - pulando confirmação")
        
        apagar_lancamentos_notas_fiscais()
        verificar_movimentacoes_restantes()
        
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        sys.exit(1)
