import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.models.despesas import GrupoDespesa

try:
    g = GrupoDespesa.objects.select_related('empresa').get(id=10)
    empresa = g.empresa
    out = {
        'grupo_id': g.id,
        'grupo_codigo': g.codigo,
        'grupo_descricao': g.descricao,
        'grupo_tipo_rateio': g.tipo_rateio,
        'empresa_id': empresa.id if empresa else None,
        'empresa_name': getattr(empresa, 'name', None) if empresa else None,
        'empresa_nome_fantasia': getattr(empresa, 'nome_fantasia', None) if empresa else None,
    }
except Exception as e:
    out = {'error': str(e)}

print(json.dumps(out, ensure_ascii=False, indent=2))
