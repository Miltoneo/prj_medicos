import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal

# Verificar campos do modelo
campos_valor = [f.name for f in NotaFiscal._meta.fields if 'val_' in f.name]
print("Campos de valor encontrados:")
for campo in campos_valor:
    print(f"- {campo}")

print("\nCampo val_outros existe:", 'val_outros' in campos_valor)
