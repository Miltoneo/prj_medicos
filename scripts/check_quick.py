from medicos.models.relatorios import RelatorioMensalSocio
from medicos.models.base import Empresa, Socio
from datetime import datetime

# Dados específicos do cenário
empresa = Empresa.objects.get(id=4)
socio = Socio.objects.get(id=7)

print(f"Empresa: {empresa.nome_fantasia}")
print(f"Sócio: {socio.pessoa.name}")

# Verificar junho e julho
junho = datetime(2025, 6, 1)
julho = datetime(2025, 7, 1)

# Relatório de junho
try:
    rel_junho = RelatorioMensalSocio.objects.get(empresa=empresa, socio=socio, competencia=junho)
    print(f"JUNHO - impostos_total: {rel_junho.impostos_total}")
except:
    print("JUNHO - não encontrado")

# Relatório de julho  
try:
    rel_julho = RelatorioMensalSocio.objects.get(empresa=empresa, socio=socio, competencia=julho)
    print(f"JULHO - impostos_total: {rel_julho.impostos_total}")
    print(f"JULHO - imposto_provisionado_mes_anterior: {rel_julho.imposto_provisionado_mes_anterior}")
except:
    print("JULHO - não encontrado")
