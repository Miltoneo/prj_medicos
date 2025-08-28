"""
Builder simplificado para o Relatório Executivo Anual.
Fonte: Simplificação da view complexa em views_relatorios.py
"""

from django.db.models import Sum
from django.db.models import Sum
from datetime import datetime
from decimal import Decimal

from medicos.models.base import Empresa, Socio, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico, Aliquotas
from medicos.models.despesas import DespesaRateada, ItemDespesaRateioMensal, DespesaSocio
from medicos.models.financeiro import Financeiro


def montar_relatorio_executivo_anual(empresa_id, ano=None):
    """
    Builder simplificado para o relatório executivo anual.
    Retorna apenas dados essenciais para reduzir complexidade.
    
    Parâmetros:
    - empresa_id: ID da empresa
    - ano: Ano do relatório (padrão: ano atual)
    
    Retorna:
    - Dict com dados consolidados da empresa por mês
    """
    empresa = Empresa.objects.get(id=empresa_id)
    ano_atual = ano or datetime.now().year
    
    # Dados de notas fiscais por mês (simplificado)
    notas_emitidas_mes = {}
    notas_recebidas_mes = {}
    notas_pendentes_mes = {}
    despesas_coletivas_mes = {}
    
    for mes in range(1, 13):
        # Notas emitidas (valor das notas fiscais emitidas)
        emitidas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano_atual,
            dtEmissao__month=mes
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        notas_emitidas_mes[mes] = emitidas
        
        # Notas recebidas (valor das notas fiscais efetivamente recebidas)
        recebidas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano_atual,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False,
            status_recebimento='recebido'
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        notas_recebidas_mes[mes] = recebidas
        
        # Notas pendentes
        pendentes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano_atual,
            dtEmissao__month=mes,
            status_recebimento__in=['pendente', 'parcial']
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        notas_pendentes_mes[mes] = pendentes
        
        # Despesas coletivas
        despesas = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa=empresa,
            data__year=ano_atual,
            data__month=mes
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
        despesas_coletivas_mes[mes] = despesas
    
    # Totais anuais
    total_emitidas = sum(notas_emitidas_mes.values())
    total_recebidas = sum(notas_recebidas_mes.values())
    total_pendentes = sum(notas_pendentes_mes.values())
    total_despesas_coletivas = sum(despesas_coletivas_mes.values())
    
    return {
        'ano_atual': ano_atual,
        'notas_emitidas_mes': notas_emitidas_mes,
        'notas_recebidas_mes': notas_recebidas_mes,
        'notas_pendentes_mes': notas_pendentes_mes,
        'despesas_coletivas_mes': despesas_coletivas_mes,
        'total_emitidas': total_emitidas,
        'total_recebidas': total_recebidas,
        'total_pendentes': total_pendentes,
        'total_despesas_coletivas': total_despesas_coletivas,
    }


