#!/usr/bin/env python
"""
Verificar movimentações conta corrente existentes
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.despesas import DespesaSocio

print("=== MOVIMENTAÇÕES CONTA CORRENTE ===")
movimentacoes = MovimentacaoContaCorrente.objects.all()[:10]

for mov in movimentacoes:
    print(f"ID: {mov.id} | Data: {mov.data_movimentacao} | Valor: R$ {mov.valor} | Sócio: {mov.socio} | Histórico: {mov.historico_complementar[:50]}...")

print(f"\nTotal de movimentações: {MovimentacaoContaCorrente.objects.count()}")

print("\n=== DESPESAS DE SÓCIO ===")
despesas = DespesaSocio.objects.all()[:5]

for desp in despesas:
    print(f"ID: {desp.id} | Data: {desp.data} | Valor: R$ {desp.valor} | Sócio: {desp.socio} | Item: {desp.item_despesa}")

print(f"\nTotal de despesas sócio: {DespesaSocio.objects.count()}")
