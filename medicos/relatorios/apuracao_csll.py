from medicos.models.relatorios_apuracao_csll import ApuracaoCSLL
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas
from medicos.models import NotaFiscal
from django.db.models import Sum
from django.db import transaction
from decimal import Decimal

TRIMESTRES = [
    (1, (1, 2, 3)),
    (2, (4, 5, 6)),
    (3, (7, 8, 9)),
    (4, (10, 11, 12)),
]

def montar_relatorio_csll_persistente(empresa_id, ano):
    empresa = Empresa.objects.get(id=empresa_id)
    aliquota = Aliquotas.obter_aliquota_vigente(empresa)
    resultados = []
    for num_tri, meses in TRIMESTRES:
        competencia = f"T{num_tri}/{ano}"
        notas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses
        )
        receita_consultas = notas.filter(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        receita_outros = notas.exclude(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        receita_bruta = receita_consultas + receita_outros
        base_calculo = receita_bruta * (aliquota.CSLL_PRESUNCAO_OUTROS/Decimal('100'))
        # Buscar rendimentos e IR de aplicações financeiras do trimestre
        from medicos.models.financeiro import AplicacaoFinanceira
        aplicacoes = AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano,
            data_referencia__month__in=meses
        )
        rendimentos_aplicacoes = aplicacoes.aggregate(total=Sum('saldo'))['total'] or Decimal('0')
        retencao_aplicacao_financeira = aplicacoes.aggregate(total=Sum('ir_cobrado'))['total'] or Decimal('0')
        base_calculo_total = base_calculo + rendimentos_aplicacoes
        imposto_devido = base_calculo_total * (aliquota.CSLL_ALIQUOTA/Decimal('100'))
        imposto_retido_nf = notas.aggregate(total=Sum('val_CSLL'))['total'] or Decimal('0')
        imposto_a_pagar = imposto_devido - imposto_retido_nf - retencao_aplicacao_financeira
        with transaction.atomic():
            obj, _ = ApuracaoCSLL.objects.update_or_create(
                empresa=empresa,
                competencia=competencia,
                defaults={
                    'receita_consultas': receita_consultas,
                    'receita_outros': receita_outros,
                    'receita_bruta': receita_bruta,
                    'base_calculo': base_calculo,
                    'rendimentos_aplicacoes': rendimentos_aplicacoes,
                    'base_calculo_total': base_calculo_total,
                    'imposto_devido': imposto_devido,
                    'imposto_retido_nf': imposto_retido_nf,
                    'retencao_aplicacao_financeira': retencao_aplicacao_financeira,
                    'imposto_a_pagar': imposto_a_pagar,
                }
            )
        resultados.append({
            'competencia': competencia,
            'receita_consultas': receita_consultas,
            'receita_outros': receita_outros,
            'receita_bruta': receita_bruta,
            'base_calculo': base_calculo,
            'rendimentos_aplicacoes': rendimentos_aplicacoes,
            'base_calculo_total': base_calculo_total,
            'imposto_devido': imposto_devido,
            'imposto_retido_nf': imposto_retido_nf,
            'retencao_aplicacao_financeira': retencao_aplicacao_financeira,
            'imposto_a_pagar': imposto_a_pagar,
        })
    return {'linhas': resultados}
