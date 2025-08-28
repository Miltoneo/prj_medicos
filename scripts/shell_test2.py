from medicos.models.relatorios import RelatorioMensalSocio
from decimal import Decimal

# Listar todos os relatórios e mostrar o campo imposto_provisionado_mes_anterior
relatorios = RelatorioMensalSocio.objects.all().order_by('-competencia')[:10]

print("Últimos 10 relatórios:")
for rel in relatorios:
    print(f"ID: {rel.id}, Competência: {rel.competencia.strftime('%Y-%m')}, "
          f"Empresa: {rel.empresa.nome_fantasia}, Sócio: {rel.socio.pessoa.name}, "
          f"impostos_total: {rel.impostos_total}, "
          f"imposto_provisionado_mes_anterior: {rel.imposto_provisionado_mes_anterior}")

# Testar criação manual de um valor
if relatorios:
    primeiro = relatorios[0]
    print(f"\nTestando com o primeiro relatório:")
    print(f"Valor original: {primeiro.imposto_provisionado_mes_anterior}")
    
    # Atualizar o valor
    primeiro.imposto_provisionado_mes_anterior = Decimal('123.45')
    primeiro.save()
    
    # Recarregar e verificar
    primeiro.refresh_from_db()
    print(f"Valor após atualização: {primeiro.imposto_provisionado_mes_anterior}")
