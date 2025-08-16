import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa
from medicos.models.relatorios_apuracao_pis import ApuracaoPIS
from medicos.models.relatorios_apuracao_cofins import ApuracaoCOFINS
from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente
from medicos.relatorios.apuracao_cofins import montar_relatorio_cofins_persistente

print('=== LIMPEZA DE CACHE E RECÁLCULO ===')

empresa = Empresa.objects.get(id=4)
print(f'Empresa: {empresa.nome}')

# Limpar cache PIS 2025
deleted_pis = ApuracaoPIS.objects.filter(empresa=empresa, competencia__endswith='/2025').delete()
print(f'Registros PIS deletados: {deleted_pis[0]}')

# Limpar cache COFINS 2025
try:
    deleted_cofins = ApuracaoCOFINS.objects.filter(empresa=empresa, competencia__endswith='/2025').delete()
    print(f'Registros COFINS deletados: {deleted_cofins[0]}')
except:
    print('Modelo COFINS não encontrado - será criado')

# Recalcular PIS
print('\n=== RECALCULANDO PIS ===')
resultado_pis = montar_relatorio_pis_persistente(4, '2025')
print(f'PIS - Linhas geradas: {len(resultado_pis["linhas"])}')
print(f'PIS - Totais: {resultado_pis["totais"]}')

# Verificar janeiro especificamente
jan_pis = resultado_pis['linhas'][0]
print(f'\nJaneiro PIS:')
print(f'  Base cálculo: {jan_pis["base_calculo"]}')
print(f'  Imposto devido: {jan_pis["imposto_devido"]}')
print(f'  Imposto retido NF: {jan_pis["imposto_retido_nf"]}')
print(f'  Imposto a pagar: {jan_pis["imposto_a_pagar"]}')

# Recalcular COFINS
print('\n=== RECALCULANDO COFINS ===')
resultado_cofins = montar_relatorio_cofins_persistente(4, '2025')
print(f'COFINS - Linhas geradas: {len(resultado_cofins["linhas"])}')
print(f'COFINS - Totais: {resultado_cofins["totais"]}')

print('\n✅ Recálculo concluído. Cache limpo e dados atualizados.')
