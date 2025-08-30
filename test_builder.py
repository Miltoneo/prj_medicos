import os
import sys
import django
from pathlib import Path

# Adicionar o diretório do projeto ao sys.path
project_dir = Path('f:/Projects/Django/prj_medicos')
sys.path.insert(0, str(project_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio
print('Executando builder...')
relatorio = montar_relatorio_mensal_socio(5, '2025-08', socio_id=10)
print('Despesas com rateio:', relatorio['relatorio']['lista_despesas_com_rateio'])
