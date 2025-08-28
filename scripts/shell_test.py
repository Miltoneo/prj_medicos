from medicos.models.relatorios import RelatorioMensalSocio
from medicos.models.base import Empresa, Socio
from datetime import datetime, timedelta

# Buscar a primeira empresa
empresa = Empresa.objects.first()
print(f"Empresa: {empresa.nome_fantasia}")

# Buscar o primeiro sócio
socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
print(f"Sócio: {socio.pessoa.name}")

# Buscar relatórios dos últimos 6 meses
hoje = datetime.now()
print("\nRelatórios existentes:")
for i in range(6):
    mes_ref = hoje.replace(day=1) - timedelta(days=i*32)
    mes_ref = mes_ref.replace(day=1)
    
    relatorios = RelatorioMensalSocio.objects.filter(
        empresa=empresa,
        socio=socio,
        competencia=mes_ref
    )
    
    if relatorios.exists():
        rel = relatorios.first()
        print(f"{mes_ref.strftime('%Y-%m')}: impostos_total={rel.impostos_total}, imposto_anterior={rel.imposto_provisionado_mes_anterior}")
    else:
        print(f"{mes_ref.strftime('%Y-%m')}: Não encontrado")

# Testar o cálculo do mês anterior manualmente
competencia_atual = datetime(2025, 8, 1)  # Assumindo agosto 2025
mes_anterior = competencia_atual.replace(day=1) - timedelta(days=1)
mes_anterior = mes_anterior.replace(day=1)
print(f"\nTeste manual:")
print(f"Competência atual: {competencia_atual.strftime('%Y-%m')}")
print(f"Mês anterior calculado: {mes_anterior.strftime('%Y-%m')}")

# Verificar se existe relatório do mês anterior
rel_anterior = RelatorioMensalSocio.objects.filter(
    empresa=empresa,
    socio=socio,
    competencia=mes_anterior
).first()

if rel_anterior:
    print(f"Relatório mês anterior encontrado: impostos_total={rel_anterior.impostos_total}")
else:
    print("Relatório do mês anterior não encontrado")
