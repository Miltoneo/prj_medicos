#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio
from medicos.models.base import Empresa

print('=== DIAGNÓSTICO: NOVAS DESPESAS DOS SÓCIOS ===')

# Buscar todas as despesas do sócio 10 em 2025-08
despesas = DespesaSocio.objects.filter(
    socio_id=10,
    data__year=2025,
    data__month=8
).order_by('-id')  # Mais recentes primeiro

print(f'Total de DespesaSocio encontradas para sócio 10 em 2025-08: {despesas.count()}')
print()

# Verificar empresa de cada grupo
empresas_grupos = {}
for despesa in despesas:
    empresa_id = despesa.item_despesa.grupo_despesa.empresa_id
    if empresa_id not in empresas_grupos:
        empresas_grupos[empresa_id] = []
    empresas_grupos[empresa_id].append(despesa)

print('=== DISTRIBUIÇÃO POR EMPRESA ===')
for empresa_id, lista_despesas in empresas_grupos.items():
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        empresa_nome = empresa.razao_social
    except:
        empresa_nome = f"Empresa ID {empresa_id} (não encontrada)"
    
    print(f'\nEMPRESA: {empresa_nome} (ID: {empresa_id}):')
    total_empresa = sum(d.valor for d in lista_despesas)
    
    for despesa in sorted(lista_despesas, key=lambda x: x.id, reverse=True):
        data_str = despesa.data.strftime('%d/%m/%Y')
        print(f'  ID {despesa.id}: {data_str} - R$ {despesa.valor} - {despesa.item_despesa}')
    
    print(f'  Subtotal: R$ {total_empresa}')

# Verificar qual empresa deveria estar no relatório
print(f'\n=== ANÁLISE DO PROBLEMA ===')
empresa_correta = 5  # Empresa que aparece na URL do relatório

despesas_empresa_correta = [d for d in despesas if d.item_despesa.grupo_despesa.empresa_id == empresa_correta]
despesas_empresa_errada = [d for d in despesas if d.item_despesa.grupo_despesa.empresa_id != empresa_correta]

print(f'[OK] Despesas vinculadas a empresa {empresa_correta} (aparecem no relatorio): {len(despesas_empresa_correta)}')
print(f'[ERRO] Despesas vinculadas a outras empresas (NAO aparecem): {len(despesas_empresa_errada)}')

if despesas_empresa_errada:
    print('\nPROBLEMA CONFIRMADO:')
    print('   As seguintes despesas estao vinculadas a empresa errada:')
    for despesa in despesas_empresa_errada:
        empresa_id = despesa.item_despesa.grupo_despesa.empresa_id
        data_str = despesa.data.strftime('%d/%m/%Y')
        print(f'   ID {despesa.id}: {data_str} - R$ {despesa.valor} - empresa_grupo={empresa_id} (deveria ser {empresa_correta})')

print(f'\n=== PRÓXIMOS PASSOS ===')
if despesas_empresa_errada:
    print('1. Migrar as despesas da empresa errada para a empresa 5')
    print('2. Verificar o formulário para entender por que está criando com empresa errada')
    print('3. Validar no relatório após migração')
else:
    print('[OK] Todas as despesas estao vinculadas a empresa correta')
    print('   O problema pode estar no builder/template/view')
