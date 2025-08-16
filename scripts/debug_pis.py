import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa
from medicos.models.fiscal import NotaFiscal
from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente

# Verificar empresa
empresa = Empresa.objects.get(id=4)
print(f'Empresa: {empresa.nome}')

# Verificar notas de janeiro 2025
notas_jan = NotaFiscal.objects.filter(empresa_destinataria=empresa, dtEmissao__year=2025, dtEmissao__month=1)
print(f'Notas janeiro 2025: {notas_jan.count()}')

if notas_jan.exists():
    for nf in notas_jan[:3]:
        print(f'  NF {nf.numero}: val_bruto={nf.val_bruto}, val_PIS={nf.val_PIS}')

# Executar builder
resultado = montar_relatorio_pis_persistente(4, '2025')
janeiro = resultado['linhas'][0]  # Janeiro é o primeiro
print(f'Janeiro - Builder: base_calculo={janeiro["base_calculo"]}, imposto_retido_nf={janeiro["imposto_retido_nf"]}')
