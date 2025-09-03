#!/usr/bin/env python
import os
import sys
import django

# Adicionar o diretório do projeto ao Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from decimal import Decimal
from medicos.models.fiscal import Aliquotas

def verificar_csll_aliquotas():
    """Verificar se as alíquotas CSLL estão configuradas corretamente"""
    
    print("🔍 Verificando configuração de alíquotas CSLL...")
    
    try:
        # Verificar se existe pelo menos uma configuração de alíquotas
        aliquota = Aliquotas.objects.first()
        if not aliquota:
            print("❌ Nenhuma configuração de alíquotas encontrada")
            return
            
        print(f"✅ Configuração encontrada (ID: {aliquota.id})")
        
        # Verificar campos CSLL
        campos_csll = {
            'CSLL_ALIQUOTA': aliquota.CSLL_ALIQUOTA,
            'CSLL_PRESUNCAO_CONSULTA': aliquota.CSLL_PRESUNCAO_CONSULTA,
            'CSLL_PRESUNCAO_OUTROS': aliquota.CSLL_PRESUNCAO_OUTROS
        }
        
        for campo, valor in campos_csll.items():
            print(f"   {campo}: {valor}%")
            
        # Testar cálculo simulado
        receita_consultas = Decimal('10000.00')
        receita_outros = Decimal('5000.00')
        
        base_consultas = receita_consultas * (aliquota.CSLL_PRESUNCAO_CONSULTA / Decimal('100'))
        base_outros = receita_outros * (aliquota.CSLL_PRESUNCAO_OUTROS / Decimal('100'))
        base_total = base_consultas + base_outros
        imposto_devido = base_total * (aliquota.CSLL_ALIQUOTA / Decimal('100'))
        
        print(f"\n📊 Simulação de cálculo CSLL:")
        print(f"   Receita consultas: R$ {receita_consultas}")
        print(f"   Receita outros: R$ {receita_outros}")
        print(f"   Base consultas ({aliquota.CSLL_PRESUNCAO_CONSULTA}%): R$ {base_consultas}")
        print(f"   Base outros ({aliquota.CSLL_PRESUNCAO_OUTROS}%): R$ {base_outros}")
        print(f"   Base total: R$ {base_total}")
        print(f"   Imposto devido ({aliquota.CSLL_ALIQUOTA}%): R$ {imposto_devido}")
        
        print("\n✅ Verificação de alíquotas CSLL concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")

if __name__ == "__main__":
    verificar_csll_aliquotas()
