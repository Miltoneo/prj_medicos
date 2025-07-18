import os
import django
import sys

# Ajusta o caminho do projeto para garantir que o Django encontre os apps
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import ItemDespesa

# Apaga todos os itens de despesa
ItemDespesa.objects.all().delete()

print('Todos os itens de despesa foram apagados.')
