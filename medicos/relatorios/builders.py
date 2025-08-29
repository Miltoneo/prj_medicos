# Imports necessários
from medicos.models.base import Empresa, Socio, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.models.despesas import DespesaSocio, DespesaRateada
from medicos.models.fiscal import NotaFiscal, Aliquotas
from medicos.models.financeiro import Financeiro
from medicos.models.relatorios import RelatorioMensalSocio
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP




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
    # A base de cálculo do IR deve considerar tipos de serviços separadamente
    # CORREÇÃO: Usar notas EMITIDAS no mês conforme Lei 9.249/1995 (adicional sempre por emissão)
    try:
        aliquota = Aliquotas.objects.filter(empresa=empresa).first()
        if aliquota:
            # Separar notas EMITIDAS por tipo de serviço para cálculo correto da base
            total_consultas = 0
            total_outros = 0
            
            # CORREÇÃO: Usar todas as notas EMITIDAS da empresa no mês (adicional sempre por emissão)
            notas_emitidas_empresa = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=competencia.year,
                dtEmissao__month=competencia.month
            )
            
            for nf in notas_emitidas_empresa:
                if nf.tipo_servico == nf.TIPO_SERVICO_CONSULTAS:
                    total_consultas += float(nf.val_bruto or 0)
                else:  # TIPO_SERVICO_OUTROS
                    total_outros += float(nf.val_bruto or 0)
            
            # Calcular bases de cálculo separadas
            base_consultas = total_consultas * (float(aliquota.IRPJ_PRESUNCAO_CONSULTA) / 100)
            base_outros = total_outros * (float(aliquota.IRPJ_PRESUNCAO_OUTROS) / 100)
            base_calculo_ir = base_consultas + base_outros
            
            excedente_adicional = max(base_calculo_ir - valor_base_adicional, 0)
        else:
            total_consultas = 0
            total_outros = 0
            base_consultas = 0
            base_outros = 0
            base_calculo_ir = 0
            excedente_adicional = 0
    except Exception as e:
        total_consultas = 0
        total_outros = 0
        base_consultas = 0
        base_outros = 0
        base_calculo_ir = 0
        excedente_adicional = 0
    
    valor_adicional_rateio = excedente_adicional * aliquota_adicional
    
    # Receita bruta recebida do sócio no mês - usar notas por data de recebimento
    # para ser consistente com a tabela "Notas Fiscais Recebidas no Mês"
    receita_bruta_socio_recebida = 0
    for nf in notas_fiscais_qs:  # Usar notas por data de recebimento
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            receita_bruta_socio_recebida += float(rateio.valor_bruto_medico)
    
    # CORREÇÃO: Para o cálculo do adicional de IR, usar receita EMITIDA do sócio
    # para ser consistente com o cálculo do adicional (sempre por emissão)
    receita_bruta_socio_emitida = 0
    for nf in notas_fiscais_emissao_qs:  # Usar notas por data de emissão
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            receita_bruta_socio_emitida += float(rateio.valor_bruto_medico)
    
    # Calcular a participação do sócio na receita bruta da empresa (para adicional de IR)
    # Usar receita_bruta_socio_emitida para ser consistente com base do adicional (emissão)
    participacao_socio = receita_bruta_socio_emitida / total_notas_bruto_empresa if total_notas_bruto_empresa > 0 else 0
    valor_adicional_socio = valor_adicional_rateio * participacao_socio if valor_adicional_rateio > 0 else 0
    
    # Processar notas fiscais do sócio para exibição
    notas_fiscais = []
    total_iss_socio = 0
    total_pis_socio = 0
    total_cofins_socio = 0
    total_irpj_socio = 0
    total_csll_socio = 0
    total_outros_socio = 0
    total_notas_liquido_socio = 0
    
    # CORREÇÃO: Calcular impostos apurados seguindo as mesmas regras da Apuração de Impostos
    # Os impostos do sócio são calculados aplicando o rateio aos impostos "a pagar" da empresa
    # (calculados seguindo regime tributário), não usando valores individuais das notas fiscais
    
    # Obter alíquotas da empresa
    try:
        aliquota_obj = Aliquotas.objects.filter(
            empresa=empresa,
            data_vigencia_inicio__lte=f'{competencia.year}-12-31',
        ).order_by('-data_vigencia_inicio').first()
        
        if aliquota_obj:
            aliquota_pis = float(getattr(aliquota_obj, 'PIS', 0))
            aliquota_cofins = float(getattr(aliquota_obj, 'COFINS', 0))
            aliquota_csll = float(getattr(aliquota_obj, 'CSLL_ALIQUOTA', 0))
            aliquota_irpj = float(getattr(aliquota_obj, 'IRPJ_ALIQUOTA', 0))
            aliquota_iss = float(getattr(aliquota_obj, 'ISS', 0))
        else:
            aliquota_pis = aliquota_cofins = aliquota_csll = aliquota_irpj = aliquota_iss = 0
    except:
        aliquota_pis = aliquota_cofins = aliquota_csll = aliquota_irpj = aliquota_iss = 0
    
    # Calcular impostos a pagar do mês seguindo a mesma lógica da apuração
    
    # Base de cálculo: notas da empresa no mês (seguindo regime tributário)
    if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
        # Regime de competência: considera data de emissão
        notas_base_calculo = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=competencia.year,
            dtEmissao__month=competencia.month
        )
    else:
        # Regime de caixa: considera data de recebimento
        notas_base_calculo = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=competencia.year,
            dtRecebimento__month=competencia.month,
            dtRecebimento__isnull=False
        )
    
    base_calculo_empresa = sum(float(nf.val_bruto or 0) for nf in notas_base_calculo)
    
    # Imposto retido: sempre considera data de recebimento
    notas_retidas = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtRecebimento__year=competencia.year,
        dtRecebimento__month=competencia.month,
        dtRecebimento__isnull=False
    )
    
    # Calcular impostos devidos da empresa
    pis_devido = base_calculo_empresa * (aliquota_pis / 100) if aliquota_pis > 0 else 0
    cofins_devido = base_calculo_empresa * (aliquota_cofins / 100) if aliquota_cofins > 0 else 0
    
    # Para CSLL e IRPJ: aplicar presunções de lucro
    if aliquota_obj:
        presuncao_consultas = float(getattr(aliquota_obj, 'CSLL_PRESUNCAO_CONSULTA', 32)) / 100
        presuncao_outros = float(getattr(aliquota_obj, 'CSLL_PRESUNCAO_OUTROS', 8)) / 100
        
        # Separar por tipo de serviço
        receita_consultas = sum(float(nf.val_bruto or 0) for nf in notas_base_calculo if nf.tipo_servico == NotaFiscal.TIPO_SERVICO_CONSULTAS)
        receita_outros = sum(float(nf.val_bruto or 0) for nf in notas_base_calculo if nf.tipo_servico != NotaFiscal.TIPO_SERVICO_CONSULTAS)
        
        base_csll = (receita_consultas * presuncao_consultas) + (receita_outros * presuncao_outros)
        base_irpj = base_csll  # Mesma base para IRPJ e CSLL
        
        csll_devido = base_csll * (aliquota_csll / 100) if aliquota_csll > 0 else 0
        irpj_devido = base_irpj * (aliquota_irpj / 100) if aliquota_irpj > 0 else 0
    else:
        csll_devido = irpj_devido = 0
    
    # Para ISSQN: calcular valor devido (base * alíquota) - o ISS nas notas é apenas o valor retido
    iss_devido = base_calculo_empresa * (aliquota_iss / 100) if aliquota_iss > 0 else 0
    
    # Impostos retidos
    pis_retido = sum(float(nf.val_PIS or 0) for nf in notas_retidas)
    cofins_retido = sum(float(nf.val_COFINS or 0) for nf in notas_retidas) 
    csll_retido = sum(float(nf.val_CSLL or 0) for nf in notas_retidas)
    irpj_retido = sum(float(nf.val_IR or 0) for nf in notas_retidas)
    iss_retido = sum(float(nf.val_ISS or 0) for nf in notas_retidas)
    
    # Impostos a pagar da empresa
    pis_a_pagar = max(0, pis_devido - pis_retido)
    cofins_a_pagar = max(0, cofins_devido - cofins_retido)
    csll_a_pagar = max(0, csll_devido - csll_retido)
    irpj_a_pagar = max(0, irpj_devido - irpj_retido)
    iss_a_pagar = max(0, iss_devido - iss_retido)
    
    # Aplicar rateio do sócio aos impostos a pagar da empresa
    # Usar a mesma base de cálculo (seguindo regime tributário) para participação do sócio
    if base_calculo_empresa > 0:
        # Calcular receita do sócio seguindo o mesmo regime tributário usado para base de cálculo
        if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
            # Regime de competência: usar notas emitidas
            receita_socio_periodo = 0
            for nf in notas_base_calculo:
                rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
                if rateio:
                    receita_socio_periodo += float(rateio.valor_bruto_medico or 0)
        else:
            # Regime de caixa: usar notas recebidas (já calculado anteriormente)
            receita_socio_periodo = receita_bruta_socio_recebida
        
        participacao_socio_impostos = receita_socio_periodo / base_calculo_empresa
        
        # Impostos devidos do sócio (calculados sobre a base proporcional)
        total_pis_devido_socio = pis_devido * participacao_socio_impostos
        total_cofins_devido_socio = cofins_devido * participacao_socio_impostos  
        total_irpj_devido_socio = irpj_devido * participacao_socio_impostos
        total_csll_devido_socio = csll_devido * participacao_socio_impostos
        total_iss_devido_socio = iss_devido * participacao_socio_impostos
        
        # Impostos retidos do sócio (calculados com base nos valores reais das notas recebidas)
        # CORREÇÃO: Usar valores proporcionais dos rateios das notas recebidas no mês
        # Os impostos retidos devem considerar a data de recebimento da nota fiscal
        # conforme documentado em medicos/templates/relatorios/relatorio_mensal_socio.html
        notas_recebidas_socio = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=competencia.year,
            dtRecebimento__month=competencia.month,
            dtRecebimento__isnull=False,
            rateios_medicos__medico=socio_selecionado
        ).distinct()
        
        total_pis_retido_socio = 0
        total_cofins_retido_socio = 0
        total_irpj_retido_socio = 0
        total_csll_retido_socio = 0
        total_iss_retido_socio = 0
        
        for nf in notas_recebidas_socio:
            rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
            if rateio:
                # Usar valores proporcionais calculados automaticamente no modelo NotaFiscalRateioMedico
                total_pis_retido_socio += float(rateio.valor_pis_medico or 0)
                total_cofins_retido_socio += float(rateio.valor_cofins_medico or 0)
                total_irpj_retido_socio += float(rateio.valor_ir_medico or 0)
                total_csll_retido_socio += float(rateio.valor_csll_medico or 0)
                total_iss_retido_socio += float(rateio.valor_iss_medico or 0)
        
        # Impostos retidos do sócio já calculados acima
        # (total_*_retido_socio já estão definidos)
        
        # Impostos devidos do sócio já calculados acima  
        # (total_*_devido_socio já estão definidos)
        
        # Impostos a provisionar serão calculados no final: devido - retido
    else:
        total_pis_devido_socio = 0
        total_cofins_devido_socio = 0
        total_irpj_devido_socio = 0
        total_csll_devido_socio = 0
        total_iss_devido_socio = 0
        
        total_pis_retido_socio = 0
        total_cofins_retido_socio = 0
        total_irpj_retido_socio = 0
        total_csll_retido_socio = 0
        total_iss_retido_socio = 0
        
        # Impostos a provisionar serão calculados no final: devido - retido (todos serão 0)
    
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
            
            # Classificar por tipo de serviço (usando valor do rateio do sócio específico)
            if nf.tipo_servico == NotaFiscal.TIPO_SERVICO_CONSULTAS:
                faturamento_consultas += valor_bruto_rateio
            elif 'plantão' in nf.descricao_servicos.lower() or 'plantao' in nf.descricao_servicos.lower():
                faturamento_plantao += valor_bruto_rateio
            else:
                faturamento_outros += valor_bruto_rateio
            
            # O cálculo detalhado do adicional de IR para o sócio foi desfeito; manter apenas o necessário para o relatório.
            notas_fiscais.append({
                'id': nf.id,
                'numero': getattr(nf, 'numero', ''),
                'tp_aliquota': nf.get_tipo_servico_display(),
                'tomador': nf.tomador,
                'percentual_rateio': float(rateio.percentual_participacao),  # Percentual de rateio do sócio
                'valor_bruto': valor_bruto_rateio,  # Valor bruto rateado para o sócio
                'valor_liquido': float(rateio.valor_liquido_medico),
                'iss': float(rateio.valor_iss_medico),
                'pis': float(rateio.valor_pis_medico),
                'cofins': float(rateio.valor_cofins_medico),
                'irpj': float(rateio.valor_ir_medico),
                'csll': float(rateio.valor_csll_medico),
                'outros': float(rateio.valor_outros_medico),  # Usar propriedade padronizada do modelo
                'data_emissao': nf.dtEmissao.strftime('%d/%m/%Y'),
                'data_recebimento': nf.dtRecebimento.strftime('%d/%m/%Y') if nf.dtRecebimento else '',
            })
            # Acumular outros valores e valor líquido do sócio (mas não impostos - estes são calculados pela apuração)
            total_outros_socio += float(rateio.valor_outros_medico or 0)
            total_notas_liquido_socio += float(rateio.valor_liquido_medico or 0)


    # Totais dos campos das notas fiscais do sócio (para o template)
    total_nf_valor_bruto = sum(float(nf['valor_bruto'] or 0) for nf in notas_fiscais)
    total_nf_iss = sum(float(nf['iss'] or 0) for nf in notas_fiscais)
    total_nf_pis = sum(float(nf['pis'] or 0) for nf in notas_fiscais)
    total_nf_cofins = sum(float(nf['cofins'] or 0) for nf in notas_fiscais)
    total_nf_irpj = sum(float(nf['irpj'] or 0) for nf in notas_fiscais)
    total_nf_csll = sum(float(nf['csll'] or 0) for nf in notas_fiscais)
    total_nf_outros = sum(float(nf['outros'] or 0) for nf in notas_fiscais)
    total_nf_valor_liquido = sum(float(nf['valor_liquido'] or 0) for nf in notas_fiscais)

    # Processar notas fiscais emitidas no mês (por data de emissão)
    notas_fiscais_emitidas = []
    for nf in notas_fiscais_emissao_qs:
        nf.calcular_impostos()  # Atualiza campos de impostos no modelo
        # Buscar o rateio do sócio para esta nota
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            notas_fiscais_emitidas.append({
                'id': nf.id,
                'numero': getattr(nf, 'numero', ''),
                'tp_aliquota': nf.get_tipo_servico_display(),
                'tomador': nf.tomador,
                'percentual_rateio': float(rateio.percentual_participacao),  # Percentual de rateio do sócio
                'valor_bruto': float(rateio.valor_bruto_medico),  # Valor bruto rateado para o sócio
                'valor_liquido': float(rateio.valor_liquido_medico),
                'iss': float(rateio.valor_iss_medico),
                'pis': float(rateio.valor_pis_medico),
                'cofins': float(rateio.valor_cofins_medico),
                'irpj': float(rateio.valor_ir_medico),
                'csll': float(rateio.valor_csll_medico),
                'outros': float(rateio.valor_outros_medico),  # Usar propriedade padronizada do modelo
                'data_emissao': nf.dtEmissao.strftime('%d/%m/%Y'),
                'data_recebimento': nf.dtRecebimento.strftime('%d/%m/%Y') if nf.dtRecebimento else '',
            })

    # Totais dos campos das notas fiscais emitidas do sócio (para o template)
    total_nf_emitidas_valor_bruto = sum(float(nf['valor_bruto'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_iss = sum(float(nf['iss'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_pis = sum(float(nf['pis'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_cofins = sum(float(nf['cofins'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_irpj = sum(float(nf['irpj'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_csll = sum(float(nf['csll'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_outros = sum(float(nf['outros'] or 0) for nf in notas_fiscais_emitidas)
    total_nf_emitidas_valor_liquido = sum(float(nf['valor_liquido'] or 0) for nf in notas_fiscais_emitidas)

    # Total notas emitidas no mês: deve considerar apenas a parte rateada para o sócio específico
    # Somar apenas o valor rateado para o sócio de cada nota fiscal emitida no mês
    total_notas_emitidas_mes = 0
    for nf in notas_fiscais_emissao_qs:
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            total_notas_emitidas_mes += float(rateio.valor_bruto_medico or 0)

    # Receita bruta e líquida do sócio - usar apenas a parte do sócio calculada anteriormente
    receita_bruta_recebida = receita_bruta_socio_recebida  # Usar valor correto (parte do sócio)

    # CORREÇÃO: Imposto a provisionar deve ser calculado como (devido - retido)
    # Total dos impostos devidos do sócio (antes da dedução de impostos retidos)
    impostos_devido_total = total_iss_devido_socio + total_pis_devido_socio + total_cofins_devido_socio + total_irpj_devido_socio + total_csll_devido_socio + valor_adicional_socio
    
    # Total dos impostos retidos do sócio
    impostos_retido_total = total_iss_retido_socio + total_pis_retido_socio + total_cofins_retido_socio + total_irpj_retido_socio + total_csll_retido_socio
    
    # Imposto a provisionar = Imposto devido - Imposto retido (conforme fórmula c=a-b)
    impostos_total = impostos_devido_total - impostos_retido_total
    
    # Valores individuais de impostos a provisionar (também seguem a fórmula devido - retido)
    total_iss_socio = total_iss_devido_socio - total_iss_retido_socio
    total_pis_socio = total_pis_devido_socio - total_pis_retido_socio
    total_cofins_socio = total_cofins_devido_socio - total_cofins_retido_socio
    total_irpj_socio = total_irpj_devido_socio - total_irpj_retido_socio
    total_csll_socio = total_csll_devido_socio - total_csll_retido_socio
    
    # Receita líquida = Receita bruta recebida - Impostos devido (conforme fórmula r-a)
    receita_liquida = receita_bruta_recebida - impostos_devido_total

    # Buscar impostos provisionados do mês anterior
    if competencia.month == 1:
        mes_anterior = competencia.replace(year=competencia.year - 1, month=12, day=1)
    else:
        mes_anterior = competencia.replace(month=competencia.month - 1, day=1)
    
    try:
        relatorio_mes_anterior = RelatorioMensalSocio.objects.get(
            empresa=empresa,
            socio=socio_selecionado,
            competencia=mes_anterior
        )
        imposto_provisionado_mes_anterior = relatorio_mes_anterior.impostos_total or Decimal('0')
    except RelatorioMensalSocio.DoesNotExist:
        imposto_provisionado_mes_anterior = Decimal('0')

    despesas_total = despesa_sem_rateio + despesa_com_rateio
    saldo_apurado = receita_liquida - despesas_total
    # Cálculo do saldo das movimentações financeiras do sócio no mês
    movimentacoes_financeiras_qs = Financeiro.objects.filter(
        socio=socio_selecionado,
        data_movimentacao__year=competencia.year,
        data_movimentacao__month=competencia.month
    )
    saldo_movimentacao_financeira = float(sum(m.valor for m in movimentacoes_financeiras_qs))
    
    # Calcular total de receitas (movimentações de crédito)
    total_receitas = float(sum(m.valor for m in movimentacoes_financeiras_qs if m.valor > 0))
    print(f"DEBUG Builder: total_receitas calculado = {total_receitas}")
    print(f"DEBUG Builder: número de movimentações = {movimentacoes_financeiras_qs.count()}")
    print(f"DEBUG Builder: movimentações positivas = {[m.valor for m in movimentacoes_financeiras_qs if m.valor > 0]}")
    
    # Calcular total de despesas outros (movimentações de débito)
    total_despesas_outros = float(abs(sum(m.valor for m in movimentacoes_financeiras_qs if m.valor < 0)))
    print(f"DEBUG Builder: total_despesas_outros calculado = {total_despesas_outros}")
    print(f"DEBUG Builder: movimentações negativas = {[m.valor for m in movimentacoes_financeiras_qs if m.valor < 0]}")
    
    movimentacoes_financeiras = [
        {
            'id': m.id,
            'data': m.data_movimentacao.strftime('%d/%m/%Y'),
            'descricao': str(m.descricao_movimentacao_financeira),
            'valor': float(m.valor),
        }
        for m in movimentacoes_financeiras_qs
    ]
    
    # Corrigir o cálculo do saldo_a_transferir conforme estrutura do quadro "Receitas":
    # SALDO A TRANSFERIR = RECEITA LÍQUIDA (r-a) - DESPESAS (-) + SALDO DAS MOVIMENTAÇÕES FINANCEIRAS (+)
    despesa_geral = despesa_sem_rateio + despesa_com_rateio
    saldo_a_transferir = receita_liquida - despesa_geral + saldo_movimentacao_financeira
    print(f"DEBUG Builder: Novo cálculo saldo_a_transferir:")
    print(f"  receita_liquida: {receita_liquida}")
    print(f"  despesa_geral: {despesa_geral}")
    print(f"  saldo_movimentacao_financeira: {saldo_movimentacao_financeira}")
    print(f"  saldo_a_transferir: {saldo_a_transferir}")

    # Definir dados para salvar no modelo (apenas campos que existem)
    dados_modelo = {
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
        'impostos_devido_total': impostos_devido_total,
        'impostos_retido_total': impostos_retido_total,
        'total_iss': total_iss_socio,
        'total_pis': total_pis_socio,
        'total_cofins': total_cofins_socio,
        'total_irpj': total_irpj_socio,
        'total_irpj_adicional': valor_adicional_socio,
        'total_csll': total_csll_socio,
        'total_iss_devido': total_iss_devido_socio,
        'total_pis_devido': total_pis_devido_socio,
        'total_cofins_devido': total_cofins_devido_socio,
        'total_irpj_devido': total_irpj_devido_socio,
        'total_csll_devido': total_csll_devido_socio,
        'total_iss_retido': total_iss_retido_socio,
        'total_pis_retido': total_pis_retido_socio,
        'total_cofins_retido': total_cofins_retido_socio,
        'total_irpj_retido': total_irpj_retido_socio,
        'total_csll_retido': total_csll_retido_socio,
        'total_notas_bruto': total_notas_bruto_empresa,
        'total_notas_liquido': total_notas_liquido_socio,
        'total_notas_emitidas_mes': total_notas_emitidas_mes,
        'total_nf_valor_bruto': total_nf_valor_bruto,
        'total_nf_iss': total_nf_iss,
        'total_nf_pis': total_nf_pis,
        'total_nf_cofins': total_nf_cofins,
        'total_nf_irpj': total_nf_irpj,
        'total_nf_csll': total_nf_csll,
        'total_nf_outros': total_nf_outros,
        'total_nf_valor_liquido': total_nf_valor_liquido,
        'total_nf_emitidas_valor_bruto': total_nf_emitidas_valor_bruto,
        'total_nf_emitidas_iss': total_nf_emitidas_iss,
        'total_nf_emitidas_pis': total_nf_emitidas_pis,
        'total_nf_emitidas_cofins': total_nf_emitidas_cofins,
        'total_nf_emitidas_irpj': total_nf_emitidas_irpj,
        'total_nf_emitidas_csll': total_nf_emitidas_csll,
        'total_nf_emitidas_outros': total_nf_emitidas_outros,
        'total_nf_emitidas_valor_liquido': total_nf_emitidas_valor_liquido,
        'faturamento_consultas': faturamento_consultas,
        'faturamento_plantao': faturamento_plantao,
        'faturamento_outros': faturamento_outros,
        'saldo_apurado': saldo_apurado,
        'saldo_movimentacao_financeira': saldo_movimentacao_financeira,
        'saldo_a_transferir': saldo_a_transferir,
        'imposto_provisionado_mes_anterior': float(imposto_provisionado_mes_anterior),
        'lista_despesas_sem_rateio': lista_despesas_sem_rateio,
        'lista_despesas_com_rateio': lista_despesas_com_rateio,
        'lista_notas_fiscais': notas_fiscais,
        'lista_notas_fiscais_emitidas': notas_fiscais_emitidas,
        'lista_movimentacoes_financeiras': movimentacoes_financeiras,
        'debug_ir_adicional': debug_ir_adicional_espelho,
    }
    
    relatorio_obj, _ = RelatorioMensalSocio.objects.update_or_create(
        empresa=empresa,
        socio=socio_selecionado,
        competencia=competencia,
        defaults=dados_modelo
    )
    relatorio_obj.save()  # Garantir persistência explícita
    # Adicionar valor_adicional_rateio ao dicionário de contexto do template
    contexto = {'relatorio': relatorio_obj}
    contexto['valor_adicional_rateio'] = valor_adicional_rateio
    
    # Percentual garantido (0.00 a 100.00) - garantir que seja exibido corretamente
    if participacao_socio > 0:
        percentual = participacao_socio * 100
    else:
        percentual = 0.0
    contexto['participacao_socio_percentual'] = round(percentual, 2) if percentual else 0.0
    
    # Campos auxiliares utilizados no template
    contexto['receita_bruta_socio'] = receita_bruta_socio_emitida  # Usar notas emitidas para cálculo de adicional de IR
    
    # Adicionar total_receitas diretamente no contexto (campo não existe no modelo ainda)
    contexto['total_receitas'] = total_receitas
    
    # Adicionar total_despesas_outros diretamente no contexto (campo não existe no modelo ainda)
    contexto['total_despesas_outros'] = total_despesas_outros
    
    # Adicionar campos calculados que não estão no modelo
    contexto['base_consultas_medicas'] = total_consultas
    contexto['base_outros_servicos'] = total_outros
    contexto['base_calculo_consultas_ir'] = base_consultas
    contexto['base_calculo_outros_ir'] = base_outros
    contexto['base_calculo_ir_total'] = base_calculo_ir
    contexto['valor_base_adicional'] = valor_base_adicional
    contexto['excedente_adicional'] = excedente_adicional
    contexto['aliquota_adicional'] = aliquota_adicional * 100  # Converter para percentual
    
    return contexto


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
    from medicos.models.fiscal import NotaFiscal, Aliquotas
    empresa = Empresa.objects.get(id=empresa_id)
    ano = int(mes_ano[:4])
    linhas = []
    total_iss = 0
    total_imposto_retido_nf = 0
    
    # Obter alíquota ISS da empresa
    aliquota_obj = Aliquotas.objects.filter(
        empresa=empresa,
        data_vigencia_inicio__lte=f'{ano}-12-31',
    ).order_by('-data_vigencia_inicio').first()
    aliquota_iss = float(getattr(aliquota_obj, 'ISS', 0)) if aliquota_obj else 0
    
    for mes in range(1, 13):
        # Notas para base de cálculo considerando regime tributário da empresa
        if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
            # Regime de competência: considera data de emissão
            notas_mes = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=ano,
                dtEmissao__month=mes
            )
        else:
            # Regime de caixa: considera data de recebimento
            notas_mes = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False  # Só considera notas efetivamente recebidas
            )
        valor_bruto = sum(float(nf.val_bruto or 0) for nf in notas_mes)
        
        # Imposto devido: calculado sobre a base de cálculo (valor bruto)
        imposto_devido = valor_bruto * aliquota_iss / 100
        
        # Imposto retido: valor efetivamente retido nas notas fiscais
        # Para ISSQN, tanto cálculo quanto retenção seguem o mesmo regime
        imposto_retido_nf = sum(float(nf.val_ISS or 0) for nf in notas_mes)
        
        total_iss += imposto_devido
        total_imposto_retido_nf += imposto_retido_nf
        linhas.append({
            'competencia': f'{mes:02d}/{ano}',
            'valor_bruto': valor_bruto,
            'valor_iss': imposto_devido,  # Agora é o valor devido calculado
            'imposto_retido_nf': imposto_retido_nf,
            'aliquota': aliquota_iss,
        })
    return {
        'linhas': linhas,
        'totais': {
            'total_iss': total_iss,
            'total_imposto_retido_nf': total_imposto_retido_nf,
        }
    }


def montar_relatorio_outros(empresa_id, mes_ano):
    """
    Monta os dados de outros relatórios de apuração.
    Retorna dict padronizado: {'relatorio': ...}
    """
    return {'relatorio': {}}

def montar_relatorio_executivo_anual(empresa_id, ano=None):
    """
    Builder básico para relatório executivo anual.
    Esta função será sobrescrita pelo builder dedicado em builder_executivo.py
    """
    return {
        'ano_atual': ano or 2025,
        'notas_emitidas_mes': {},
        'total_emitidas': 0,
        'total_recebidas': 0,
    } 
