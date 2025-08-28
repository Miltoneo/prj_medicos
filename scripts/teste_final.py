from medicos.models.relatorios import RelatorioMensalSocio
from medicos.models.base import Empresa, Socio
from datetime import datetime

print("=== TESTE FINAL ===")

# Testar o cenário específico
empresa = Empresa.objects.get(id=4)
socio = Socio.objects.get(id=7)

print(f"Empresa: {empresa.nome_fantasia}")
print(f"Sócio: {socio.pessoa.name}")

# Verificar relatório de junho/2025
junho_2025 = datetime(2025, 6, 1)
try:
    rel_junho = RelatorioMensalSocio.objects.get(empresa=empresa, socio=socio, competencia=junho_2025)
    print(f"JUNHO - impostos_total: {rel_junho.impostos_total}")
except RelatorioMensalSocio.DoesNotExist:
    print("JUNHO - NÃO ENCONTRADO")
    rel_junho = None

# Verificar relatório de julho/2025
julho_2025 = datetime(2025, 7, 1)
try:
    rel_julho = RelatorioMensalSocio.objects.get(empresa=empresa, socio=socio, competencia=julho_2025)
    print(f"JULHO - impostos_total: {rel_julho.impostos_total}")
    print(f"JULHO - imposto_provisionado_mes_anterior: {rel_julho.imposto_provisionado_mes_anterior}")
    
    # Se junho existe mas julho não tem o valor correto, corrigir
    if rel_junho and rel_julho.imposto_provisionado_mes_anterior != rel_junho.impostos_total:
        print(f"CORRIGINDO: {rel_julho.imposto_provisionado_mes_anterior} -> {rel_junho.impostos_total}")
        rel_julho.imposto_provisionado_mes_anterior = rel_junho.impostos_total
        rel_julho.save()
        print("CORRIGIDO!")
        
except RelatorioMensalSocio.DoesNotExist:
    print("JULHO - NÃO ENCONTRADO")

print("Agora teste na interface!")
