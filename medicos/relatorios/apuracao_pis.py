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
    for mes in range(1, 13):
        competencia = f'{mes:02d}/{ano}'
        notas_mes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=int(ano),
            dtEmissao__month=mes
        )
        base_calculo = sum(float(nf.val_bruto or 0) for nf in notas_mes)
        aliquota_obj = Aliquotas.objects.filter(
            empresa=empresa,
            data_vigencia_inicio__lte=f'{ano}-12-31',
        ).order_by('-data_vigencia_inicio').first()
        aliquota = float(getattr(aliquota_obj, 'PIS', 0)) if aliquota_obj else 0
        imposto_devido = round(base_calculo * (aliquota / 100), 2)
        imposto_retido_nf = sum(float(nf.val_PIS or 0) for nf in notas_mes if getattr(nf, 'retido', False))
        # TODO: Consultar regra/documentação para crédito_mes_anterior e crédito_mes_seguinte
        credito_mes_anterior = 0
        credito_mes_seguinte = 0
        imposto_a_pagar = round(imposto_devido - imposto_retido_nf + credito_mes_anterior - credito_mes_seguinte, 2)
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
    totais = {
        'total_pis': total_pis,
        'total_base_calculo': total_base_calculo,
        'total_retido': total_retido,
        'total_a_pagar': total_a_pagar,
    }
    return {
        'linhas': linhas,
        'totais': totais,
    }
