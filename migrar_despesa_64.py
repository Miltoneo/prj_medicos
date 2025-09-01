#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio, ItemDespesa, GrupoDespesa

print('=== MIGRACAO DESPESA ID 64 ===')

try:
    # Buscar a despesa problema
    despesa = DespesaSocio.objects.get(id=64)
    print(f'Despesa ID 64 encontrada:')
    print(f'  Data: {despesa.data.strftime("%d/%m/%Y")}')
    print(f'  Valor: R$ {despesa.valor}')
    print(f'  Socio: {despesa.socio.pessoa.name}')
    print(f'  Item atual: {despesa.item_despesa}')
    print(f'  Grupo atual: {despesa.item_despesa.grupo_despesa}')
    print(f'  Empresa atual: {despesa.item_despesa.grupo_despesa.empresa_id}')
    
    # Obter dados do item/grupo original
    item_original = despesa.item_despesa
    grupo_original = item_original.grupo_despesa
    
    print(f'\n=== CRIANDO/BUSCANDO EQUIVALENTES NA EMPRESA 5 ===')
    
    # Buscar ou criar grupo equivalente na empresa 5
    grupo_correto, grupo_criado = GrupoDespesa.objects.get_or_create(
        empresa_id=5,
        codigo=grupo_original.codigo,
        tipo_rateio=grupo_original.tipo_rateio,
        defaults={
            'descricao': grupo_original.descricao or '',
        }
    )
    
    if grupo_criado:
        print(f'[CRIADO] Grupo criado: {grupo_correto}')
    else:
        print(f'[ENCONTRADO] Grupo encontrado: {grupo_correto}')
    
    # Buscar ou criar item equivalente na empresa 5
    item_correto, item_criado = ItemDespesa.objects.get_or_create(
        grupo_despesa=grupo_correto,
        codigo=item_original.codigo,
        defaults={
            'descricao': item_original.descricao or '',
        }
    )
    
    if item_criado:
        print(f'[CRIADO] Item criado: {item_correto}')
    else:
        print(f'[ENCONTRADO] Item encontrado: {item_correto}')
    
    # Atualizar a despesa
    print(f'\n=== MIGRANDO DESPESA ===')
    print(f'Antes: item_despesa_id={despesa.item_despesa_id} (empresa {despesa.item_despesa.grupo_despesa.empresa_id})')
    
    despesa.item_despesa = item_correto
    despesa.save()
    
    print(f'Depois: item_despesa_id={despesa.item_despesa_id} (empresa {despesa.item_despesa.grupo_despesa.empresa_id})')
    
    print(f'\n[SUCESSO] MIGRACAO CONCLUIDA!')
    print(f'   Despesa ID 64 agora pertence a empresa 5')
    print(f'   Valor: R$ {despesa.valor}')
    print(f'   Data: {despesa.data.strftime("%d/%m/%Y")}')
    
except Exception as e:
    print(f'[ERRO]: {e}')
    import traceback
    traceback.print_exc()
