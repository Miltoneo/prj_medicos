import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models.despesas import DespesaSocio

ids = [58,59]
out = []
for i in ids:
    try:
        d = DespesaSocio.objects.select_related('item_despesa__grupo_despesa__empresa','socio__pessoa').get(id=i)
        item = d.item_despesa
        grupo = item.grupo_despesa if item else None
        empresa = grupo.empresa if grupo else None
        out.append({
            'id': d.id,
            'data': d.data.strftime('%Y-%m-%d'),
            'socio_id': getattr(d.socio,'id',None),
            'socio': getattr(getattr(d.socio,'pessoa',None),'name',''),
            'item_id': item.id if item else None,
            'item_codigo': getattr(item,'codigo',None) if item else None,
            'grupo_id': grupo.id if grupo else None,
            'grupo_codigo': getattr(grupo,'codigo',None) if grupo else None,
            'grupo_empresa_id': empresa.id if empresa else None,
            'empresa_name': getattr(empresa,'name',None) if empresa else None,
            'valor': float(d.valor),
        })
    except Exception as e:
        out.append({'id': i, 'error': str(e)})
print(json.dumps(out, ensure_ascii=False, indent=2))
