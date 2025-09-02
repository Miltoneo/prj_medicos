#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificação rápida dos lançamentos de notas fiscais
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente

# Verificar movimentações restantes
criterios = [
    "Nota Fiscal",
    "Rateio NF ID:",
    "Receita de Nota Fiscal"
]

print("=" * 60)
print("🔍 VERIFICAÇÃO: Lançamentos de Notas Fiscais")
print("=" * 60)

total_restantes = 0
for criterio in criterios:
    count = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains=criterio
    ).count()
    print(f"📋 {criterio}: {count} registros")
    total_restantes += count

print(f"\n📊 TOTAL RESTANTE: {total_restantes}")

if total_restantes == 0:
    print("✅ Sucesso: Todos os lançamentos foram removidos!")
else:
    print("⚠️  Ainda existem lançamentos de notas fiscais")
    
print("=" * 60)
