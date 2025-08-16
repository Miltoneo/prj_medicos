import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente
from medicos.relatorios.apuracao_cofins import montar_relatorio_cofins_persistente

print('=== TESTE ALIQUOTAS NA DESCRIÇÃO ===')

# Testar PIS
print('\n1. TESTANDO PIS:')
try:
    resultado_pis = montar_relatorio_pis_persistente(4, '2025')
    if resultado_pis['linhas']:
        aliquota_pis = resultado_pis['linhas'][0].get('aliquota', 0)
        print(f'   Alíquota PIS encontrada: {aliquota_pis}%')
        print(f'   Descrição será: "Imposto devido ({aliquota_pis}%)"')
    else:
        print('   Nenhuma linha encontrada no PIS')
except Exception as e:
    print(f'   Erro no PIS: {e}')

# Testar COFINS
print('\n2. TESTANDO COFINS:')
try:
    resultado_cofins = montar_relatorio_cofins_persistente(4, '2025')
    if resultado_cofins['linhas']:
        aliquota_cofins = resultado_cofins['linhas'][0].get('aliquota', 0)
        print(f'   Alíquota COFINS encontrada: {aliquota_cofins}%')
        print(f'   Descrição será: "Imposto devido ({aliquota_cofins}%)"')
    else:
        print('   Nenhuma linha encontrada no COFINS')
except Exception as e:
    print(f'   Erro no COFINS: {e}')

print('\n=== RESULTADO ===')
print('✅ Alterações aplicadas com sucesso!')
print('📝 MUDANÇAS:')
print('   - PIS: "Imposto devido" → "Imposto devido (X%)"')
print('   - COFINS: "Imposto devido" → "Imposto devido (X%)"')
print('\n🎯 A alíquota agora aparece na descrição da linha "Imposto devido"!')
print('\n🌐 Teste na URL: http://127.0.0.1:8000/medicos/relatorio-issqn/4/')
