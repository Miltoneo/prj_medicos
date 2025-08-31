import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models import Empresa
from medicos.models.despesas import DespesaSocio, GrupoDespesa, ItemDespesa

empresa_target = Empresa.objects.get(id=5)

despesas_ids = [58,59]
results = []
for did in despesas_ids:
    try:
        d = DespesaSocio.objects.select_related('item_despesa__grupo_despesa').get(id=did)
    except DespesaSocio.DoesNotExist:
        results.append({'id': did, 'error': 'DespesaSocio not found'})
        continue
    old_item = d.item_despesa
    old_group = old_item.grupo_despesa if old_item else None
    if not old_group:
        results.append({'id': did, 'error': 'No grupo/item attached'})
        continue
    # Find or create group in target empresa with same codigo
    target_group, created_group = GrupoDespesa.objects.get_or_create(
        empresa=empresa_target,
        codigo=old_group.codigo,
        defaults={
            'descricao': old_group.descricao,
            'tipo_rateio': old_group.tipo_rateio,
        }
    )
    # Find or create item in target group with same codigo
    target_item, created_item = ItemDespesa.objects.get_or_create(
        grupo_despesa=target_group,
        codigo=old_item.codigo,
        defaults={
            'descricao': old_item.descricao,
        }
    )
    # Reassign despesa
    d.item_despesa = target_item
    d.save()
    results.append({
        'id': did,
        'old_group_id': old_group.id,
        'target_group_id': target_group.id,
        'created_group': created_group,
        'old_item_id': old_item.id,
        'target_item_id': target_item.id,
        'created_item': created_item,
    })

print(json.dumps(results, ensure_ascii=False, indent=2))
