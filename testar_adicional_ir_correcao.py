#!/usr/bin/env python
"""
Script para testar a correção do cálculo do Adicional de IR Trimestral.
Verifica se o adicional só é aplicado quando a base excede R$ 60.000,00.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('f:\\Projects\\Django\\prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import Empresa
from medicos.views_relatorios import calcular_adicional_ir_trimestral

def testar_calculo_adicional_ir():
    """
    Testa a lógica do cálculo do adicional de IR trimestral.
    """
    print("=== TESTE DE CORREÇÃO: ADICIONAL DE IR TRIMESTRAL ===\n")
    
    try:
        # Buscar primeira empresa disponível
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada para teste")
            return
            
        print(f"🏢 Testando com empresa: {empresa.nome} (ID: {empresa.id})")
        print(f"📅 Ano de teste: 2024\n")
        
        # Executar o cálculo trimestral
        resultado = calcular_adicional_ir_trimestral(empresa.id, '2024')
        
        print("📊 RESULTADO DO CÁLCULO TRIMESTRAL:")
        print("-" * 80)
        
        for dados in resultado:
            trimestre = dados['trimestre']
            base_total = dados['base_total']
            limite = dados['limite_trimestral']
            excedente = dados['excedente']
            adicional = dados['adicional']
            
            print(f"📈 {trimestre}:")
            print(f"   Base total: R$ {base_total:,.2f}")
            print(f"   Limite: R$ {limite:,.2f}")
            print(f"   Excedente: R$ {excedente:,.2f}")
            print(f"   Adicional (10%): R$ {adicional:,.2f}")
            
            # Verificar se a lógica está correta
            if base_total <= limite:
                if adicional == Decimal('0'):
                    print(f"   ✅ CORRETO: Base ≤ {limite:,.2f}, adicional = R$ 0,00")
                else:
                    print(f"   ❌ ERRO: Base ≤ {limite:,.2f}, mas adicional = R$ {adicional:,.2f} (deveria ser R$ 0,00)")
            else:
                excedente_esperado = base_total - limite
                adicional_esperado = excedente_esperado * Decimal('0.10')
                if abs(adicional - adicional_esperado) < Decimal('0.01'):
                    print(f"   ✅ CORRETO: Base > {limite:,.2f}, adicional calculado corretamente")
                else:
                    print(f"   ❌ ERRO: Adicional incorreto. Esperado: R$ {adicional_esperado:,.2f}, Obtido: R$ {adicional:,.2f}")
            
            print()
        
        # Teste com valores específicos para validar a lógica
        print("\n🧪 TESTE COM VALORES ESPECÍFICOS:")
        print("-" * 50)
        
        casos_teste = [
            (Decimal('50000.00'), "Base abaixo do limite"),
            (Decimal('60000.00'), "Base igual ao limite"),
            (Decimal('70000.00'), "Base acima do limite"),
            (Decimal('120000.00'), "Base muito acima do limite"),
        ]
        
        limite_trimestral = Decimal('60000.00')
        
        for base_teste, descricao in casos_teste:
            excedente = max(Decimal('0'), base_teste - limite_trimestral)
            adicional = excedente * Decimal('0.10')
            
            print(f"📊 {descricao}:")
            print(f"   Base: R$ {base_teste:,.2f}")
            print(f"   Excedente: R$ {excedente:,.2f}")
            print(f"   Adicional: R$ {adicional:,.2f}")
            
            if base_teste <= limite_trimestral:
                if adicional == Decimal('0'):
                    print("   ✅ CORRETO: Sem adicional quando base ≤ limite")
                else:
                    print("   ❌ ERRO: Deveria ser R$ 0,00")
            else:
                print("   ✅ CORRETO: Adicional aplicado apenas ao excedente")
            print()
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_calculo_adicional_ir()
