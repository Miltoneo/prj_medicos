import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

print('=== TESTE FINAL ISSQN ===')

try:
    from medicos.models.fiscal import Aliquotas
    print('Modelo Aliquotas carregado')
    
    # Testar campo ISS_RETENCAO
    count = Aliquotas.objects.count()
    print(f'Total aliquotas: {count}')
    
    if count > 0:
        aliq = Aliquotas.objects.first()
        print(f'Campo ISS_RETENCAO: {aliq.ISS_RETENCAO}')
    
    from medicos.relatorios.builders import montar_relatorio_issqn
    resultado = montar_relatorio_issqn(4, '2025-01')
    print(f'Builder ISSQN funcionando: {len(resultado["linhas"])} linhas')
    
    print('SUCESSO: Tudo funcionando!')
    
except Exception as e:
    print(f'ERRO: {e}')
