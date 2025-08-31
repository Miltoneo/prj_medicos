import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models import Empresa
from medicos.models.base import Socio
from medicos.models.despesas import DespesaSocio

out_path = 'f:/Projects/Django/prj_medicos/tmp_despesas_sem_rateio_output.json'
try:
    empresa = Empresa.objects.get(id=5)
    socio = Socio.objects.get(id=10)
    ano = 2025
    mes = 8
    qs = DespesaSocio.objects.filter(socio=socio, item_despesa__grupo_despesa__empresa=empresa, data__year=ano, data__month=mes)
    data = {
        'count': qs.count(),
        'items': [
            {
                'id': d.id,
                'data': d.data.strftime('%Y-%m-%d'),
                'grupo': d.item_despesa.grupo_despesa.descricao if d.item_despesa and d.item_despesa.grupo_despesa else None,
                'descricao': d.item_despesa.descricao if d.item_despesa else None,
                'valor': float(d.valor),
            }
            for d in qs
        ]
    }
except Exception as e:
    data = {'error': str(e)}
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('WROTE', out_path)
