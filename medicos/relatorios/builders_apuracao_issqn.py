from medicos.models.fiscal import NotaFiscal
from medicos.models.base import Empresa
from medicos.models.relatorios_apuracao_issqn import ApuracaoISSQN

def calcular_e_salvar_apuracao_issqn(empresa, competencia, aliquota_iss):
    notas = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtEmissao__startswith=competencia  # MM/YYYY
    )
    base_calculo = sum(n.valor_servico for n in notas)
    imposto_devido = base_calculo * aliquota_iss / 100
    imposto_retido_nf = sum(n.valor_iss_retido for n in notas)
    imposto_a_pagar = imposto_devido - imposto_retido_nf
    apuracao, created = ApuracaoISSQN.objects.update_or_create(
        empresa=empresa,
        competencia=competencia,
        defaults={
            'base_calculo': base_calculo,
            'imposto_devido': imposto_devido,
            'imposto_retido_nf': imposto_retido_nf,
            'imposto_a_pagar': imposto_a_pagar,
        }
    )
    return apuracao
