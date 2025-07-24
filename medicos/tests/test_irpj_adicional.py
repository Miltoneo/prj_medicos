"""
Teste unitário para cálculo do adicional de IRPJ e sua propagação para o relatório mensal do sócio.
Regras e fontes:
- medicos/models/fiscal.py, métodos Aliquotas.calcular_impostos_nf e calcular_impostos_com_regime
- .github/copilot-instructions.md, seção 4 e 2
"""
import pytest
from decimal import Decimal
from medicos.models.fiscal import Aliquotas

@pytest.mark.django_db
def test_calculo_adicional_irpj():
    aliquota = Aliquotas.objects.create(
        ISS=2,
        PIS=1,
        COFINS=3,
        IRPJ_BASE_CAL=100,
        CSLL_BASE_CAL=100,
        IRPJ_ALIQUOTA_OUTROS=15,
        CSLL_ALIQUOTA_OUTROS=9,
        IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL=Decimal('20000.00'),
        IRPJ_ADICIONAL=Decimal('10.00'),
        ativa=True
    )
    valor_bruto = Decimal('30000.00')
    resultado = aliquota.calcular_impostos_nf(valor_bruto)
    # Excedente: 30000 - 20000 = 10000, adicional: 10000 * 10% = 1000
    assert resultado['valor_ir_adicional'] == Decimal('1000.00')
    # Se valor_bruto abaixo do limite, adicional deve ser zero
    resultado2 = aliquota.calcular_impostos_nf(Decimal('15000.00'))
    assert resultado2['valor_ir_adicional'] == Decimal('0.00')
