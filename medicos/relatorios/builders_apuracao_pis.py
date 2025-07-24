from medicos.models.relatorios_apuracao_pis import ApuracaoPIS
from medicos.models.base import Empresa
from medicos.models.notafiscal import NotaFiscal
from django.db.models import Sum

def calcular_e_salvar_apuracao_pis(empresa, competencia, aliquota):
    notas = NotaFiscal.objects.filter(empresa=empresa, competencia=competencia)
    base_calculo = notas.aggregate(total=Sum('valor_total'))['total'] or 0
    imposto_devido = base_calculo * (aliquota / 100)
    imposto_retido_nf = notas.aggregate(total=Sum('valor_pis_retido'))['total'] or 0
    # Buscar crédito do mês anterior
    apuracao_anterior = ApuracaoPIS.objects.filter(empresa=empresa, competencia=_competencia_anterior(competencia)).first()
    credito_mes_anterior = apuracao_anterior.credito_mes_seguinte if apuracao_anterior else 0
    # Calcular valor total para pagamento
    valor_total = (imposto_devido - imposto_retido_nf) + credito_mes_anterior
    if valor_total < 10:
        imposto_a_pagar = 0
        credito_mes_seguinte = valor_total
    else:
        imposto_a_pagar = valor_total
        credito_mes_seguinte = 0
    apuracao, _ = ApuracaoPIS.objects.update_or_create(
        empresa=empresa,
        competencia=competencia,
        defaults={
            'base_calculo': base_calculo,
            'aliquota': aliquota,
            'imposto_devido': imposto_devido,
            'imposto_retido_nf': imposto_retido_nf,
            'imposto_a_pagar': imposto_a_pagar,
            'credito_mes_anterior': credito_mes_anterior,
            'credito_mes_seguinte': credito_mes_seguinte,
        }
    )
    return apuracao

# Função utilitária para obter competência anterior (MM/YYYY)
def _competencia_anterior(competencia):
    from datetime import datetime
    mes, ano = map(int, competencia.split('/'))
    if mes == 1:
        mes = 12
        ano -= 1
    else:
        mes -= 1
    return f'{mes:02d}/{ano}'
