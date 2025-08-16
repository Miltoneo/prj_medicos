#!/usr/bin/env python
import os
import sys
import django

# Adicionar o path do projeto
sys.path.insert(0, os.path.dirname(__file__))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio

# Testar com os dados do problema
empresa_id = 4
mes_ano = "2025-07"
socio_id = 7

print("=== TESTE DE CÁLCULO DO PERCENTUAL ===")
print(f"Empresa: {empresa_id}, Mês: {mes_ano}, Sócio: {socio_id}")

relatorio_dict = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)

print("\n=== VALORES DO CONTEXTO ===")
for key, value in relatorio_dict.items():
    if key != 'relatorio':
        print(f"{key}: {value}")

print("\n=== CAMPOS ESPECÍFICOS ===")
print(f"participacao_socio_percentual: {relatorio_dict.get('participacao_socio_percentual', 'NÃO ENCONTRADO')}")
print(f"receita_bruta_socio: {relatorio_dict.get('receita_bruta_socio', 'NÃO ENCONTRADO')}")
print(f"valor_adicional_rateio: {relatorio_dict.get('valor_adicional_rateio', 'NÃO ENCONTRADO')}")
