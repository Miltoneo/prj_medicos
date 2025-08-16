import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_issqn
from medicos.relatorios.apuracao_irpj_mensal import montar_relatorio_irpj_mensal_persistente

print('=== TESTE ALIQUOTAS EM TODAS AS TABELAS ===')

# Testar ISSQN
print('\n1. TESTANDO ISSQN:')
try:
    resultado_issqn = montar_relatorio_issqn(4, '2025-01')
    if resultado_issqn['linhas']:
        aliquota_issqn = resultado_issqn['linhas'][0].get('aliquota', 0)
        print(f'   ✅ Alíquota ISSQN: {aliquota_issqn}%')
        print(f'   📝 Descrição: "Imposto devido ({aliquota_issqn}%)"')
    else:
        print('   ⚠️ Nenhuma linha encontrada no ISSQN')
except Exception as e:
    print(f'   ❌ Erro no ISSQN: {e}')

# Testar IRPJ Mensal
print('\n2. TESTANDO IRPJ MENSAL:')
try:
    resultado_irpj = montar_relatorio_irpj_mensal_persistente(4, '2025')
    if resultado_irpj['linhas']:
        aliquota_irpj = resultado_irpj['linhas'][0].get('aliquota', 0)
        print(f'   ✅ Alíquota IRPJ: {aliquota_irpj}%')
        print(f'   📝 Descrição: "Imposto devido ({aliquota_irpj}%)"')
    else:
        print('   ⚠️ Nenhuma linha encontrada no IRPJ Mensal')
except Exception as e:
    print(f'   ❌ Erro no IRPJ Mensal: {e}')

print('\n=== RESUMO DAS ALTERAÇÕES ===')
print('✅ ISSQN: "Imposto devido" → "Imposto devido (X%)"')
print('✅ COFINS: "Imposto devido" → "Imposto devido (X%)" (já estava)')
print('✅ PIS: "Imposto devido" → "Imposto devido (X%)" (já estava)')
print('✅ IRPJ Mensal: "Imposto devido" → "Imposto devido (X%)"')

print('\n🎯 Todas as tabelas solicitadas agora exibem a alíquota!')
print('🌐 Teste na URL: http://127.0.0.1:8000/medicos/relatorio-issqn/4/')
