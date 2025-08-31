import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')

django.setup()
from medicos.models.despesas import GrupoDespesa
from medicos.models import Empresa

# Mostrar GrupoDespesa id=10
try:
    g = GrupoDespesa.objects.get(id=10)
    grupo = {
        'id': g.id,
        'descricao': g.descricao,
        'empresa_id': g.empresa.id if g.empresa else None,
        'empresa_nome': g.empresa.nome if g.empresa else None,
        'tipo_rateio': getattr(g, 'tipo_rateio', None),
    }
except Exception as e:
    grupo = {'error': str(e)}

empresas = [{'id': e.id, 'nome': getattr(e, 'nome', '')} for e in Empresa.objects.all()]

print(json.dumps({'grupo_10': grupo, 'empresas': empresas}, ensure_ascii=False, indent=2))
