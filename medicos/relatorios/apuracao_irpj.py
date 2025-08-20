from medicos.models.relatorios_apuracao_irpj import ApuracaoIRPJ
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

def montar_relatorio_irpj_persistente(empresa_id, ano):
    empresa = Empresa.objects.get(id=empresa_id)
    aliquota = Aliquotas.obter_aliquota_vigente(empresa)
    resultados = []
    for num_tri, meses in TRIMESTRES:
        competencia = f"T{num_tri}/{ano}"
        
        # Verificar regime tributário da empresa para IRPJ
        if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
            # Regime de competência: considera data de emissão
            notas = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=ano,
                dtEmissao__month__in=meses
            )
        else:
            # Regime de caixa: considera data de recebimento
            notas = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtRecebimento__year=ano,
                dtRecebimento__month__in=meses,
                dtRecebimento__isnull=False  # Só considera notas efetivamente recebidas
            )
        receita_consultas = notas.filter(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        receita_outros = notas.exclude(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        receita_bruta = receita_consultas + receita_outros
        
        # CORREÇÃO: Calcular base de cálculo aplicando presunções específicas por tipo de serviço
        # Base de cálculo para consultas (32% conforme Lei 9.249/1995, art. 15, §1º, III, 'a')
        base_calculo_consultas = receita_consultas * (aliquota.IRPJ_PRESUNCAO_CONSULTA/Decimal('100'))
        # Base de cálculo para outros serviços (32% conforme Lei 9.249/1995, art. 15, §1º, III, 'a')
        base_calculo_outros = receita_outros * (aliquota.IRPJ_PRESUNCAO_OUTROS/Decimal('100'))
        # Base de cálculo total da receita bruta
        base_calculo = base_calculo_consultas + base_calculo_outros
        # Buscar rendimentos e IR de aplicações financeiras do trimestre
        from medicos.models.financeiro import AplicacaoFinanceira
        # Considera aplicações com data_referencia no trimestre e empresa
        aplicacoes = AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano,
            data_referencia__month__in=meses
        )
        rendimentos_aplicacoes = aplicacoes.aggregate(total=Sum('rendimentos'))['total'] or Decimal('0')
        retencao_aplicacao_financeira = aplicacoes.aggregate(total=Sum('ir_cobrado'))['total'] or Decimal('0')
        base_calculo_total = base_calculo + rendimentos_aplicacoes
        imposto_devido = base_calculo_total * (aliquota.IRPJ_ALIQUOTA/Decimal('100'))
        
        # CORREÇÃO: Adicional trimestral conforme Lei 9.249/1995, Art. 3º, §1º
        # Adicional de 10% sobre parcela do LUCRO PRESUMIDO que exceder R$ 60.000,00/trimestre
        # IMPORTANTE: Adicional incide apenas sobre lucro presumido, NÃO sobre rendimentos de aplicações
        adicional = Decimal('0')
        limite_trimestral_legal = Decimal('60000.00')  # R$ 60.000,00/trimestre (3 × R$ 20.000,00/mês)
        
        # Usar apenas a base de cálculo (lucro presumido), excluindo rendimentos de aplicações
        lucro_presumido_trimestral = base_calculo  # Apenas 32% da receita bruta, sem aplicações
        
        if lucro_presumido_trimestral > limite_trimestral_legal:
            excesso_lucro_presumido = lucro_presumido_trimestral - limite_trimestral_legal
            adicional = excesso_lucro_presumido * (Decimal('10.00') / Decimal('100'))  # 10% fixo por lei
        
        imposto_retido_nf = notas.aggregate(total=Sum('val_IR'))['total'] or Decimal('0')
        # já atribuído acima
        imposto_a_pagar = imposto_devido + adicional - imposto_retido_nf - retencao_aplicacao_financeira
        with transaction.atomic():
            obj, _ = ApuracaoIRPJ.objects.update_or_create(
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
                    'adicional': adicional,
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
            'adicional': adicional,
            'imposto_retido_nf': imposto_retido_nf,
            'retencao_aplicacao_financeira': retencao_aplicacao_financeira,
            'imposto_a_pagar': imposto_a_pagar,
        })
    return {'linhas': resultados}
