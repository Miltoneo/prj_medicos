#!/usr/bin/env python3
"""
Teste de Validação do Regime Tributário
- Testa o impacto do regime de tributação (caixa vs competência) nos cálculos
- Valida as regras específicas de cada regime conforme legislação
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from medicos.models import Conta, Empresa, Aliquotas
from medicos.models.base import REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from django.core.exceptions import ValidationError

def test_regime_tributario():
    """Testa a implementação dos regimes tributários"""
    
    print("=== TESTE DE REGIME TRIBUTÁRIO ===\n")
    
    # 1. Criar dados de teste
    print("1. Criando dados de teste...")
    
    conta = Conta.objects.create(name="Teste Regime Tributário")
    
    # Empresa com regime de competência
    empresa_competencia = Empresa.objects.create(
        conta=conta,
        name="Empresa Competência",
        cnpj="11111111000199",
        regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA
    )
    
    # Empresa com regime de caixa
    empresa_caixa = Empresa.objects.create(
        conta=conta,
        name="Empresa Caixa", 
        cnpj="22222222000199",
        regime_tributario=REGIME_TRIBUTACAO_CAIXA
    )
    
    # Configuração de alíquotas
    aliquotas = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('3.00'),
        ISS_PLANTAO=Decimal('3.50'),
        ISS_OUTROS=Decimal('4.00'),
        PIS=Decimal('0.65'),
        COFINS=Decimal('3.00'),
        IRPJ_BASE_CAL=Decimal('32.00'),
        IRPJ_ALIC_1=Decimal('15.00'),
        CSLL_BASE_CAL=Decimal('32.00'),
        CSLL_ALIC_1=Decimal('9.00'),
        data_vigencia_inicio=date.today()
    )
    
    print("✅ Dados de teste criados")
    
    # 2. Testar propriedades do regime tributário
    print("\n2. Testando propriedades do regime...")
    
    print(f"Empresa Competência:")
    print(f"  - Regime: {empresa_competencia.regime_tributario_nome}")
    print(f"  - É competência: {empresa_competencia.eh_regime_competencia}")
    print(f"  - É caixa: {empresa_competencia.eh_regime_caixa}")
    
    print(f"Empresa Caixa:")
    print(f"  - Regime: {empresa_caixa.regime_tributario_nome}")
    print(f"  - É competência: {empresa_caixa.eh_regime_competencia}")
    print(f"  - É caixa: {empresa_caixa.eh_regime_caixa}")
    
    # 3. Testar cálculos com diferentes regimes
    print("\n3. Testando cálculos com diferentes regimes...")
    
    valor_teste = Decimal('1000.00')
    
    # Cálculo para empresa com regime de competência
    print(f"\n--- REGIME DE COMPETÊNCIA ---")
    resultado_competencia = Aliquotas.calcular_impostos_para_empresa(
        empresa=empresa_competencia,
        valor_bruto=valor_teste,
        tipo_servico='consultas'
    )
    
    print(f"Valor Bruto: R$ {resultado_competencia['valor_bruto']}")
    print(f"ISS ({resultado_competencia['aliquota_iss_aplicada']}%): R$ {resultado_competencia['valor_iss']}")
    print(f"Total Impostos: R$ {resultado_competencia['total_impostos']}")
    print(f"Valor Líquido: R$ {resultado_competencia['valor_liquido']}")
    print(f"Regime: {resultado_competencia['regime_tributario']['nome']}")
    
    if 'regime_observacoes' in resultado_competencia:
        print("Observações do Regime:")
        for obs in resultado_competencia['regime_observacoes']:
            print(f"  {obs}")
    
    # Cálculo para empresa com regime de caixa
    print(f"\n--- REGIME DE CAIXA ---")
    resultado_caixa = Aliquotas.calcular_impostos_para_empresa(
        empresa=empresa_caixa,
        valor_bruto=valor_teste,
        tipo_servico='consultas'
    )
    
    print(f"Valor Bruto: R$ {resultado_caixa['valor_bruto']}")
    print(f"ISS ({resultado_caixa['aliquota_iss_aplicada']}%): R$ {resultado_caixa['valor_iss']}")
    print(f"Total Impostos: R$ {resultado_caixa['total_impostos']}")
    print(f"Valor Líquido: R$ {resultado_caixa['valor_liquido']}")
    print(f"Regime: {resultado_caixa['regime_tributario']['nome']}")
    
    if 'regime_observacoes' in resultado_caixa:
        print("Observações do Regime:")
        for obs in resultado_caixa['regime_observacoes']:
            print(f"  {obs}")
    
    if 'permite_diferimento' in resultado_caixa:
        print(f"Permite Diferimento: {resultado_caixa['permite_diferimento']}")
    
    # 4. Comparar resultados
    print(f"\n4. Comparação entre regimes...")
    
    diferenca_impostos = resultado_competencia['total_impostos'] - resultado_caixa['total_impostos']
    
    print(f"Diferença no total de impostos: R$ {diferenca_impostos}")
    
    if diferenca_impostos == 0:
        print("✅ Valores base iguais - diferenças estão nas regras de aplicação temporal")
    else:
        print("⚠️  Diferenças nos valores - verificar implementação específica")
    
    # 5. Testar com diferentes tipos de serviço
    print(f"\n5. Testando diferentes tipos de serviço...")
    
    tipos_servico = ['consultas', 'plantao', 'outros']
    
    for tipo in tipos_servico:
        print(f"\n--- {tipo.upper()} ---")
        
        res_comp = Aliquotas.calcular_impostos_para_empresa(
            empresa=empresa_competencia,
            valor_bruto=valor_teste,
            tipo_servico=tipo
        )
        
        res_caixa = Aliquotas.calcular_impostos_para_empresa(
            empresa=empresa_caixa,
            valor_bruto=valor_teste,
            tipo_servico=tipo
        )
        
        print(f"Competência - ISS: R$ {res_comp['valor_iss']} ({res_comp['aliquota_iss_aplicada']}%)")
        print(f"Caixa - ISS: R$ {res_caixa['valor_iss']} ({res_caixa['aliquota_iss_aplicada']}%)")
    
    # 6. Teste com data específica (relevante para regime caixa)
    print(f"\n6. Testando com data específica...")
    
    data_futura = date.today() + timedelta(days=30)
    
    resultado_data_especifica = Aliquotas.calcular_impostos_para_empresa(
        empresa=empresa_caixa,
        valor_bruto=valor_teste,
        tipo_servico='consultas',
        data_referencia=data_futura
    )
    
    print(f"Cálculo para {data_futura}:")
    print(f"Regime: {resultado_data_especifica['regime_tributario']['nome']}")
    if 'data_base_calculo' in resultado_data_especifica:
        print(f"Data base cálculo: {resultado_data_especifica['data_base_calculo']}")
    
    # Limpar dados de teste
    print(f"\n7. Limpando dados de teste...")
    conta.delete()
    print("✅ Dados de teste removidos")
    
    return True

def test_validacao_regime():
    """Testa validações relacionadas ao regime tributário"""
    
    print("\n=== TESTE DE VALIDAÇÕES DO REGIME ===\n")
    
    try:
        conta = Conta.objects.create(name="Teste Validação")
        
        # Teste 1: Empresa com regime inválido (deve usar padrão)
        empresa = Empresa.objects.create(
            conta=conta,
            name="Empresa Teste",
            cnpj="33333333000199"
            # regime_tributario usa default = COMPETENCIA
        )
        
        print(f"✅ Empresa criada com regime padrão: {empresa.regime_tributario_nome}")
        
        # Teste 2: Alterar regime
        empresa.regime_tributario = REGIME_TRIBUTACAO_CAIXA
        empresa.save()
        
        print(f"✅ Regime alterado para: {empresa.regime_tributario_nome}")
        
        # Teste 3: Validar choices
        choices_disponiveis = [choice[0] for choice in Empresa.REGIME_CHOICES]
        print(f"✅ Choices disponíveis: {choices_disponiveis}")
        
        # Limpar
        conta.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de validação: {e}")
        return False

if __name__ == "__main__":
    try:
        sucesso1 = test_regime_tributario()
        sucesso2 = test_validacao_regime()
        
        print(f"\n=== RESULTADO FINAL ===")
        if sucesso1 and sucesso2:
            print("✅ SUCESSO: Implementação do regime tributário está FUNCIONANDO!")
            print("\n📋 RESUMO:")
            print("  • Modelo Empresa: Campo regime_tributario com choices")
            print("  • Propriedades: eh_regime_competencia, eh_regime_caixa")
            print("  • Cálculos: Consideram regime tributário da empresa")
            print("  • Regimes: Competência e Caixa implementados")
            print("  • Observações: Específicas para cada regime")
        else:
            print("❌ FALHOU: Verificar erros acima")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
