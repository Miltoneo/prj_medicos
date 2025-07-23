


# =========================
# Imports padronizados
# =========================
# Python Standard
from datetime import datetime

# Django
from django.db.models import Sum

# Imports internos do projeto
from medicos.models.base import Empresa, Socio
from medicos.models.despesas import DespesaRateada, DespesaSocio, ItemDespesa, GrupoDespesa



# Imports de módulos de negócio
from medicos.models.fiscal import Aliquotas, NotaFiscal
from medicos.models.financeiro import Financeiro
from medicos.models.relatorios import RelatorioMensalSocio

def montar_relatorio_mensal_empresa(empresa_id, mes_ano):
    """
    Monta os dados do relatório mensal da empresa.
    Retorna dict padronizado: {'relatorio': ...}
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    """
    empresa = Empresa.objects.get(id=empresa_id)
    competencia = datetime.strptime(mes_ano, "%Y-%m")

    # TODO: Implementar lógica do relatório mensal da empresa conforme regras de negócio
    return {'relatorio': {}}


def montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=None):
    """
    Monta os dados do relatório mensal dos sócios.
    Retorna dict padronizado: {'relatorio': ...}
    """
    empresa = Empresa.objects.get(id=empresa_id)
    competencia = datetime.strptime(mes_ano, "%Y-%m")

    socios = list(Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name'))
    socio_selecionado = None
    if socio_id:
        socio_selecionado = next((s for s in socios if s.id == int(socio_id)), None)
    if not socio_selecionado and socios:
        socio_selecionado = socios[0]

    # Despesas sem rateio
    despesas_sem_rateio = DespesaSocio.objects.filter(
        socio=socio_selecionado,
        item_despesa__grupo_despesa__empresa=empresa,
        data__year=competencia.year,
        data__month=competencia.month
    ).select_related('item_despesa__grupo_despesa')

    lista_despesas_sem_rateio = []
    for despesa in despesas_sem_rateio:
        lista_despesas_sem_rateio.append({
            'id': despesa.id,
            'data': despesa.data.strftime('%d/%m/%Y'),
            'grupo': despesa.item_despesa.grupo_despesa.descricao,
            'descricao': despesa.item_despesa.descricao,
            'valor': float(despesa.valor),
        })

    # Despesas com rateio
    despesas_com_rateio = DespesaRateada.objects.filter(
        item_despesa__grupo_despesa__empresa=empresa,
        data__year=competencia.year,
        data__month=competencia.month
    ).select_related('item_despesa__grupo_despesa')

    lista_despesas_com_rateio = []
    for despesa in despesas_com_rateio:
        rateio = None
        for config in despesa.obter_configuracao_rateio():
            if config.socio_id == socio_selecionado.id:
                rateio = config
                break
        from decimal import Decimal
        percentual = Decimal(rateio.percentual_rateio) if rateio else Decimal('0')
        valor_socio = despesa.valor * (percentual / Decimal('100')) if rateio else Decimal('0')
        lista_despesas_com_rateio.append({
            'id': despesa.id,
            'data': despesa.data.strftime('%d/%m/%Y'),
            'grupo': despesa.item_despesa.grupo_despesa.descricao,
            'descricao': despesa.item_despesa.descricao,
            'valor_total': float(despesa.valor),
            'rateio_percentual': float(percentual),
            'valor_socio': float(valor_socio),
        })

    # Totais padronizados: despesa_sem_rateio e despesa_com_rateio
    despesa_sem_rateio = sum(d['valor'] for d in lista_despesas_sem_rateio)
    despesa_com_rateio = sum(d['valor_socio'] for d in lista_despesas_com_rateio)

    # Notas fiscais do sócio no mês
    notas_fiscais_qs = NotaFiscal.objects.filter(
        rateios_medicos__medico=socio_selecionado,
        empresa_destinataria=empresa,
        dtEmissao__year=competencia.year,
        dtEmissao__month=competencia.month
    )

    notas_fiscais = []
    total_notas_bruto = 0
    total_iss = 0
    total_pis = 0
    total_cofins = 0
    total_irpj = 0
    total_csll = 0
    total_notas_liquido = 0

    for nf in notas_fiscais_qs:
        nf.calcular_impostos()  # Atualiza campos de impostos no modelo
        # Buscar o rateio do sócio para esta nota
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            notas_fiscais.append({
                'id': nf.id,
                'numero': getattr(nf, 'numero', ''),
                'tp_aliquota': nf.get_tipo_servico_display(),
                'tomador': nf.tomador,
                'valor_bruto': float(rateio.valor_bruto_medico),
                'valor_liquido': float(rateio.valor_liquido_medico),
                'iss': float(rateio.valor_iss_medico),
                'pis': float(rateio.valor_pis_medico),
                'cofins': float(rateio.valor_cofins_medico),
                'irpj': float(rateio.valor_ir_medico),
                'csll': float(rateio.valor_csll_medico),
                'data_emissao': nf.dtEmissao.strftime('%d/%m/%Y'),
                'data_recebimento': nf.dtRecebimento.strftime('%d/%m/%Y') if nf.dtRecebimento else '',
                'fornecedor': nf.empresa_destinataria.nome if hasattr(nf.empresa_destinataria, 'nome') else str(nf.empresa_destinataria),
            })
            total_notas_bruto += float(rateio.valor_bruto_medico or 0)
            total_iss += float(rateio.valor_iss_medico or 0)
            total_pis += float(rateio.valor_pis_medico or 0)
            total_cofins += float(rateio.valor_cofins_medico or 0)
            total_irpj += float(rateio.valor_ir_medico or 0)
            total_csll += float(rateio.valor_csll_medico or 0)
            total_notas_liquido += float(rateio.valor_liquido_medico or 0)

    total_notas_emitidas_mes = len(notas_fiscais)


    # Receita bruta e líquida do sócio
    receita_bruta_recebida = total_notas_bruto
    receita_liquida = total_notas_liquido

    # Impostos agregados
    impostos_total = total_iss + total_pis + total_cofins + total_irpj + total_csll

    despesas_total = despesa_sem_rateio + despesa_com_rateio
    saldo_apurado = receita_liquida - despesas_total
    # Cálculo do saldo das movimentações financeiras do sócio no mês
    movimentacoes_financeiras_qs = Financeiro.objects.filter(
        socio=socio_selecionado,
        data_movimentacao__year=competencia.year,
        data_movimentacao__month=competencia.month
    )
    saldo_movimentacao_financeira = float(sum(m.valor for m in movimentacoes_financeiras_qs))
    movimentacoes_financeiras = [
        {
            'id': m.id,
            'data': m.data_movimentacao.strftime('%d/%m/%Y'),
            'descricao': str(m.descricao_movimentacao_financeira),
            'valor': float(m.valor),
        }
        for m in movimentacoes_financeiras_qs
    ]
    saldo_a_transferir = saldo_apurado + saldo_movimentacao_financeira

    relatorio_obj, _ = RelatorioMensalSocio.objects.update_or_create(
        empresa=empresa,
        socio=socio_selecionado,
        competencia=competencia,
        defaults={
            'data_geracao': datetime.now(),
            'total_despesas_sem_rateio': despesa_sem_rateio,
            'total_despesas_com_rateio': despesa_com_rateio,
            'despesas_total': despesas_total,
            'despesa_sem_rateio': despesa_sem_rateio,
            'despesa_com_rateio': despesa_com_rateio,
            'despesa_geral': despesa_sem_rateio + despesa_com_rateio,
            'receita_bruta_recebida': receita_bruta_recebida,
            'receita_liquida': receita_liquida,
            'impostos_total': impostos_total,
            'total_iss': total_iss,
            'total_pis': total_pis,
            'total_cofins': total_cofins,
            'total_irpj': total_irpj,
            'total_csll': total_csll,
            'total_notas_bruto': total_notas_bruto,
            'total_notas_liquido': total_notas_liquido,
            'total_notas_emitidas_mes': total_notas_emitidas_mes,
            'saldo_apurado': saldo_apurado,
            'saldo_movimentacao_financeira': saldo_movimentacao_financeira,
            'saldo_a_transferir': saldo_a_transferir,
            'lista_despesas_sem_rateio': lista_despesas_sem_rateio,
            'lista_despesas_com_rateio': lista_despesas_com_rateio,
            'lista_notas_fiscais': notas_fiscais,
            'lista_movimentacoes_financeiras': movimentacoes_financeiras,
        }
    )
    relatorio_obj.save()  # Garantir persistência explícita
    return {'relatorio': relatorio_obj}


def montar_relatorio_issqn(empresa_id, mes_ano):
    """
    Monta os dados do relatório de apuração de ISSQN.
    Retorna dict padronizado: {'relatorio': ...}
    """
    return {'relatorio': {}}


def montar_relatorio_outros(empresa_id, mes_ano):
    """
    Monta os dados de outros relatórios de apuração.
    Retorna dict padronizado: {'relatorio': ...}
    """
    return {'relatorio': {}}
