"""
Apuração IRPJ Mensal - Pagamento por Estimativa
Fonte: Lei 9.430/1996, Art. 2º - Pagamento mensal por estimativa

Este módulo implementa o cálculo do IRPJ mensal conforme Art. 2º da Lei 9.430/1996,
que permite às pessoas jurídicas optarem pelo pagamento mensal do imposto sobre
base de cálculo estimada.

A apuração definitiva continua sendo trimestral (Art. 1º), mas o pagamento mensal
por estimativa facilita o fluxo de caixa e planejamento tributário.
"""

from medicos.models.relatorios_apuracao_irpj_mensal import ApuracaoIRPJMensal
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas
from medicos.models import NotaFiscal
from django.db.models import Sum
from django.db import transaction
from decimal import Decimal
from datetime import datetime

MESES = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]

def montar_relatorio_irpj_mensal_persistente(empresa_id, ano):
    """
    Monta relatório IRPJ mensal por estimativa conforme Lei 9.430/1996, Art. 2º.
    
    Parâmetros:
    - empresa_id: ID da empresa para cálculo
    - ano: Ano da apuração (string ou int)
    
    Retorna:
    - Dictionary com 'linhas' contendo os cálculos mensais
    """
    empresa = Empresa.objects.get(id=empresa_id)
    aliquota = Aliquotas.obter_aliquota_vigente(empresa)
    resultados = []
    
    for num_mes, nome_mes in MESES:
        competencia = f"{num_mes:02d}/{ano}"
        
        # Buscar notas fiscais do mês
        notas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month=num_mes
        )
        
        # Receitas por tipo de serviço
        receita_consultas = notas.filter(
            tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        
        receita_outros = notas.exclude(
            tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        
        receita_bruta = receita_consultas + receita_outros
        
        # CORREÇÃO: Base de cálculo mensal conforme Art. 2º da Lei 9.430/1996
        # Aplica percentuais específicos de presunção por tipo de serviço
        # Base de cálculo para consultas (32% conforme Lei 9.249/1995, art. 15, §1º, III, 'a')
        base_calculo_consultas = receita_consultas * (aliquota.IRPJ_PRESUNCAO_CONSULTA / Decimal('100'))
        # Base de cálculo para outros serviços (32% conforme Lei 9.249/1995, art. 15, §1º, III, 'a') 
        base_calculo_outros = receita_outros * (aliquota.IRPJ_PRESUNCAO_OUTROS / Decimal('100'))
        # Base de cálculo total da receita bruta
        base_calculo = base_calculo_consultas + base_calculo_outros
        
        # Buscar rendimentos e IR de aplicações financeiras do mês
        from medicos.models.financeiro import AplicacaoFinanceira
        aplicacoes = AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano,
            data_referencia__month=num_mes
        )
        
        rendimentos_aplicacoes = aplicacoes.aggregate(
            total=Sum('rendimentos')
        )['total'] or Decimal('0')
        
        retencao_aplicacao_financeira = aplicacoes.aggregate(
            total=Sum('ir_cobrado')
        )['total'] or Decimal('0')
        
        base_calculo_total = base_calculo + rendimentos_aplicacoes
        
        # Imposto devido mensal (15% sobre base de cálculo)
        imposto_devido = base_calculo_total * (aliquota.IRPJ_ALIQUOTA / Decimal('100'))
        
        # CORREÇÃO: Adicional mensal conforme Lei 9.249/1995, Art. 3º, §1º
        # Adicional de 10% sobre parcela do LUCRO PRESUMIDO que exceder R$ 20.000,00/mês
        # IMPORTANTE: Adicional incide apenas sobre lucro presumido, NÃO sobre rendimentos de aplicações
        adicional = Decimal('0')
        limite_mensal_legal = Decimal('20000.00')  # R$ 20.000,00/mês (Lei 9.249/1995)
        
        # Usar apenas a base de cálculo (lucro presumido), excluindo rendimentos de aplicações
        lucro_presumido_mensal = base_calculo  # Apenas 32% da receita bruta, sem aplicações
        
        if lucro_presumido_mensal > limite_mensal_legal:
            excesso_lucro_presumido = lucro_presumido_mensal - limite_mensal_legal
            adicional = excesso_lucro_presumido * (Decimal('10.00') / Decimal('100'))  # 10% fixo por lei
        
        # Impostos retidos nas notas fiscais
        imposto_retido_nf = notas.aggregate(
            total=Sum('val_IR')
        )['total'] or Decimal('0')
        
        # Imposto a pagar no mês
        imposto_a_pagar = imposto_devido + adicional - imposto_retido_nf - retencao_aplicacao_financeira
        
        # Salvar no banco para persistência
        with transaction.atomic():
            obj, _ = ApuracaoIRPJMensal.objects.update_or_create(
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
        
        # Adicionar ao resultado
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
            'aliquota': float(aliquota.IRPJ_ALIQUOTA),  # Adicionar alíquota para exibição
        })
    
    return {'linhas': resultados}
