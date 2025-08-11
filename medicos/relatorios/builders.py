# Imports necessários
from medicos.models.base import Empresa, Socio
from medicos.models.despesas import DespesaSocio, DespesaRateada
from medicos.models.fiscal import NotaFiscal, Aliquotas
from medicos.models.financeiro import Financeiro
from medicos.models.relatorios import RelatorioMensalSocio
from datetime import datetime




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
    # Para o cálculo de adicional de IR: considera data de emissão (conforme documentação)
    notas_fiscais_emissao_qs = NotaFiscal.objects.filter(
        rateios_medicos__medico=socio_selecionado,
        empresa_destinataria=empresa,
        dtEmissao__year=competencia.year,
        dtEmissao__month=competencia.month
    )
    
    # Para a tabela "Notas Fiscais Recebidas no Mês": considera data de recebimento
    notas_fiscais_qs = NotaFiscal.objects.filter(
        rateios_medicos__medico=socio_selecionado,
        empresa_destinataria=empresa,
        dtRecebimento__year=competencia.year,
        dtRecebimento__month=competencia.month,
        dtRecebimento__isnull=False  # Apenas notas que foram recebidas
    )

    # Notas fiscais da empresa no mês (para receita bruta total da empresa)
    notas_empresa_qs = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtEmissao__year=competencia.year,
        dtEmissao__month=competencia.month
    )

    total_notas_bruto_empresa = sum(float(nf.val_bruto or 0) for nf in notas_empresa_qs)
    
    # Buscar a alíquota da empresa para obter o valor base correto
    try:
        aliquota = Aliquotas.objects.filter(empresa=empresa).first()
        if aliquota and hasattr(aliquota, 'IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL'):
            valor_base_adicional = float(aliquota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL)
            aliquota_adicional = float(aliquota.IRPJ_ADICIONAL) / 100
        else:
            # Se não encontrar alíquota, não calcula adicional
            valor_base_adicional = total_notas_bruto_empresa + 1  # Força adicional = 0
            aliquota_adicional = 0
    except:
        # Em caso de erro, não calcula adicional
        valor_base_adicional = total_notas_bruto_empresa + 1  # Força adicional = 0
        aliquota_adicional = 0
    
    # Cálculo do valor total do adicional a ser rateado (adicional IRPJ)
    excedente_adicional = max(total_notas_bruto_empresa - valor_base_adicional, 0)
    valor_adicional_rateio = excedente_adicional * aliquota_adicional
    # Participação do sócio na receita bruta da empresa (para cálculo de adicional de IR)
    # Usar notas por data de emissão conforme documentação - deve somar apenas a parte do sócio
    receita_bruta_socio = 0
    for nf in notas_fiscais_emissao_qs:
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            receita_bruta_socio += float(rateio.valor_bruto_medico)
    
    participacao_socio = receita_bruta_socio / total_notas_bruto_empresa if total_notas_bruto_empresa > 0 else 0
    valor_adicional_socio = valor_adicional_rateio * participacao_socio if valor_adicional_rateio > 0 else 0
    
    # Processar notas fiscais do sócio para exibição
    notas_fiscais = []
    total_iss_socio = 0
    total_pis_socio = 0
    total_cofins_socio = 0
    total_irpj_socio = 0
    total_csll_socio = 0
    total_notas_liquido_socio = 0
    
    # Separar faturamento por tipo de serviço
    faturamento_consultas = 0
    faturamento_plantao = 0  
    faturamento_outros = 0

    debug_ir_adicional_espelho = []
    for nf in notas_fiscais_qs:
        nf.calcular_impostos()  # Atualiza campos de impostos no modelo
        # Buscar o rateio do sócio para esta nota
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            valor_bruto_rateio = float(rateio.valor_bruto_medico)
            valor_bruto_total_nf = float(nf.val_bruto or 0)
            
            # Classificar por tipo de serviço (usando valor bruto total da nota fiscal)
            if nf.tipo_servico == NotaFiscal.TIPO_SERVICO_CONSULTAS:
                faturamento_consultas += valor_bruto_total_nf
            elif 'plantão' in nf.descricao_servicos.lower() or 'plantao' in nf.descricao_servicos.lower():
                faturamento_plantao += valor_bruto_total_nf
            else:
                faturamento_outros += valor_bruto_total_nf
            
            # O cálculo detalhado do adicional de IR para o sócio foi desfeito; manter apenas o necessário para o relatório.
            notas_fiscais.append({
                'id': nf.id,
                'numero': getattr(nf, 'numero', ''),
                'tp_aliquota': nf.get_tipo_servico_display(),
                'tomador': nf.tomador,
                'valor_bruto': valor_bruto_total_nf,  # Valor bruto total da nota fiscal
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
            # Acumular totais do sócio
            total_iss_socio += float(rateio.valor_iss_medico or 0)
            total_pis_socio += float(rateio.valor_pis_medico or 0)
            total_cofins_socio += float(rateio.valor_cofins_medico or 0)
            total_irpj_socio += float(rateio.valor_ir_medico or 0)
            total_csll_socio += float(rateio.valor_csll_medico or 0)
            total_notas_liquido_socio += float(rateio.valor_liquido_medico or 0)


    # Totais dos campos das notas fiscais do sócio (para o template)
    total_nf_valor_bruto = sum(float(nf['valor_bruto'] or 0) for nf in notas_fiscais)
    total_nf_iss = sum(float(nf['iss'] or 0) for nf in notas_fiscais)
    total_nf_pis = sum(float(nf['pis'] or 0) for nf in notas_fiscais)
    total_nf_cofins = sum(float(nf['cofins'] or 0) for nf in notas_fiscais)
    total_nf_irpj = sum(float(nf['irpj'] or 0) for nf in notas_fiscais)
    total_nf_csll = sum(float(nf['csll'] or 0) for nf in notas_fiscais)
    total_nf_valor_liquido = sum(float(nf['valor_liquido'] or 0) for nf in notas_fiscais)

    # Total notas emitidas no mês: deve considerar todas as notas fiscais com data de emissão no mês de competência
    # Somar todas as notas emitidas do sócio no mês (valor total da nota fiscal)
    total_notas_emitidas_mes = sum(float(nf.val_bruto or 0) for nf in notas_fiscais_emissao_qs)

    # Receita bruta e líquida do sócio
    # receita_bruta_recebida deve considerar o valor total bruto de todas as notas recebidas pelo sócio no mês
    # (valor total das notas fiscais, não apenas a parte rateada)
    receita_bruta_recebida = sum(float(nf.val_bruto or 0) for nf in notas_fiscais_qs)
    
    receita_liquida = total_notas_liquido_socio

    # Impostos agregados do sócio
    impostos_total = total_iss_socio + total_pis_socio + total_cofins_socio + total_irpj_socio + total_csll_socio

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
            'total_iss': total_iss_socio,
            'total_pis': total_pis_socio,
            'total_cofins': total_cofins_socio,
            'total_irpj': total_irpj_socio,
            'total_irpj_adicional': valor_adicional_socio,
            'total_csll': total_csll_socio,
            'total_notas_bruto': total_notas_bruto_empresa,  # Receita bruta total da empresa
            'total_notas_liquido': total_notas_liquido_socio,
            'total_notas_emitidas_mes': total_notas_emitidas_mes,
            # Totais das notas fiscais do sócio (para linha de totais da tabela)
            'total_nf_valor_bruto': total_nf_valor_bruto,
            'total_nf_iss': total_nf_iss,
            'total_nf_pis': total_nf_pis,
            'total_nf_cofins': total_nf_cofins,
            'total_nf_irpj': total_nf_irpj,
            'total_nf_csll': total_nf_csll,
            'total_nf_valor_liquido': total_nf_valor_liquido,
            'faturamento_consultas': faturamento_consultas,
            'faturamento_plantao': faturamento_plantao,
            'faturamento_outros': faturamento_outros,
            'saldo_apurado': saldo_apurado,
            'saldo_movimentacao_financeira': saldo_movimentacao_financeira,
            'saldo_a_transferir': saldo_a_transferir,
            'lista_despesas_sem_rateio': lista_despesas_sem_rateio,
            'lista_despesas_com_rateio': lista_despesas_com_rateio,
            'lista_notas_fiscais': notas_fiscais,
            'lista_movimentacoes_financeiras': movimentacoes_financeiras,
            'debug_ir_adicional': debug_ir_adicional_espelho,
        }
    )
    relatorio_obj.save()  # Garantir persistência explícita
    # Adicionar valor_adicional_rateio ao dicionário de contexto do template
    contexto = {'relatorio': relatorio_obj}
    contexto['valor_adicional_rateio'] = valor_adicional_rateio
    contexto['participacao_socio'] = participacao_socio
    contexto['valor_adicional_socio'] = valor_adicional_socio
    contexto['receita_bruta_socio'] = receita_bruta_socio
    return contexto


