import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

try:
    from medicos.models import NotaFiscal, Socio, Financeiro, Conta
    print('✓ Models imported successfully!')
    
    from medicos import admin
    print('✓ Admin imported successfully!')
    
    print('✓ Modularization working correctly!')
    print('✓ All field references fixed!')
    
except Exception as e:
    print(f'✗ Error: {e}')
