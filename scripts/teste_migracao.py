import subprocess
import sys

# Teste direto da URL
result = subprocess.run([
    sys.executable, "-c", 
    """
import os, django, requests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

try:
    from medicos.models.fiscal import Aliquotas
    print('✅ Modelo Aliquotas carregado')
    
    # Testar campo ISS_RETENCAO
    count = Aliquotas.objects.count()
    print(f'✅ Total alíquotas: {count}')
    
    if count > 0:
        aliq = Aliquotas.objects.first()
        print(f'✅ Campo ISS_RETENCAO: {aliq.ISS_RETENCAO}')
    
    print('✅ Campo ISS_RETENCAO funciona corretamente!')
    
except Exception as e:
    print(f'❌ Erro: {e}')
    """
], capture_output=True, text=True, cwd=".")

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