def montar_relatorio_issqn(empresa_id, mes_ano):
    """
    Monta os dados do relatório de apuração de ISSQN.
    Retorna dict padronizado: {'linhas': [...], 'totais': {...}}
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    """
    empresa = Empresa.objects.get(id=empresa_id)
    ano = int(mes_ano[:4])
    linhas = []
    total_iss = 0
    for mes in range(1, 13):
        notas_mes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month=mes
        )
        valor_bruto = sum(float(nf.val_bruto or 0) for nf in notas_mes)
        valor_iss = sum(float(nf.val_ISS or 0) for nf in notas_mes)
        total_iss += valor_iss
        linhas.append({
            'competencia': f'{mes:02d}/{ano}',
            'valor_bruto': valor_bruto,
            'valor_iss': valor_iss,
        })
    return {
        'linhas': linhas,
        'totais': {
            'total_iss': total_iss,
        }
    }


def montar_relatorio_outros(empresa_id, mes_ano):
    """
    Monta os dados de outros relatórios de apuração.
    Retorna dict padronizado: {'relatorio': ...}
    """
    return {'relatorio': {}}


def montar_relatorio_issqn(empresa_id, mes_ano):
    """
    Monta os dados do relatório de apuração de ISSQN.
    Retorna dict padronizado: {'linhas': [...], 'totais': {...}}
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    """
    from medicos.models.fiscal import NotaFiscal
    empresa = Empresa.objects.get(id=empresa_id)
    ano = int(mes_ano[:4])
    linhas = []
    total_iss = 0
    for mes in range(1, 13):
        notas_mes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month=mes
        )
        valor_bruto = sum(float(nf.val_bruto or 0) for nf in notas_mes)
        valor_iss = sum(float(nf.val_ISS or 0) for nf in notas_mes)
        total_iss += valor_iss
        linhas.append({
            'competencia': f'{mes:02d}/{ano}',
            'valor_bruto': valor_bruto,
            'valor_iss': valor_iss,
        })
    return {
        'linhas': linhas,
        'totais': {
            'total_iss': total_iss,
        }
    }


def montar_relatorio_outros(empresa_id, mes_ano):
    """
    Monta os dados de outros relatórios de apuração.
    Retorna dict padronizado: {'relatorio': ...}
    """
    return {'relatorio': {}}
