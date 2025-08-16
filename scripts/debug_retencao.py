import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas

print('=== VERIFICANDO CONFIGURAÇÕES DE RETENÇÃO ===')

# Verificar empresa 4
empresa = Empresa.objects.get(id=4)
print(f'Empresa: {empresa.nome}')

# Verificar alíquotas
aliquotas = Aliquotas.objects.filter(empresa=empresa).first()
if aliquotas:
    print(f'ISS configurado: {aliquotas.ISS}%')
    
    # Verificar se há algum campo relacionado a retenção
    campos_aliquotas = dir(aliquotas)
    campos_retencao = [campo for campo in campos_aliquotas if 'retid' in campo.lower() or 'reten' in campo.lower()]
    
    if campos_retencao:
        print(f'Campos de retenção encontrados: {campos_retencao}')
    else:
        print('Nenhum campo de retenção encontrado nas alíquotas')
        
    # Verificar campos que contenham 'iss'
    campos_iss = [campo for campo in campos_aliquotas if 'iss' in campo.lower()]
    print(f'Campos relacionados ao ISS: {campos_iss}')
else:
    print('Nenhuma alíquota configurada para esta empresa')

print('\n=== RECOMENDAÇÃO ===')
print('O cálculo atual usa 20% fixo para retenção de ISS.')
print('Devemos investigar se:')
print('1. Essa é a regra correta para o município')  
print('2. Deveria ser configurável por empresa')
print('3. Deveria usar dados reais das notas fiscais')
