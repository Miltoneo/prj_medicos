#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para APAGAR AUTOMATICAMENTE todos os lançamentos de notas fiscais da conta corrente.
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

def apagar_automatico():
    """Apaga automaticamente todos os lançamentos de notas fiscais"""
    
    print("=" * 80)
    print("🗑️  SCRIPT: Apagar Lançamentos de Notas Fiscais da Conta Corrente")
    print("=" * 80)
    
    # Buscar todas as movimentações relacionadas a notas fiscais
    criterios = [
        "Nota Fiscal",
        "Rateio NF ID:",
        "Receita de Nota Fiscal"
    ]
    
    movimentacoes_para_apagar = MovimentacaoContaCorrente.objects.none()
    
    for criterio in criterios:
        movimentacoes = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__icontains=criterio
        )
        movimentacoes_para_apagar = movimentacoes_para_apagar.union(movimentacoes)
    
    total_movimentacoes = movimentacoes_para_apagar.count()
    
    print(f"📊 Total de movimentações encontradas: {total_movimentacoes}")
    
    if total_movimentacoes == 0:
        print("✅ Nenhuma movimentação de nota fiscal encontrada")
        return
    
    # Mostrar exemplos
    print("\n📋 Exemplos de movimentações a serem apagadas:")
    print("-" * 80)
    
    for i, mov in enumerate(list(movimentacoes_para_apagar)[:5], 1):
        socio_nome = getattr(getattr(mov.socio, 'pessoa', None), 'name', 'N/A') if mov.socio else 'N/A'
        print(f"{i}. ID: {mov.id} | {mov.data_movimentacao} | {socio_nome} | R$ {mov.valor:,.2f}")
        print(f"   └─ {mov.historico_complementar[:80]}...")
    
    if total_movimentacoes > 5:
        print(f"   ... e mais {total_movimentacoes - 5} movimentações")
    
    print("\n🗑️  Iniciando exclusão automática...")
    
    try:
        with transaction.atomic():
            deleted_count, deleted_details = movimentacoes_para_apagar.delete()
            
            print(f"✅ Exclusão concluída!")
            print(f"📊 Total apagado: {deleted_count} registros")
            
            if deleted_details:
                print("\n📋 Detalhes:")
                for model, count in deleted_details.items():
                    if count > 0:
                        print(f"   • {model}: {count}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # Verificação final
    print("\n🔍 Verificação final:")
    restantes = 0
    for criterio in criterios:
        count = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__icontains=criterio
        ).count()
        print(f"   {criterio}: {count} restantes")
        restantes += count
    
    if restantes == 0:
        print("✅ Todos os lançamentos de notas fiscais foram removidos!")
    else:
        print(f"⚠️  Ainda restam {restantes} movimentações")
    
    print("=" * 80)

if __name__ == "__main__":
    apagar_automatico()
