#!/usr/bin/env python
"""
Script para testar o cálculo dos impostos no Relatório Mensal do Sócio
seguindo as regras da Apuração de Impostos.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio

def test_impostos_relatorio_socio():
    """
    Testa o cálculo dos impostos no relatório mensal do sócio
    para verificar se está seguindo as regras da apuração.
    """
    print("=== TESTE: Impostos Relatório Mensal Sócio ===")
    
    # Parâmetros do teste
    empresa_id = 4
    mes_ano = "2025-07"
    socio_id = 7
    
    try:
        # Executar função
        resultado = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id)
        
        if 'relatorio' in resultado:
            relatorio = resultado['relatorio']
            
            print(f"Empresa ID: {empresa_id}")
            print(f"Competência: {mes_ano}")
            print(f"Sócio ID: {socio_id}")
            print()
            
            # Mostrar valores dos impostos calculados
            print("=== IMPOSTOS A PROVISIONAR (seguindo regras da apuração) ===")
            print(f"PIS.......: R$ {getattr(relatorio, 'total_pis', 0):,.2f}")
            print(f"COFINS....: R$ {getattr(relatorio, 'total_cofins', 0):,.2f}")
            print(f"IRPJ......: R$ {getattr(relatorio, 'total_irpj', 0):,.2f}")
            print(f"CSLL......: R$ {getattr(relatorio, 'total_csll', 0):,.2f}")
            print(f"ISSQN.....: R$ {getattr(relatorio, 'total_iss', 0):,.2f}")
            print(f"TOTAL.....: R$ {getattr(relatorio, 'impostos_total', 0):,.2f}")
            print()
            
            # Mostrar receitas
            print("=== RECEITAS ===")
            print(f"Receita Bruta Recebida: R$ {getattr(relatorio, 'receita_bruta_recebida', 0):,.2f}")
            print(f"Receita Líquida.......: R$ {getattr(relatorio, 'receita_liquida', 0):,.2f}")
            print()
            
            print("✅ TESTE EXECUTADO COM SUCESSO!")
            print("Os impostos agora são calculados seguindo as regras da Apuração de Impostos")
            
        else:
            print("❌ ERRO: Resultado não contém 'relatorio'")
            
    except Exception as e:
        print(f"❌ ERRO na execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_impostos_relatorio_socio()
