from medicos.models.relatorios_apuracao_csll import ApuracaoCSLL
from medicos.models.base import Empresa, REGIME_TRIBUTACAO_COMPETENCIA
from medicos.models.fiscal import Aliquotas
from medicos.models import NotaFiscal
from django.db.models import Sum, Q
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
        
        # Verificar regime tributário da empresa para CSLL
        # EXCLUDINDO notas fiscais canceladas de todos os cálculos
        if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
            # Regime de competência: considera data de emissão
            notas = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=ano,
                dtEmissao__month__in=meses
            ).exclude(status_recebimento='cancelado')
        else:
            # Regime de caixa: considera data de recebimento
            notas = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtRecebimento__year=ano,
                dtRecebimento__month__in=meses,
                dtRecebimento__isnull=False  # Só considera notas efetivamente recebidas
            ).exclude(status_recebimento='cancelado')
        receita_consultas = notas.filter(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        receita_outros = notas.exclude(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        receita_bruta = receita_consultas + receita_outros
        
        # CORREÇÃO: Calcular base de cálculo aplicando presunções específicas por tipo de serviço
        # Base de cálculo para consultas (32% conforme Lei 9.249/1995, art. 20)
        base_calculo_consultas = receita_consultas * (aliquota.CSLL_PRESUNCAO_CONSULTA/Decimal('100'))
        # Base de cálculo para outros serviços (32% conforme Lei 9.249/1995, art. 20)
        base_calculo_outros = receita_outros * (aliquota.CSLL_PRESUNCAO_OUTROS/Decimal('100'))
        # Base de cálculo total da receita bruta
        base_calculo = base_calculo_consultas + base_calculo_outros
        # Buscar rendimentos e IR de aplicações financeiras do trimestre
        from medicos.models.financeiro import AplicacaoFinanceira
        aplicacoes = AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano,
            data_referencia__month__in=meses
        )
        rendimentos_aplicacoes = aplicacoes.aggregate(total=Sum('rendimentos'))['total'] or Decimal('0')
        base_calculo_total = base_calculo + rendimentos_aplicacoes
        imposto_devido = base_calculo_total * (aliquota.CSLL_ALIQUOTA/Decimal('100'))
        
        # CORREÇÃO: Imposto retido sempre considera data de RECEBIMENTO, independente do regime tributário
        notas_recebidas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month__in=meses,
            dtRecebimento__isnull=False  # Só considera notas efetivamente recebidas
        ).exclude(status_recebimento='cancelado')  # Excluir notas canceladas
        imposto_retido_nf = notas_recebidas.aggregate(total=Sum('val_CSLL'))['total'] or Decimal('0')
        imposto_a_pagar = imposto_devido - imposto_retido_nf
        with transaction.atomic():
            obj, _ = ApuracaoCSLL.objects.update_or_create(
                empresa=empresa,
                competencia=competencia,
                defaults={
                    'receita_consultas': receita_consultas,
                    'receita_outros': receita_outros,
                    'receita_bruta': receita_bruta,
                    'base_calculo_consultas': base_calculo_consultas,  # ADICIONADO
                    'base_calculo_outros': base_calculo_outros,  # ADICIONADO
                    'base_calculo': base_calculo,
                    'rendimentos_aplicacoes': rendimentos_aplicacoes,
                    'base_calculo_total': base_calculo_total,
                    'imposto_devido': imposto_devido,
                    'imposto_retido_nf': imposto_retido_nf,
                    'retencao_aplicacao_financeira': Decimal('0'),  # Zerado conforme solicitação
                    'imposto_a_pagar': imposto_a_pagar,
                }
            )
        resultados.append({
            'competencia': competencia,
            'receita_consultas': receita_consultas,
            'receita_outros': receita_outros,
            'receita_bruta': receita_bruta,
            'base_calculo_consultas': base_calculo_consultas,  # ADICIONADO
            'base_calculo_outros': base_calculo_outros,  # ADICIONADO
            'base_calculo': base_calculo,
            'rendimentos_aplicacoes': rendimentos_aplicacoes,
            'base_calculo_total': base_calculo_total,
            'imposto_devido': imposto_devido,
            'imposto_retido_nf': imposto_retido_nf,
            'retencao_aplicacao_financeira': Decimal('0'),  # Zerado conforme solicitação
            'imposto_a_pagar': imposto_a_pagar,
        })
    return {'linhas': resultados}
