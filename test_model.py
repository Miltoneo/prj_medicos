import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import Aliquotas

print("Modelo importado com sucesso!")
print("Campos do modelo:")
for field in Aliquotas._meta.fields:
    print(f"- {field.name}: {field.__class__.__name__}")
