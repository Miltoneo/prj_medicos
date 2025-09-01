#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificação: Confirma se todos os lançamentos de notas fiscais foram removidos
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.despesas import DespesaSocio
from django.db import models

def verificar_exclusao_notas_fiscais():
    """Verifica se todos os lançamentos de notas fiscais foram removidos"""
    
    print("=" * 80)
    print("VERIFICAÇÃO: Lançamentos de Notas Fiscais Removidos")
    print("=" * 80)
    
    # Verificar diferentes tipos de lançamentos de notas fiscais
    criterios = [
        ("Nota Fiscal", "historico_complementar__icontains", "Nota Fiscal"),
        ("Rateio NF ID", "historico_complementar__icontains", "Rateio NF ID:"),
        ("Receita de Nota Fiscal", "historico_complementar__icontains", "Receita de Nota Fiscal"),
        ("Recebimento da Nota Fiscal", "historico_complementar__icontains", "Recebimento da Nota Fiscal"),
    ]
    
    total_restantes = 0
    
    print("🔍 VERIFICAÇÃO POR CRITÉRIO:")
    for nome, campo, valor in criterios:
        filtro = {campo: valor}
        count = MovimentacaoContaCorrente.objects.filter(**filtro).count()
        total_restantes += count
        
        status = "✅" if count == 0 else "❌"
        print(f"   {status} {nome}: {count} movimentações restantes")
    
    print()
    print(f"📊 TOTAL DE LANÇAMENTOS DE NF RESTANTES: {total_restantes}")
    
    # Verificar lançamentos restantes de outros tipos
    total_movimentacoes = MovimentacaoContaCorrente.objects.count()
    despesas_socio = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Despesa ID:"
    ).count()
    
    outros_lancamentos = total_movimentacoes - total_restantes
    
    print()
    print("📋 RESUMO GERAL DA CONTA CORRENTE:")
    print(f"   📊 Total de movimentações: {total_movimentacoes}")
    print(f"   💰 Lançamentos de despesas de sócio: {despesas_socio}")
    print(f"   📄 Lançamentos de notas fiscais: {total_restantes}")
    print(f"   🔧 Outros lançamentos: {outros_lancamentos - despesas_socio}")
    
    # Resultado final
    print()
    if total_restantes == 0:
        print("✅ SUCESSO: Todos os lançamentos de notas fiscais foram removidos!")
        print("✅ O extrato da conta corrente agora contém apenas:")
        print("   - Lançamentos de despesas de sócio")
        print("   - Outros lançamentos manuais (se houver)")
    else:
        print("❌ ATENÇÃO: Ainda existem lançamentos de notas fiscais no sistema")
        print("   Pode ser necessário executar o script de exclusão novamente")
    
    print("=" * 80)

if __name__ == "__main__":
    verificar_exclusao_notas_fiscais()
