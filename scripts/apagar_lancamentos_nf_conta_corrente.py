#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para apagar TODOS os lançamentos de notas fiscais da movimentação de conta corrente
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente
from django.db import transaction

def apagar_lancamentos_notas_fiscais():
    """Apaga todos os lançamentos de notas fiscais da conta corrente"""
    
    print("=" * 80)
    print("SCRIPT: Apagar Lançamentos de Notas Fiscais da Conta Corrente")
    print("=" * 80)
    
    # Buscar movimentações relacionadas a notas fiscais
    # Método 1: Por histórico complementar
    movimentacoes_historico = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Nota Fiscal"
    )
    
    # Método 2: Por rateio NF ID
    movimentacoes_rateio = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Rateio NF ID:"
    )
    
    # Método 3: Por receita de nota fiscal
    movimentacoes_receita = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Receita de Nota Fiscal"
    )
    
    # Método 4: Por recebimento de nota fiscal
    movimentacoes_recebimento = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Recebimento da Nota Fiscal"
    )
    
    # Contar movimentações por tipo
    count_historico = movimentacoes_historico.count()
    count_rateio = movimentacoes_rateio.count()
    count_receita = movimentacoes_receita.count()
    count_recebimento = movimentacoes_recebimento.count()
    
    print(f"📊 CONTAGEM POR TIPO:")
    print(f"   📄 Histórico contém 'Nota Fiscal': {count_historico}")
    print(f"   📋 Histórico contém 'Rateio NF ID:': {count_rateio}")
    print(f"   💰 Histórico contém 'Receita de Nota Fiscal': {count_receita}")
    print(f"   📥 Histórico contém 'Recebimento da Nota Fiscal': {count_recebimento}")
    print()
    
    # Obter todas as movimentações únicas (sem duplicatas)
    todas_movimentacoes = MovimentacaoContaCorrente.objects.filter(
        models.Q(historico_complementar__icontains="Nota Fiscal") |
        models.Q(historico_complementar__icontains="Rateio NF ID:") |
        models.Q(historico_complementar__icontains="Receita de Nota Fiscal") |
        models.Q(historico_complementar__icontains="Recebimento da Nota Fiscal")
    ).distinct()
    
    total_movimentacoes = todas_movimentacoes.count()
    
    if total_movimentacoes == 0:
        print("⚠ Nenhuma movimentação de nota fiscal encontrada")
        return
    
    print(f"📊 Total de movimentações únicas encontradas: {total_movimentacoes}")
    print()
    
    # Mostrar exemplos
    print("📋 Exemplos de movimentações a serem apagadas:")
    print("-" * 80)
    
    exemplos = todas_movimentacoes.select_related('socio__pessoa')[:10]
    for i, mov in enumerate(exemplos, 1):
        socio_nome = getattr(getattr(mov.socio, 'pessoa', None), 'name', 'N/A') if mov.socio else 'N/A'
        valor = mov.valor or 0
        historico = mov.historico_complementar[:70] + "..." if len(mov.historico_complementar) > 70 else mov.historico_complementar
        
        print(f"{i:2d}. ID: {mov.id} | {mov.data_movimentacao} | {socio_nome} | R$ {valor:,.2f}")
        print(f"   └─ {historico}")
    
    if total_movimentacoes > 10:
        print(f"   ... e mais {total_movimentacoes - 10} movimentações")
    
    print()
    print("🗑️  Iniciando exclusão automática...")
    
    # Apagar em lotes para evitar problemas de memória
    deletados_total = 0
    lote_size = 100
    
    with transaction.atomic():
        while True:
            # Buscar próximo lote
            ids_lote = list(MovimentacaoContaCorrente.objects.filter(
                models.Q(historico_complementar__icontains="Nota Fiscal") |
                models.Q(historico_complementar__icontains="Rateio NF ID:") |
                models.Q(historico_complementar__icontains="Receita de Nota Fiscal") |
                models.Q(historico_complementar__icontains="Recebimento da Nota Fiscal")
            ).values_list('id', flat=True)[:lote_size])
            
            if not ids_lote:
                break  # Não há mais registros para deletar
            
            # Deletar por IDs
            deletados_lote = MovimentacaoContaCorrente.objects.filter(id__in=ids_lote).delete()
            deletados_count = deletados_lote[0]  # Número total de objetos deletados
            deletados_total += deletados_count
            
            print(f"✓ Lote deletado: {deletados_count} movimentações")
            
            if len(ids_lote) < lote_size:
                break  # Foi o último lote
    
    print()
    print("=" * 80)
    print("✅ EXCLUSÃO CONCLUÍDA!")
    print(f"🗑️  Total de movimentações apagadas: {deletados_total}")
    print("=" * 80)

if __name__ == "__main__":
    from django.db import models
    try:
        apagar_lancamentos_notas_fiscais()
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        sys.exit(1)
