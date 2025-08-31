import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models import Empresa
from medicos.models.base import Socio
from medicos.models.despesas import DespesaSocio

try:
    empresa = Empresa.objects.get(id=5)
    socio = Socio.objects.get(id=10)
    qs = DespesaSocio.objects.filter(
        socio=socio,
        item_despesa__grupo_despesa__empresa=empresa,
        data__year=2025,
        data__month=8
    ).select_related('item_despesa__grupo_despesa')
    data = {
        'count': qs.count(),
        'items': [
            {
                'id': d.id,
                'data': d.data.strftime('%Y-%m-%d'),
                'socio': d.socio.pessoa.name if d.socio and d.socio.pessoa else 'N/A',
                'descricao': d.item_despesa.descricao if d.item_despesa else 'N/A',
                'grupo': d.item_despesa.grupo_despesa.descricao if d.item_despesa and d.item_despesa.grupo_despesa else 'N/A',
                'valor': float(d.valor),
            }
            for d in qs
        ]
    }
except Exception as e:
    data = {'error': str(e)}
print(json.dumps(data, ensure_ascii=False, indent=2))
