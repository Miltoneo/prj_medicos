import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models.despesas import DespesaSocio

qs = DespesaSocio.objects.filter(data__year=2025, data__month=8).select_related('socio__pessoa','item_despesa__grupo_despesa').order_by('data','id')
rows = []
for d in qs:
    rows.append({
        'id': d.id,
        'data': d.data.strftime('%Y-%m-%d'),
        'socio_id': getattr(d.socio, 'id', None),
        'socio': getattr(getattr(d.socio, 'pessoa', None), 'name', 'N/A'),
        'item_id': d.item_despesa.id if d.item_despesa else None,
        'descricao': d.item_despesa.descricao if d.item_despesa else '',
        'grupo_id': d.item_despesa.grupo_despesa.id if d.item_despesa and d.item_despesa.grupo_despesa else None,
        'grupo': d.item_despesa.grupo_despesa.descricao if d.item_despesa and d.item_despesa.grupo_despesa else '',
        'valor': float(d.valor),
    })

print(json.dumps({'count': len(rows), 'items': rows}, ensure_ascii=False, indent=2))