def montar_resumo_demonstrativo_socios(empresa_id, mes_ano=None):
    """
    Builder para resumo demonstrativo por sócio.
    
    Parâmetros:
    - empresa_id: ID da empresa
    - mes_ano: String no formato 'YYYY-MM' (padrão: mês/ano atual)
    
    Retorna:
    - Dict com dados dos sócios no mês/ano especificado
    """
    empresa = Empresa.objects.get(id=empresa_id)
    
    if mes_ano:
        ano, mes = map(int, mes_ano.split('-'))
    else:
        hoje = datetime.now()
        ano, mes = hoje.year, hoje.month
    
    # Buscar sócios ativos da empresa
    socios = Socio.objects.filter(empresa=empresa, ativo=True).select_related('pessoa').order_by('pessoa__name')
    
    resumo_socios = []
    total_receita_emitida = Decimal('0')
    total_receita_bruta = Decimal('0')
    total_imposto_devido = Decimal('0')
    total_imposto_retido = Decimal('0')
    total_imposto_a_pagar = Decimal('0')
    total_receita_liquida = Decimal('0')
    total_despesa_com_rateio = Decimal('0')
    total_despesa_sem_rateio = Decimal('0')
    total_saldo_financeiro = Decimal('0')
    total_saldo_transferir = Decimal('0')
    
    for socio in socios:
        # Receita emitida do sócio no mês (sempre baseada em data de emissão)
        notas_emitidas_socio = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            rateios_medicos__medico=socio,
            dtEmissao__year=ano,
            dtEmissao__month=mes
        ).distinct()
        
        receita_emitida = notas_emitidas_socio.aggregate(
            total_rateio=Sum('rateios_medicos__valor_bruto_medico')
        )['total_rateio'] or Decimal('0')
        
        # CORREÇÃO: Considerar regime de tributação da empresa para base de cálculo do "Imposto Devido"
        # Competência: usa notas emitidas (dtEmissao) | Caixa: usa notas recebidas (dtRecebimento)
        if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
            # Regime de competência: usar notas emitidas (data de emissão)
            notas_base_imposto_devido = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                rateios_medicos__medico=socio,
                dtEmissao__year=ano,
                dtEmissao__month=mes
            ).distinct()
            
            receita_base_imposto_devido = notas_base_imposto_devido.aggregate(
                total_rateio=Sum('rateios_medicos__valor_bruto_medico')
            )['total_rateio'] or Decimal('0')
        else:
            # Regime de caixa: usar notas recebidas (data de recebimento)
            notas_base_imposto_devido = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                rateios_medicos__medico=socio,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False,
                status_recebimento='recebido'
            ).distinct()
            
            receita_base_imposto_devido = notas_base_imposto_devido.aggregate(
                total_rateio=Sum('rateios_medicos__valor_bruto_medico')
            )['total_rateio'] or Decimal('0')
        
        # Nota fiscal recebida do sócio no mês (baseada em data de recebimento) - para "Receita Bruta"
        notas_recebidas_socio = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            rateios_medicos__medico=socio,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False,
            status_recebimento='recebido'
        ).distinct()
        
        receita_bruta = notas_recebidas_socio.aggregate(
            total_rateio=Sum('rateios_medicos__valor_bruto_medico')
        )['total_rateio'] or Decimal('0')
        
        # Impostos retidos: sempre por data de recebimento (valores proporcionais do rateio)
        rateios_socio = NotaFiscalRateioMedico.objects.filter(
            medico=socio,
            nota_fiscal__empresa_destinataria=empresa,
            nota_fiscal__dtRecebimento__year=ano,
            nota_fiscal__dtRecebimento__month=mes,
            nota_fiscal__dtRecebimento__isnull=False,
            nota_fiscal__status_recebimento='recebido'
        )
        
        impostos_retidos_rateados = rateios_socio.aggregate(
            total_iss=Sum('valor_iss_medico'),
            total_pis=Sum('valor_pis_medico'),
            total_cofins=Sum('valor_cofins_medico'),
            total_ir=Sum('valor_ir_medico'),
            total_csll=Sum('valor_csll_medico')
        )
        
        # Imposto retido = valores proporcionais retidos nas notas fiscais (rateio)
        imposto_retido = (
            (impostos_retidos_rateados['total_iss'] or Decimal('0')) +
            (impostos_retidos_rateados['total_pis'] or Decimal('0')) +
            (impostos_retidos_rateados['total_cofins'] or Decimal('0')) +
            (impostos_retidos_rateados['total_ir'] or Decimal('0')) +
            (impostos_retidos_rateados['total_csll'] or Decimal('0'))
        )
        
        # Imposto devido: calculado seguindo regime tributário da empresa sobre a base correta
        aliquotas = Aliquotas.obter_aliquota_vigente(empresa)
        
        if aliquotas and receita_base_imposto_devido > 0:
            # Calcular impostos devidos usando alíquotas sobre a base correta (seguindo regime tributário)
            # ISS: sempre competência por lei (LC 116/2003)
            iss_devido = receita_base_imposto_devido * (aliquotas.ISS / Decimal('100'))
            
            # PIS e COFINS: seguem regime da empresa
            pis_devido = receita_base_imposto_devido * (aliquotas.PIS / Decimal('100'))
            cofins_devido = receita_base_imposto_devido * (aliquotas.COFINS / Decimal('100'))
            
            # IRPJ e CSLL: seguem regime da empresa, com presunção de lucro (32% para consultas)
            base_calculo_ir = receita_base_imposto_devido * (aliquotas.IRPJ_PRESUNCAO_CONSULTA / Decimal('100'))
            base_calculo_csll = receita_base_imposto_devido * (aliquotas.CSLL_PRESUNCAO_CONSULTA / Decimal('100'))
            
            ir_devido = base_calculo_ir * (aliquotas.IRPJ_ALIQUOTA / Decimal('100'))
            csll_devido = base_calculo_csll * (aliquotas.CSLL_ALIQUOTA / Decimal('100'))
            
            imposto_devido = iss_devido + pis_devido + cofins_devido + ir_devido + csll_devido
        else:
            imposto_devido = Decimal('0')
        
        # Imposto a pagar = devido - retido 
        imposto_a_pagar = max(imposto_devido - imposto_retido, Decimal('0'))
        
        # Receita líquida = receita bruta - imposto a pagar
        receita_liquida = receita_bruta - imposto_a_pagar
        
        # Despesas com rateio do sócio no mês
        despesas_rateadas = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa=empresa,
            data__year=ano,
            data__month=mes
        )
        
        despesa_com_rateio = Decimal('0')
        for despesa in despesas_rateadas:
            # Obter configuração de rateio para este sócio/item/mês
            rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                despesa.item_despesa, socio, despesa.data
            )
            if rateio and rateio.percentual_rateio:
                valor_rateado = despesa.valor * (rateio.percentual_rateio / Decimal('100'))
                despesa_com_rateio += valor_rateado
        
        # Despesas sem rateio do sócio no mês (despesas diretas do sócio)
        despesas_socio = DespesaSocio.objects.filter(
            socio=socio,
            data__year=ano,
            data__month=mes
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
        
        despesa_sem_rateio = despesas_socio
        
        # Saldo financeiro do sócio no mês (baseado na tabela Financeiro)
        saldo_financeiro_data = Financeiro.obter_saldo_mensal(
            socio=socio,
            mes_referencia=datetime(ano, mes, 1).date()
        )
        saldo_financeiro = Decimal(str(saldo_financeiro_data.get('saldo_liquido', 0)))
        
        # Saldo transferir = Saldo financeiro - Despesa com rateio - Despesa sem rateio
        saldo_transferir = saldo_financeiro - despesa_com_rateio - despesa_sem_rateio
        
        # Acumular totais
        total_receita_emitida += receita_emitida
        total_receita_bruta += receita_bruta
        total_imposto_devido += imposto_devido
        total_imposto_retido += imposto_retido
        total_imposto_a_pagar += imposto_a_pagar
        total_receita_liquida += receita_liquida
        total_despesa_com_rateio += despesa_com_rateio
        total_despesa_sem_rateio += despesa_sem_rateio
        total_saldo_financeiro += saldo_financeiro
        total_saldo_transferir += saldo_transferir
        
        resumo_socios.append({
            'socio': socio,
            'receita_emitida': receita_emitida,
            'receita_bruta': receita_bruta,
            'imposto_devido': imposto_devido,
            'imposto_retido': imposto_retido,
            'imposto_a_pagar': imposto_a_pagar,
            'receita_liquida': receita_liquida,
            'saldo_financeiro': saldo_financeiro,
            'despesa_com_rateio': despesa_com_rateio,
            'despesa_sem_rateio': despesa_sem_rateio,
            'saldo_transferir': saldo_transferir,
        })
    
    return {
        'resumo_socios': resumo_socios,
        'totais_resumo': {
            'receita_emitida': total_receita_emitida,
            'receita_bruta': total_receita_bruta,
            'imposto_devido': total_imposto_devido,
            'imposto_retido': total_imposto_retido,
            'imposto_a_pagar': total_imposto_a_pagar,
            'receita_liquida': total_receita_liquida,
            'saldo_financeiro': total_saldo_financeiro,
            'despesa_com_rateio': total_despesa_com_rateio,
            'despesa_sem_rateio': total_despesa_sem_rateio,
            'saldo_transferir': total_saldo_transferir,
        },
        'mes_ano_competencia': f"{ano:04d}-{mes:02d}",
        'mes_ano_display': f"{mes:02d}/{ano}",
    }
