from datetime import datetime
from django.db.models import Sum
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas, NotaFiscal
from medicos.models.relatorios_apuracao_pis import ApuracaoPIS

# Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios


# Função utilitária para obter competência anterior (MM/YYYY)
def _competencia_anterior(competencia):
    """
    Retorna a competência anterior no formato MM/YYYY.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    """
    mes, ano = map(int, competencia.split('/'))
    if mes == 1:
        return f'12/{ano-1}'
    else:
        return f'{mes-1:02d}/{ano}'

def montar_relatorio_pis_persistente(empresa_id, ano):
    """
    Monta e persiste os dados do relatório de apuração de PIS para cada competência do ano.
    Retorna dict padronizado: {'linhas': [...], 'totais': {...}}
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    """
    empresa = Empresa.objects.get(id=empresa_id)
    linhas = []
    total_pis = 0
    total_base_calculo = 0
    total_retido = 0
    total_a_pagar = 0
    # Regra de valor mínimo de pagamento do PIS:
    # Se o valor apurado for inferior a R$ 10,00, o pagamento é acumulado para a competência seguinte.
    # Fonte: IN RFB nº 1.717/2017, art. 68. Exemplo: competência 03/2025 apura R$ 7,50, não gera pagamento, acumula para 04/2025.
    VALOR_MINIMO_PAGAMENTO = 10.00  # Fonte: IN RFB nº 1.717/2017, art. 68
    saldo_acumulado = 0.0
    for mes in range(1, 13):
        competencia = f'{mes:02d}/{ano}'
        
        # Notas para base de cálculo (data de emissão)
        notas_mes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=int(ano),
            dtEmissao__month=mes
        )
        base_calculo = sum(float(nf.val_bruto or 0) for nf in notas_mes)
        
        # Alíquota vigente
        aliquota_obj = Aliquotas.objects.filter(
            empresa=empresa,
            data_vigencia_inicio__lte=f'{ano}-12-31',
        ).order_by('-data_vigencia_inicio').first()
        aliquota = float(getattr(aliquota_obj, 'PIS', 0)) if aliquota_obj else 0
        imposto_devido = round(base_calculo * (aliquota / 100), 2)
        
        # Imposto retido considerando data de RECEBIMENTO da nota fiscal
        notas_recebidas_mes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=int(ano),
            dtRecebimento__month=mes
        )
        imposto_retido_nf = sum(float(nf.val_PIS or 0) for nf in notas_recebidas_mes)
        
        credito_mes_anterior = saldo_acumulado
        credito_mes_seguinte = 0
        imposto_a_pagar = round(imposto_devido - imposto_retido_nf + credito_mes_anterior - credito_mes_seguinte, 2)
        if imposto_a_pagar < VALOR_MINIMO_PAGAMENTO:
            saldo_acumulado = imposto_a_pagar
            imposto_a_pagar = 0.0
            credito_mes_seguinte = saldo_acumulado
        else:
            saldo_acumulado = 0.0
        obj, _ = ApuracaoPIS.objects.update_or_create(
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
        linhas.append({
            'competencia': competencia,
            'base_calculo': base_calculo,
            'aliquota': aliquota,
            'imposto_devido': imposto_devido,
            'imposto_retido_nf': imposto_retido_nf,
            'imposto_a_pagar': imposto_a_pagar,
            'credito_mes_anterior': credito_mes_anterior,
            'credito_mes_seguinte': credito_mes_seguinte,
        })
        total_pis += imposto_devido
        total_base_calculo += base_calculo
        total_retido += imposto_retido_nf
        total_a_pagar += imposto_a_pagar
    return {
        'linhas': linhas,
        'totais': {
            'total_base_calculo': total_base_calculo,
            'total_imposto_devido': total_pis,
            'total_imposto_retido_nf': total_retido,
            'total_imposto_a_pagar': total_a_pagar,
        },
    }
