# Imports necessários
from medicos.models.base import Empresa, Socio, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
from medicos.models.fiscal import NotaFiscal, Aliquotas
from medicos.models.financeiro import Financeiro
from medicos.models.relatorios import RelatorioMensalSocio
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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


def montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=None, auto_lancar_impostos=False, 
                                 atualizar_lancamentos_existentes=True):
    """
    Monta os dados do relatório mensal dos sócios com lançamento automático opcional de impostos.
    
    Args:
        empresa_id: ID da empresa
        mes_ano: String no formato "YYYY-MM"
        socio_id: ID do sócio (opcional)
        auto_lancar_impostos: Se True, cria/atualiza lançamentos automáticos de impostos
        atualizar_lancamentos_existentes: Se True, atualiza lançamentos existentes (usado com auto_lancar_impostos)
    
    Retorna dict com:
        - relatorio: objeto RelatorioMensalSocio
        - resultado_lancamento_automatico: resultado do lançamento automático (se solicitado)
        - outros campos de contexto
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
        # Incluir nome do sócio e campos adicionais para exibição no template
        socio_nome = getattr(getattr(despesa, 'socio', None), 'pessoa', None)
        socio_display = socio_nome.name if socio_nome else str(getattr(despesa, 'socio', ''))
        lista_despesas_sem_rateio.append({
            'id': despesa.id,
            'data': despesa.data.strftime('%d/%m/%Y'),
            'socio': socio_display,
            'grupo': despesa.item_despesa.grupo_despesa.descricao,
            'descricao': despesa.item_despesa.descricao,
            # manter chave 'valor' para compatibilidade com cálculo existente
            'valor': float(despesa.valor),
            'valor_total': float(despesa.valor),
            'taxa_rateio': '-',  # despesas sem rateio não têm taxa aplicada
            'valor_apropriado': float(despesa.valor),
        })

    # Despesas com rateio
    despesas_com_rateio = DespesaRateada.objects.filter(
        item_despesa__grupo_despesa__empresa=empresa,
        data__year=competencia.year,
        data__month=competencia.month
    ).select_related('item_despesa__grupo_despesa')

    lista_despesas_com_rateio = []
    # (debug prints removed)
    for despesa in despesas_com_rateio:
        # Garantir que exista um rateio para este item/sócio/mês (pode criar ou copiar do mês anterior)
        try:
            rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                despesa.item_despesa,
                socio_selecionado,
                despesa.data
            )
        except Exception:
            # Em caso de erro inesperado, pular esta despesa e logar para análise
            print(f"[ERROR] Falha ao obter/criar rateio para despesa {despesa.id} e socio {socio_selecionado.id}")
            continue

        percentual = Decimal(rateio.percentual_rateio or 0)
        valor_socio = despesa.valor * (percentual / Decimal('100')) if percentual > 0 else Decimal('0')

        if percentual == 0:
            # rateio zerado para este sócio — sem log em produção
            pass

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
    # EXCLUDINDO notas fiscais canceladas
    notas_fiscais_emissao_qs = NotaFiscal.objects.filter(
        rateios_medicos__medico=socio_selecionado,
        empresa_destinataria=empresa,
        dtEmissao__year=competencia.year,
        dtEmissao__month=competencia.month
    ).exclude(status_recebimento='cancelado')
    
    # Para a tabela "Notas Fiscais Recebidas no Mês": considera data de recebimento
    # EXCLUDINDO notas fiscais canceladas
    notas_fiscais_qs = NotaFiscal.objects.filter(
        rateios_medicos__medico=socio_selecionado,
        empresa_destinataria=empresa,
        dtRecebimento__year=competencia.year,
        dtRecebimento__month=competencia.month,
        dtRecebimento__isnull=False  # Apenas notas que foram recebidas
    ).exclude(status_recebimento='cancelado')

    # Notas fiscais da empresa no mês (para receita bruta total da empresa)
    # EXCLUDINDO notas fiscais canceladas
    notas_empresa_qs = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtEmissao__year=competencia.year,
        dtEmissao__month=competencia.month
    ).exclude(status_recebimento='cancelado')

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
    
    # CORREÇÃO: Adicional de IR TRIMESTRAL - Calcular com base trimestral
    # Lei 9.249/1995, Art. 3º, §1º - limite trimestral de R$ 60.000,00
    try:
        aliquota = Aliquotas.objects.filter(empresa=empresa).first()
        if aliquota:
            # Determinar o trimestre atual
            trimestre = (competencia.month - 1) // 3 + 1
            meses_trimestre = {
                1: [1, 2, 3],    # T1: Jan, Fev, Mar
                2: [4, 5, 6],    # T2: Abr, Mai, Jun
                3: [7, 8, 9],    # T3: Jul, Ago, Set
                4: [10, 11, 12]  # T4: Out, Nov, Dez
            }
            
            # Calcular base trimestral (soma dos 3 meses do trimestre)
            total_consultas_trimestre = 0
            total_outros_trimestre = 0
            
            for mes in meses_trimestre[trimestre]:
                notas_mes = NotaFiscal.objects.filter(
                    empresa_destinataria=empresa,
                    dtEmissao__year=competencia.year,
                    dtEmissao__month=mes
                ).exclude(status_recebimento='cancelado')
                
                for nf in notas_mes:
                    if nf.tipo_servico == nf.TIPO_SERVICO_CONSULTAS:
                        total_consultas_trimestre += float(nf.val_bruto or 0)
                    else:  # TIPO_SERVICO_OUTROS
                        total_outros_trimestre += float(nf.val_bruto or 0)
            
            # Calcular base de cálculo trimestral
            base_consultas_trimestre = total_consultas_trimestre * (float(aliquota.IRPJ_PRESUNCAO_CONSULTA) / 100)
            base_outros_trimestre = total_outros_trimestre * (float(aliquota.IRPJ_PRESUNCAO_OUTROS) / 100)
            base_calculo_ir_trimestre = base_consultas_trimestre + base_outros_trimestre
            
            # Aplicar limite trimestral de R$ 60.000,00
            limite_trimestral = 60000.00  # Lei 9.249/1995, Art. 3º, §1º
            excedente_adicional_trimestre = max(base_calculo_ir_trimestre - limite_trimestral, 0)
            
            # Para exibição no relatório mensal, usar dados do mês atual
            total_consultas = 0
            total_outros = 0
            
            notas_emitidas_empresa = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=competencia.year,
                dtEmissao__month=competencia.month
            ).exclude(status_recebimento='cancelado')
            
            for nf in notas_emitidas_empresa:
                if nf.tipo_servico == nf.TIPO_SERVICO_CONSULTAS:
                    total_consultas += float(nf.val_bruto or 0)
                else:  # TIPO_SERVICO_OUTROS
                    total_outros += float(nf.val_bruto or 0)
            
            base_consultas = total_consultas * (float(aliquota.IRPJ_PRESUNCAO_CONSULTA) / 100)
            base_outros = total_outros * (float(aliquota.IRPJ_PRESUNCAO_OUTROS) / 100)
            base_calculo_ir = base_consultas + base_outros
            
        else:
            total_consultas = 0
            total_outros = 0
            base_consultas = 0
            base_outros = 0
            base_calculo_ir = 0
            excedente_adicional_trimestre = 0
    except Exception as e:
        total_consultas = 0
        total_outros = 0
        base_consultas = 0
        base_outros = 0
        base_calculo_ir = 0
        excedente_adicional_trimestre = 0
    
    # ADICIONAL DE IR TRIMESTRAL: Calcular valor total da empresa para rateio entre sócios
    # Alíquota do adicional é sempre 10% conforme Lei 9.249/1995, Art. 3º, §1º
    aliquota_adicional_fixa = 0.10  # 10% fixo por lei
    adicional_ir_trimestral_empresa = excedente_adicional_trimestre * aliquota_adicional_fixa
    
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
    # Para adicional trimestral, usar receita trimestral da empresa
    total_receita_trimestre = total_consultas_trimestre + total_outros_trimestre if 'total_consultas_trimestre' in locals() else total_notas_bruto_empresa
    
    # Calcular receita trimestral do sócio para participação correta
    receita_bruta_socio_trimestre = 0
    if 'meses_trimestre' in locals() and 'trimestre' in locals():
        for mes in meses_trimestre[trimestre]:
            notas_mes_socio = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=competencia.year,
                dtEmissao__month=mes
            ).exclude(status_recebimento='cancelado')
            
            for nf in notas_mes_socio:
                rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
                if rateio:
                    receita_bruta_socio_trimestre += float(rateio.valor_bruto_medico)
    
    participacao_socio = receita_bruta_socio_trimestre / total_receita_trimestre if total_receita_trimestre > 0 else 0
    
    # ADICIONAL DE IR TRIMESTRAL: Calcular a parte proporcional do sócio no adicional de IR trimestral
    # REGRA: Só aparece nos meses de fechamento de trimestre (3, 6, 9, 12)
    if competencia.month in [3, 6, 9, 12]:
        adicional_ir_trimestral_socio = adicional_ir_trimestral_empresa * participacao_socio if adicional_ir_trimestral_empresa > 0 else 0
    else:
        adicional_ir_trimestral_socio = 0
    
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
    # EXCLUDINDO notas fiscais canceladas
    if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
        # Regime de competência: considera data de emissão
        notas_base_calculo = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=competencia.year,
            dtEmissao__month=competencia.month
        ).exclude(status_recebimento='cancelado')
    else:
        # Regime de caixa: considera data de recebimento
        notas_base_calculo = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=competencia.year,
            dtRecebimento__month=competencia.month,
            dtRecebimento__isnull=False
        ).exclude(status_recebimento='cancelado')
    
    base_calculo_empresa = sum(float(nf.val_bruto or 0) for nf in notas_base_calculo)
    
    # Calcular bases de consultas e outros serviços do sócio seguindo regime tributário
    base_consultas_socio_regime = 0
    base_outros_socio_regime = 0
    
    # Usar o mesmo queryset usado para base de cálculo dos impostos (notas_base_calculo)
    # que já respeita o regime tributário da empresa
    for nf in notas_base_calculo:
        rateio = nf.rateios_medicos.filter(medico=socio_selecionado).first()
        if rateio:
            valor_bruto_rateio = float(rateio.valor_bruto_medico or 0)
            # Classificar por tipo de serviço
            if nf.tipo_servico == NotaFiscal.TIPO_SERVICO_CONSULTAS:
                base_consultas_socio_regime += valor_bruto_rateio
            else:
                base_outros_socio_regime += valor_bruto_rateio
    
    # Imposto retido: sempre considera data de recebimento
    # EXCLUDINDO notas fiscais canceladas
    notas_retidas = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtRecebimento__year=competencia.year,
        dtRecebimento__month=competencia.month,
        dtRecebimento__isnull=False
    ).exclude(status_recebimento='cancelado')
    
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
        # EXCLUDINDO notas fiscais canceladas
        notas_recebidas_socio = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=competencia.year,
            dtRecebimento__month=competencia.month,
            dtRecebimento__isnull=False,
            rateios_medicos__medico=socio_selecionado
        ).exclude(status_recebimento='cancelado').distinct()
        
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
    # Total dos impostos devidos do sócio (antes da dedução de impostos retidos) - SEM incluir adicional de IR
    impostos_devido_total = total_iss_devido_socio + total_pis_devido_socio + total_cofins_devido_socio + total_irpj_devido_socio + total_csll_devido_socio
    
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
    
    # RECEITA LÍQUIDA: Fórmula corrigida conforme solicitação do usuário
    # (=) RECEITA LÍQUIDA = receita bruta - impostos_devido_total - adicional de IR trimestral
    receita_liquida = receita_bruta_recebida - impostos_devido_total - adicional_ir_trimestral_socio

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

    # Calcular despesas provisionadas (despesas apropriadas do mês seguinte)
    mes_seguinte = competencia + relativedelta(months=1)
    
    # Despesas sem rateio do mês seguinte
    despesas_sem_rateio_mes_seguinte = DespesaSocio.objects.filter(
        item_despesa__grupo_despesa__empresa=empresa,
        socio=socio_selecionado,
        data__year=mes_seguinte.year,
        data__month=mes_seguinte.month
    ).select_related('item_despesa__grupo_despesa')
    
    total_despesas_sem_rateio_mes_seguinte = sum(float(d.valor) for d in despesas_sem_rateio_mes_seguinte)
    
    # Despesas com rateio do mês seguinte
    despesas_com_rateio_mes_seguinte = DespesaRateada.objects.filter(
        item_despesa__grupo_despesa__empresa=empresa,
        data__year=mes_seguinte.year,
        data__month=mes_seguinte.month
    ).select_related('item_despesa__grupo_despesa')
    
    total_despesas_com_rateio_mes_seguinte = 0
    for despesa in despesas_com_rateio_mes_seguinte:
        try:
            rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                despesa.item_despesa,
                socio_selecionado,
                despesa.data
            )
            percentual = Decimal(rateio.percentual_rateio or 0)
            valor_socio = despesa.valor * (percentual / Decimal('100')) if percentual > 0 else Decimal('0')
            total_despesas_com_rateio_mes_seguinte += float(valor_socio)
        except Exception:
            continue
    
    # Total de despesas provisionadas
    despesas_provisionadas = total_despesas_sem_rateio_mes_seguinte + total_despesas_com_rateio_mes_seguinte
    
    print(f"DEBUG Builder: Despesas provisionadas calculadas:")
    print(f"  Mês seguinte: {mes_seguinte.strftime('%Y-%m')}")
    print(f"  Despesas sem rateio: {total_despesas_sem_rateio_mes_seguinte}")
    print(f"  Despesas com rateio: {total_despesas_com_rateio_mes_seguinte}")
    print(f"  Total despesas provisionadas: {despesas_provisionadas}")

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
        'total_irpj_adicional': adicional_ir_trimestral_socio,  # ADICIONAL DE IR TRIMESTRAL do sócio
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
    
    # Adicionar adicional_ir_trimestral_empresa ao dicionário de contexto do template
    contexto = {'relatorio': relatorio_obj}
    contexto['adicional_ir_trimestral_empresa'] = adicional_ir_trimestral_empresa
    
    # Campos auxiliares utilizados no template
    contexto['receita_bruta_socio'] = receita_bruta_socio_emitida  # Usar notas emitidas para cálculo de adicional de IR
    
    # Adicionar total_receitas diretamente no contexto (campo não existe no modelo ainda)
    contexto['total_receitas'] = total_receitas
    
    # Adicionar total_despesas_outros diretamente no contexto (campo não existe no modelo ainda)
    contexto['total_despesas_outros'] = total_despesas_outros
    
    # Adicionar despesas provisionadas ao contexto
    contexto['despesas_provisionadas'] = despesas_provisionadas
    
    # Adicionar campos calculados que não estão no modelo
    contexto['base_consultas_medicas'] = total_consultas
    contexto['base_outros_servicos'] = total_outros
    
    # Adicionar bases do sócio seguindo regime tributário
    contexto['base_consultas_socio_regime'] = base_consultas_socio_regime
    contexto['base_outros_socio_regime'] = base_outros_socio_regime
    
    # Adicionar alíquotas dos impostos para exibição no template
    contexto['aliquota_pis'] = aliquota_pis
    contexto['aliquota_cofins'] = aliquota_cofins
    contexto['aliquota_irpj'] = aliquota_irpj
    contexto['aliquota_csll'] = aliquota_csll
    contexto['aliquota_iss'] = aliquota_iss
    
    # Debug para verificar valores
    print(f"DEBUG Builder: base_consultas_socio_regime = {base_consultas_socio_regime}")
    print(f"DEBUG Builder: base_outros_socio_regime = {base_outros_socio_regime}")
    
    # Incluir listas diretamente no contexto para uso imediato pela view
    contexto['lista_despesas_sem_rateio'] = lista_despesas_sem_rateio
    contexto['lista_despesas_com_rateio'] = lista_despesas_com_rateio
    
    # Lançamento automático de impostos (se solicitado)
    if auto_lancar_impostos and socio_selecionado:
        try:
            from medicos.services.lancamento_impostos import LancamentoImpostosService
            
            # Usar valores diretos das variáveis calculadas (mais seguro que acessar o objeto persistido)
            valores_impostos = {
                'PIS': total_pis_socio,
                'COFINS': total_cofins_socio,
                'IRPJ': total_irpj_socio + adicional_ir_trimestral_socio,  # Incluir ADICIONAL DE IR TRIMESTRAL
                'CSLL': total_csll_socio,
                'ISSQN': total_iss_socio,
            }
            
            # Executar lançamento automático
            service = LancamentoImpostosService()
            resultado_lancamento = service.processar_impostos_automaticamente(
                empresa=empresa,
                socio=socio_selecionado,
                mes=competencia.month,
                ano=competencia.year,
                valores_impostos=valores_impostos,
                atualizar_existentes=atualizar_lancamentos_existentes
            )
            
            contexto['resultado_lancamento_automatico'] = resultado_lancamento
            
        except Exception as e:
            # Em caso de erro, incluir no contexto mas não interromper o relatório
            contexto['resultado_lancamento_automatico'] = {
                'success': False,
                'error': f'Erro no lançamento automático: {str(e)}'
            }
    
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
        # EXCLUDINDO notas fiscais canceladas de todos os cálculos
        if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
            # Regime de competência: considera data de emissão
            notas_mes = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtEmissao__year=ano,
                dtEmissao__month=mes
            ).exclude(status_recebimento='cancelado')
        else:
            # Regime de caixa: considera data de recebimento
            notas_mes = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False  # Só considera notas efetivamente recebidas
            ).exclude(status_recebimento='cancelado')
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


def processar_fechamento_mensal_conta_corrente(empresa_id, competencia):
    """
    Processa fechamento mensal da conta corrente para todos os sócios.
    Implementa padrão bancário de fechamento com persistência de saldos.
    
    Args:
        empresa_id: ID da empresa (multi-tenant)
        competencia: date object do primeiro dia do mês (ex: date(2025, 8, 1))
    
    Returns:
        dict: {'sucesso': bool, 'socios_processados': int, 'erros': list}
    
    Fonte: Práticas bancárias e padrões do projeto
    """
    from medicos.models.conta_corrente import MovimentacaoContaCorrente, SaldoMensalContaCorrente
    from medicos.models.base import Socio, Empresa
    from django.db import transaction
    from django.utils import timezone
    from datetime import date
    import calendar
    
    # Validações iniciais
    try:
        empresa = Empresa.objects.get(id=empresa_id)
    except Empresa.DoesNotExist:
        return {'sucesso': False, 'erros': [f'Empresa {empresa_id} não encontrada']}
    
    if not isinstance(competencia, date):
        return {'sucesso': False, 'erros': ['Competência deve ser um objeto date']}
    
    ano = competencia.year
    mes = competencia.month
    
    # Primeiro e último dia do mês
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
    
    # Determinar competência anterior
    if mes == 1:
        competencia_anterior = date(ano - 1, 12, 1)
    else:
        competencia_anterior = date(ano, mes - 1, 1)
    
    socios_processados = 0
    erros = []
    
    # Processar em transação atômica (padrão bancário)
    try:
        with transaction.atomic():
            # Buscar todos os sócios ativos da empresa
            socios = Socio.objects.filter(
                empresa_id=empresa_id,
                ativo=True
            ).order_by('pessoa__name')
            
            for socio in socios:
                try:
                    # 1. Buscar saldo anterior do mês passado
                    try:
                        saldo_mes_anterior = SaldoMensalContaCorrente.objects.get(
                            empresa_id=empresa_id,
                            socio=socio,
                            competencia=competencia_anterior,
                            fechado=True
                        )
                        saldo_anterior = saldo_mes_anterior.saldo_final
                    except SaldoMensalContaCorrente.DoesNotExist:
                        # Primeira vez: calcular acumulado até o mês anterior
                        movs_anteriores = MovimentacaoContaCorrente.objects.filter(
                            socio=socio,
                            data_movimentacao__lt=primeiro_dia
                        )
                        saldo_anterior = sum(mov.valor for mov in movs_anteriores)
                    
                    # 2. Buscar movimentações do mês atual
                    movs_mes_atual = MovimentacaoContaCorrente.objects.filter(
                        socio=socio,
                        data_movimentacao__range=[primeiro_dia, ultimo_dia]
                    )
                    
                    # 3. Calcular totais do período
                    total_creditos = sum(mov.valor for mov in movs_mes_atual if mov.valor > 0)
                    total_debitos = abs(sum(mov.valor for mov in movs_mes_atual if mov.valor < 0))
                    
                    # 4. Criar ou atualizar saldo mensal
                    saldo_mensal, created = SaldoMensalContaCorrente.objects.get_or_create(
                        empresa_id=empresa_id,
                        socio=socio,
                        competencia=primeiro_dia,
                        defaults={
                            'saldo_anterior': saldo_anterior,
                            'total_creditos': total_creditos,
                            'total_debitos': total_debitos,
                        }
                    )
                    
                    if not created:
                        # Atualizar registro existente
                        saldo_mensal.saldo_anterior = saldo_anterior
                        saldo_mensal.total_creditos = total_creditos
                        saldo_mensal.total_debitos = total_debitos
                    
                    # 5. Calcular saldo final e salvar
                    saldo_mensal.calcular_saldo_final()
                    saldo_mensal.save()
                    
                    socios_processados += 1
                    
                except Exception as e:
                    erros.append(f'Erro processando sócio {socio.pessoa.name}: {str(e)}')
            
            # Se chegou até aqui, todos os sócios foram processados com sucesso
            return {
                'sucesso': True,
                'socios_processados': socios_processados,
                'erros': erros,
                'competencia': competencia.strftime('%m/%Y'),
                'empresa': empresa.nome_fantasia
            }
            
    except Exception as e:
        return {
            'sucesso': False,
            'erros': [f'Erro na transação: {str(e)}'],
            'socios_processados': 0
        }


def fechar_periodo_conta_corrente(empresa_id, competencia, usuario=None):
    """
    Fecha oficialmente o período da conta corrente para todos os sócios.
    Marca como fechado e impede alterações futuras.
    
    Args:
        empresa_id: ID da empresa
        competencia: date object do primeiro dia do mês
        usuario: Usuário responsável pelo fechamento
    
    Returns:
        dict: Resultado do fechamento
    """
    from medicos.models.conta_corrente import SaldoMensalContaCorrente
    from django.db import transaction
    from django.utils import timezone
    
    try:
        with transaction.atomic():
            saldos = SaldoMensalContaCorrente.objects.filter(
                empresa_id=empresa_id,
                competencia=competencia,
                fechado=False
            )
            
            if not saldos.exists():
                return {'sucesso': False, 'erros': ['Nenhum saldo encontrado para fechamento']}
            
            # Marcar todos como fechados
            for saldo in saldos:
                saldo.fechar_periodo(usuario)
            
            return {
                'sucesso': True,
                'saldos_fechados': saldos.count(),
                'competencia': competencia.strftime('%m/%Y'),
                'data_fechamento': timezone.now()
            }
            
    except Exception as e:
        return {'sucesso': False, 'erros': [str(e)]}


def obter_saldo_anterior_conta_corrente(empresa_id, socio_id, competencia):
    """
    Obtém o saldo anterior da conta corrente para uma competência específica.
    
    Args:
        empresa_id: ID da empresa
        socio_id: ID do sócio
        competencia: date object do primeiro dia do mês
    
    Returns:
        Decimal: Saldo anterior ou 0 se não encontrado
    """
    from medicos.models.conta_corrente import SaldoMensalContaCorrente, MovimentacaoContaCorrente
    from datetime import date
    
    # Determinar competência anterior
    ano = competencia.year
    mes = competencia.month
    
    if mes == 1:
        competencia_anterior = date(ano - 1, 12, 1)
    else:
        competencia_anterior = date(ano, mes - 1, 1)
    
    try:
        # Buscar saldo persistido do mês anterior
        saldo_mes_anterior = SaldoMensalContaCorrente.objects.get(
            empresa_id=empresa_id,
            socio_id=socio_id,
            competencia=competencia_anterior,
            fechado=True
        )
        return saldo_mes_anterior.saldo_final
        
    except SaldoMensalContaCorrente.DoesNotExist:
        # Calcular dinamicamente se não há saldo persistido
        primeiro_dia_competencia = competencia
        movs_anteriores = MovimentacaoContaCorrente.objects.filter(
            socio_id=socio_id,
            data_movimentacao__lt=primeiro_dia_competencia
        )
        return sum(mov.valor for mov in movs_anteriores)
