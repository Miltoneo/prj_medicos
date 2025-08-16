import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import Aliquotas

print('=== TESTE CAMPO ISS_RETENCAO ===')

# Verificar se o campo existe
try:
    aliquota = Aliquotas.objects.first()
    if aliquota:
        print(f'✅ Modelo carregado: {aliquota.empresa}')
        print(f'✅ Campo ISS_RETENCAO acessível: {aliquota.ISS_RETENCAO}%')
    else:
        print('⚠️ Nenhuma alíquota encontrada no banco')
        
    # Testar se pode fazer query com o campo
    query_test = Aliquotas.objects.filter(ISS_RETENCAO__gte=0).count()
    print(f'✅ Query com ISS_RETENCAO funciona: {query_test} registros')
    
except Exception as e:
    print(f'❌ Erro ao acessar ISS_RETENCAO: {e}')

print('\n=== TESTANDO URL RELATORIO ISSQN ===')
try:
    from medicos.relatorios.builders import montar_relatorio_issqn
    resultado = montar_relatorio_issqn(4, '2025-01')
    print(f'✅ Builder ISSQN executado com sucesso')
    print(f'📊 Linhas: {len(resultado["linhas"])}')
except Exception as e:
    print(f'❌ Erro no builder ISSQN: {e}')

print('\n🎯 Teste concluído!')
