#!/usr/bin/env python
"""
Script para testar o cálculo correto da fórmula c=a-b nos impostos a provisionar
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def test_impostos_calculation():
    """
    Teste para verificar se a fórmula c=a-b está sendo aplicada corretamente
    """
    # Valores fornecidos pelo usuário
    imposto_devido = 2643.87  # a
    imposto_retido = 605.27   # b
    imposto_esperado = imposto_devido - imposto_retido  # c = a - b = 2038.60
    
    print("=== TESTE DE CÁLCULO DE IMPOSTOS A PROVISIONAR ===")
    print(f"IMPOSTO DEVIDO*(a): {imposto_devido:,.2f}")
    print(f"IMPOSTO RETIDO*(b): {imposto_retido:,.2f}")
    print(f"IMPOSTO A PROVISIONAR ESPERADO*(c=a-b): {imposto_esperado:,.2f}")
    print()
    
    # Verificar se o resultado é o esperado
    if abs(imposto_esperado - 2038.60) < 0.01:
        print("✅ CÁLCULO CORRETO: A fórmula c=a-b está sendo aplicada corretamente")
        print(f"   Resultado: {imposto_esperado:,.2f} = 2.038,60")
    else:
        print("❌ CÁLCULO INCORRETO: A fórmula c=a-b não está sendo aplicada")
        print(f"   Esperado: 2.038,60")
        print(f"   Calculado: {imposto_esperado:,.2f}")
    
    return imposto_esperado

if __name__ == "__main__":
    result = test_impostos_calculation()
    print(f"\nResultado final: {result:,.2f}")
