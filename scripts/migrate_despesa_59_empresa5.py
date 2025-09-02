import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models import Empresa
from medicos.models.despesas import DespesaSocio, GrupoDespesa, ItemDespesa

empresa_target = Empresa.objects.get(id=5)

did = 59
out = {'id': did}
try:
    d = DespesaSocio.objects.select_related('item_despesa__grupo_despesa').get(id=did)
    old_item = d.item_despesa
    old_group = old_item.grupo_despesa if old_item else None
    out['old_group_id'] = old_group.id if old_group else None
    # Ensure target group exists
    target_group, created_g = GrupoDespesa.objects.get_or_create(
        empresa=empresa_target,
        codigo=old_group.codigo,
        defaults={'descricao': old_group.descricao, 'tipo_rateio': old_group.tipo_rateio}
    )
    target_item, created_i = ItemDespesa.objects.get_or_create(
        grupo_despesa=target_group,
        codigo=old_item.codigo,
        defaults={'descricao': old_item.descricao}
    )

    d.item_despesa = target_item
    d.save()
    out.update({
        'target_group_id': target_group.id,
        'created_group': created_g,
        'target_item_id': target_item.id,
        'created_item': created_i,
        'status': 'migrated'
    })
except Exception as e:
    out['error'] = str(e)

print(json.dumps(out, ensure_ascii=False, indent=2))
