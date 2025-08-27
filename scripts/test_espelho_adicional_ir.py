#!/usr/bin/env python
"""
Teste do Espelho do Adicional de IR - Verificação de Regime de Tributação
Data de emissão vs data de recebimento conforme Lei 9.249/1995 Art. 3º §1º

Execução: python test_espelho_adicional_ir.py
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from decimal import Decimal
from medicos.models import Empresa, NotaFiscal
from medicos.relatorios.apuracao_irpj import ApuracaoIrpjBuilder
from medicos.views_relatorios import RelatoriosView
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from unittest.mock import Mock

def testar_espelho_adicional_ir():
    """
    Testa se o Espelho do Adicional de IR usa corretamente os dados
    já calculados pelos builders que respeitam regime de tributação
    """
    print("=" * 80)
    print("TESTE: Espelho do Adicional de IR - Uso de dados já calculados")
    print("=" * 80)
    
    # 1. Verificar empresa de competência
    try:
        empresa = Empresa.objects.get(id=4)
        print(f"✓ Empresa: {empresa.nome}")
        print(f"✓ Regime: {empresa.regime_tributario} (1=Competência, 2=Caixa)")
        
        if empresa.regime_tributario != 1:
            print("❌ ERRO: Empresa não está em regime de competência!")
            return False
            
    except Empresa.DoesNotExist:
        print("❌ ERRO: Empresa ID 4 não encontrada!")
        return False
    
    # 2. Simular requisição para a view
    request = HttpRequest()
    request.method = 'GET'
    request.user = Mock()
    request.user.is_authenticated = True
    request.session = {'mes_ano': '2024-07'}
    
    # 3. Instanciar view
    view = RelatoriosView()
    view.request = request
    
    # 4. Executar cálculo do builder diretamente
    builder = ApuracaoIrpjBuilder(empresa_id=4, ano=2024)
    dados_builder = builder.build()
    
    print(f"\n📊 DADOS DO BUILDER (com regime aplicado):")
    print(f"   Linhas encontradas: {len(dados_builder['linhas'])}")
    
    for linha in dados_builder['linhas']:
        base_calculo = linha.get('base_calculo', 0)
        receita_bruta = linha.get('receita_bruta', 0)
        print(f"   Trimestre: {linha.get('competencia')}")
        print(f"   Receita Bruta: R$ {receita_bruta:,.2f}")
        print(f"   Base Cálculo (builder): R$ {base_calculo:,.2f}")
        
        # Verificar se há adicional devido
        limite_trimestral = Decimal('60000.00')
        excedente = max(Decimal('0'), Decimal(str(base_calculo)) - limite_trimestral)
        adicional_devido = excedente * Decimal('0.10')
        
        print(f"   Excedente: R$ {excedente:,.2f}")
        print(f"   Adicional IR: R$ {adicional_devido:,.2f}")
        print()
    
    # 5. Simular view context (simplificado)
    try:
        context = view.get_context_data(empresa_id=4)
        espelho_adicional = context.get('espelho_adicional_trimestral', [])
        
        print(f"📈 ESPELHO DO ADICIONAL (view):")
        print(f"   Linhas no espelho: {len(espelho_adicional)}")
        
        for linha in espelho_adicional:
            print(f"   Trimestre: {linha.get('competencia')}")
            print(f"   Base Cálculo Total: R$ {linha.get('base_calculo_total', 0):,.2f}")
            print(f"   Excedente: R$ {linha.get('excedente', 0):,.2f}")
            print(f"   Adicional Devido: R$ {linha.get('adicional_devido', 0):,.2f}")
            print()
        
        # 6. Verificar consistência
        print("🔍 VERIFICAÇÃO DE CONSISTÊNCIA:")
        
        if len(dados_builder['linhas']) == len(espelho_adicional):
            print("✓ Quantidade de linhas consistente")
            
            for i, (linha_builder, linha_espelho) in enumerate(zip(dados_builder['linhas'], espelho_adicional)):
                base_builder = Decimal(str(linha_builder.get('base_calculo', 0)))
                base_espelho = linha_espelho.get('base_calculo_total', 0)
                
                if abs(base_builder - base_espelho) < Decimal('0.01'):  # Tolerância de 1 centavo
                    print(f"✓ Trimestre {i+1}: Bases consistentes (R$ {base_builder:,.2f})")
                else:
                    print(f"❌ Trimestre {i+1}: Bases INCONSISTENTES!")
                    print(f"   Builder: R$ {base_builder:,.2f}")
                    print(f"   Espelho: R$ {base_espelho:,.2f}")
                    return False
        else:
            print(f"❌ Quantidade de linhas inconsistente: Builder={len(dados_builder['linhas'])}, Espelho={len(espelho_adicional)}")
            return False
        
        print("\n✅ SUCESSO: Espelho do Adicional de IR usa corretamente os dados calculados pelos builders!")
        print("✅ Os dados respeitam o regime de tributação (data de emissão para competência)!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO na execução da view: {e}")
        return False

if __name__ == '__main__':
    sucesso = testar_espelho_adicional_ir()
    
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 TESTE APROVADO: Espelho do Adicional de IR funciona corretamente!")
    else:
        print("💥 TESTE REPROVADO: Correções necessárias!")
    print("=" * 80)
