import sys
import os
from django.conf import settings
from django.template import engines, TemplateSyntaxError

TEMPLATE_PATH = r"f:/Projects/Django/prj_medicos/medicos/templates/relatorios/relatorio_mensal_socio.html"

with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    s = f.read()

if not settings.configured:
    settings.configure(TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), '..', 'medicos', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {},
    }])

try:
    engines['django'].from_string(s)
    print('Template parsed OK')
except TemplateSyntaxError as e:
    print('TemplateSyntaxError:', e)
    sys.exit(2)
except Exception as e:
    print('Other error:', e)
    sys.exit(3)
