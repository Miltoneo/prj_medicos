import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio

# Teste do relatório para empresa_id=4, socio_id=7, mes_ano=2025-07
resultado = montar_relatorio_mensal_socio(4, '2025-07', 7)

print("=== DEBUG IMPOSTOS DEVIDOS ===")
print(f"impostos_devido_total: {resultado.get('impostos_devido_total', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_pis_devido: {resultado.get('total_pis_devido', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_cofins_devido: {resultado.get('total_cofins_devido', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_irpj_devido: {resultado.get('total_irpj_devido', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_csll_devido: {resultado.get('total_csll_devido', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_iss_devido: {resultado.get('total_iss_devido', 'CAMPO NÃO ENCONTRADO')}")

print("\n=== IMPOSTOS A PROVISIONAR (para comparação) ===")
print(f"impostos_total: {resultado.get('impostos_total', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_pis: {resultado.get('total_pis', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_cofins: {resultado.get('total_cofins', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_irpj: {resultado.get('total_irpj', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_csll: {resultado.get('total_csll', 'CAMPO NÃO ENCONTRADO')}")
print(f"total_iss: {resultado.get('total_iss', 'CAMPO NÃO ENCONTRADO')}")
