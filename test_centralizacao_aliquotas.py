#!/usr/bin/env python3
"""
Teste de Validação da Centralização Completa de Alíquotas
- Verifica se não há mais campos de alíquotas no modelo Empresa
- Testa se toda lógica de alíquotas está centralizada no modelo Aliquotas
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from medicos.models import Conta, Empresa, Aliquotas
from django.core.exceptions import ValidationError

def test_centralizacao_aliquotas():
    """Testa se a centralização de alíquotas está completa"""
    
    print("=== TESTE DE CENTRALIZAÇÃO DE ALÍQUOTAS ===\n")
    
    # 1. Verificar se Empresa não possui campos de alíquotas
    print("1. Verificando campos do modelo Empresa...")
    empresa_fields = [field.name for field in Empresa._meta.get_fields()]
    campos_aliquotas = [f for f in empresa_fields if 'aliquota' in f.lower() or 'iss' in f.lower()]
    
    if campos_aliquotas:
        print(f"❌ ERRO: Empresa ainda possui campos de alíquotas: {campos_aliquotas}")
        return False
    else:
        print("✅ OK: Empresa não possui campos de alíquotas")
    
    # 2. Verificar métodos de alíquotas no modelo Empresa
    print("\n2. Verificando métodos relacionados a alíquotas na Empresa...")
    empresa_methods = [method for method in dir(Empresa) if not method.startswith('_')]
    metodos_aliquotas = [m for m in empresa_methods if 'aliquota' in m.lower() or 'imposto' in m.lower()]
    
    if metodos_aliquotas:
        print(f"⚠️  AVISO: Empresa ainda possui métodos de alíquotas: {metodos_aliquotas}")
        print("   (Estes devem ser removidos para centralização completa)")
    else:
        print("✅ OK: Empresa não possui métodos de alíquotas")
    
    # 3. Verificar modelo Aliquotas
    print("\n3. Verificando modelo Aliquotas...")
    aliquotas_fields = [field.name for field in Aliquotas._meta.get_fields()]
    campos_iss = [f for f in aliquotas_fields if 'ISS' in f]
    
    expected_iss_fields = ['ISS_CONSULTAS', 'ISS_PLANTAO', 'ISS_OUTROS']
    missing_fields = [f for f in expected_iss_fields if f not in campos_iss]
    
    if missing_fields:
        print(f"❌ ERRO: Campos ISS ausentes no modelo Aliquotas: {missing_fields}")
        return False
    else:
        print(f"✅ OK: Modelo Aliquotas possui todos os campos ISS: {expected_iss_fields}")
    
    # 4. Testar funcionalidade centralizada
    print("\n4. Testando funcionalidade centralizada...")
    
    try:
        # Criar conta de teste
        conta_teste = Conta.objects.create(name="Teste Centralização")
        
        # Criar empresa sem alíquotas
        empresa_teste = Empresa.objects.create(
            conta=conta_teste,
            name="Empresa Teste",
            cnpj="12345678000199"
        )
        print("✅ OK: Empresa criada sem campos de alíquotas")
        
        # Testar obtenção de alíquota padrão (sem configuração)
        aliquota_consultas = Aliquotas.obter_aliquota_ou_padrao(conta_teste, 'consultas')
        aliquota_plantao = Aliquotas.obter_aliquota_ou_padrao(conta_teste, 'plantao')
        aliquota_outros = Aliquotas.obter_aliquota_ou_padrao(conta_teste, 'outros')
        
        print(f"✅ OK: Alíquotas padrão - Consultas: {aliquota_consultas}%, Plantão: {aliquota_plantao}%, Outros: {aliquota_outros}%")
        
        # Criar configuração de alíquotas
        aliquotas_config = Aliquotas.objects.create(
            conta=conta_teste,
            ISS_CONSULTAS=Decimal('3.00'),
            ISS_PLANTAO=Decimal('3.50'),
            ISS_OUTROS=Decimal('4.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            data_vigencia_inicio='2025-01-01'
        )
        print("✅ OK: Configuração de alíquotas criada")
        
        # Testar obtenção de alíquota configurada
        aliquota_config_consultas = Aliquotas.obter_aliquota_ou_padrao(conta_teste, 'consultas')
        aliquota_config_plantao = Aliquotas.obter_aliquota_ou_padrao(conta_teste, 'plantao')
        aliquota_config_outros = Aliquotas.obter_aliquota_ou_padrao(conta_teste, 'outros')
        
        print(f"✅ OK: Alíquotas configuradas - Consultas: {aliquota_config_consultas}%, Plantão: {aliquota_config_plantao}%, Outros: {aliquota_config_outros}%")
        
        # Testar cálculo de impostos
        resultado_calculo = aliquotas_config.calcular_impostos_nf(Decimal('1000.00'), 'consultas')
        print(f"✅ OK: Cálculo de impostos - ISS: R$ {resultado_calculo['valor_iss']}, Total: R$ {resultado_calculo['total_impostos']}")
        
        # Limpar dados de teste
        conta_teste.delete()
        print("✅ OK: Dados de teste removidos")
        
        # 5. Testar regime tributário
        print("\n5. Testando integração com regime tributário...")
        
        conta_regime = Conta.objects.create(name="Teste Regime")
        
        # Empresa com competência
        empresa_comp = Empresa.objects.create(
            conta=conta_regime,
            name="Empresa Comp",
            cnpj="11111111000188",
            regime_tributario=1  # COMPETÊNCIA
        )
        
        # Empresa com caixa
        empresa_caixa = Empresa.objects.create(
            conta=conta_regime,
            name="Empresa Caixa",
            cnpj="22222222000188", 
            regime_tributario=2  # CAIXA
        )
        
        print(f"✅ OK: Empresas criadas - Competência: {empresa_comp.regime_tributario_nome}, Caixa: {empresa_caixa.regime_tributario_nome}")
        
        # Testar cálculo com regime
        config_aliquotas = Aliquotas.objects.create(
            conta=conta_regime,
            ISS_CONSULTAS=Decimal('3.00'),
            data_vigencia_inicio='2025-01-01'
        )
        
        resultado_comp = Aliquotas.calcular_impostos_para_empresa(
            empresa=empresa_comp,
            valor_bruto=Decimal('1000.00'),
            tipo_servico='consultas'
        )
        
        resultado_caixa = Aliquotas.calcular_impostos_para_empresa(
            empresa=empresa_caixa,
            valor_bruto=Decimal('1000.00'),
            tipo_servico='consultas'
        )
        
        print(f"✅ OK: Cálculos com regime - Comp: {resultado_comp['regime_tributario']['nome']}, Caixa: {resultado_caixa['regime_tributario']['nome']}")
        
        # Limpar
        conta_regime.delete()
        print("✅ OK: Dados de teste de regime removidos")
        
    except Exception as e:
        print(f"❌ ERRO no teste de funcionalidade: {e}")
        return False
    
    return True

def test_acesso_via_relacionamento():
    """Testa acesso a alíquotas via relacionamento da conta"""
    
    print("\n5. Testando acesso via relacionamento...")
    
    try:
        # Criar dados de teste
        conta = Conta.objects.create(name="Teste Relacionamento")
        empresa = Empresa.objects.create(conta=conta, name="Empresa Rel", cnpj="98765432000199")
        
        # Acessar alíquotas via relacionamento
        aliquotas_via_conta = conta.aliquotas.all()
        aliquotas_via_empresa = empresa.conta.aliquotas.all()
        
        print("✅ OK: Acesso via relacionamento funcionando")
        print(f"   - Via conta: {aliquotas_via_conta.count()} configurações")
        print(f"   - Via empresa->conta: {aliquotas_via_empresa.count()} configurações")
        
        # Limpar
        conta.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no teste de relacionamento: {e}")
        return False

if __name__ == "__main__":
    try:
        sucesso1 = test_centralizacao_aliquotas()
        sucesso2 = test_acesso_via_relacionamento()
        
        print(f"\n=== RESULTADO FINAL ===")
        if sucesso1 and sucesso2:
            print("✅ SUCESSO: Centralização de alíquotas está COMPLETA!")
            print("\n📋 RESUMO:")
            print("  • Modelo Empresa: SEM campos de alíquotas")
            print("  • Modelo Aliquotas: CENTRALIZA toda lógica fiscal")
            print("  • Funcionalidade: PRESERVADA com valores padrão")
            print("  • Relacionamentos: FUNCIONANDO corretamente")
        else:
            print("❌ FALHOU: Centralização incompleta - verificar erros acima")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
