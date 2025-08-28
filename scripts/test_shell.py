from medicos.models.relatorios import RelatorioMensalSocio

# Verificar relatórios existentes
relatorios = RelatorioMensalSocio.objects.all().order_by('-competencia')[:5]

for rel in relatorios:
    print(f"{rel.competencia.strftime('%Y-%m')}: impostos_total={rel.impostos_total}, imposto_mes_anterior={rel.imposto_provisionado_mes_anterior}")

# Verificar último relatório especificamente
if relatorios:
    ultimo = relatorios[0]
    print(f"\nÚltimo relatório: {ultimo.competencia.strftime('%Y-%m')}")
    print(f"imposto_provisionado_mes_anterior: '{ultimo.imposto_provisionado_mes_anterior}'")
    print(f"Tipo: {type(ultimo.imposto_provisionado_mes_anterior)}")
    
    # Tentar forçar um valor para teste
    ultimo.imposto_provisionado_mes_anterior = 123.45
    ultimo.save()
    ultimo.refresh_from_db()
    print(f"Após update: {ultimo.imposto_provisionado_mes_anterior}")
