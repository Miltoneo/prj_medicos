#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio

print('Consultando despesas do socio 10 em 2025-08...')

# Query simples
despesas = DespesaSocio.objects.filter(
    socio_id=10, 
    data__year=2025, 
    data__month=8
).select_related('item_despesa__grupo_despesa').order_by('-id')

print(f'Total: {despesas.count()}')

for despesa in despesas:
    empresa_id = despesa.item_despesa.grupo_despesa.empresa_id
    data_str = despesa.data.strftime('%d/%m/%Y')
    print(f'ID {despesa.id}: {data_str} - R$ {despesa.valor} - empresa={empresa_id}')

# Verificar problema
empresa_5 = [d for d in despesas if d.item_despesa.grupo_despesa.empresa_id == 5]
outras = [d for d in despesas if d.item_despesa.grupo_despesa.empresa_id != 5]

print(f'\nDespesas empresa 5: {len(empresa_5)}')
print(f'Despesas outras empresas: {len(outras)}')

if outras:
    print('\nPROBLEMA: Despesas em empresas erradas:')
    for d in outras:
        print(f'  ID {d.id} -> empresa {d.item_despesa.grupo_despesa.empresa_id}')
    print('\nNecessaria migracao!')
else:
    print('\nTodas as despesas estao na empresa 5. Problema pode ser no builder/template.')
