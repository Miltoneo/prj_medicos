import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas, NotaFiscal

# Verificar alíquotas da empresa 4
empresa = Empresa.objects.get(id=4)
print(f'Empresa: {empresa.nome}')

aliquotas = Aliquotas.objects.filter(empresa=empresa)
print(f'Alíquotas configuradas: {aliquotas.count()}')

for aliq in aliquotas:
    print(f'  Vigência: {aliq.data_vigencia_inicio} - PIS: {aliq.PIS}% - COFINS: {aliq.COFINS}%')

# Verificar uma nota específica
nf = NotaFiscal.objects.filter(empresa_destinataria=empresa, dtEmissao__year=2025).first()
if nf:
    print(f'\nNota exemplo: {nf.numero}')
    print(f'  val_bruto: {nf.val_bruto}')
    print(f'  val_PIS: {nf.val_PIS}')
    print(f'  val_COFINS: {nf.val_COFINS}')
else:
    print('\nNenhuma nota encontrada em 2025')
