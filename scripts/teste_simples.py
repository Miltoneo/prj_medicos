#!/usr/bin/env python
"""Teste simples para verificar estado atual das despesas."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio

# Verificar despesas do sócio 10 em 2025-08
despesas = DespesaSocio.objects.filter(
    socio_id=10,
    data__year=2025,
    data__month=8
).select_related('item_despesa__grupo_despesa__empresa').order_by('data')

print(f"Total despesas encontradas: {despesas.count()}")
for despesa in despesas:
    empresa_grupo = despesa.item_despesa.grupo_despesa.empresa_id
    print(f"ID {despesa.id}: {despesa.data.strftime('%d/%m/%Y')} - R$ {despesa.valor:.2f} - empresa_grupo={empresa_grupo}")

# Testar builder
print("\n=== TESTE BUILDER ===")
from medicos.relatorios.builders import montar_relatorio_mensal_socio

resultado = montar_relatorio_mensal_socio(empresa_id=5, mes_ano='2025-08', socio_id=10)
lista_despesas = resultado.get('lista_despesas_sem_rateio', [])
print(f"Builder retornou: {len(lista_despesas)} despesas")
for desp in lista_despesas:
    print(f"  ID {desp.get('id')}: {desp.get('data')} - R$ {desp.get('valor_total', 0):.2f}")
