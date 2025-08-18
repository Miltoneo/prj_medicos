
"""
Views dos relatórios do sistema Medicos
Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
"""

# Imports padrão Python
from datetime import datetime
from decimal import Decimal

# Imports de terceiros
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

# Imports locais
from medicos.models.base import Empresa, Socio
from medicos.models.fiscal import Aliquotas
from medicos.relatorios.builders import (
    montar_relatorio_mensal_empresa,
    montar_relatorio_mensal_socio,
    montar_relatorio_issqn,
    montar_relatorio_outros,
)
from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente
from medicos.relatorios.apuracao_cofins import montar_relatorio_cofins_persistente
from medicos.relatorios.apuracao_irpj import montar_relatorio_irpj_persistente
from medicos.relatorios.apuracao_irpj_mensal import montar_relatorio_irpj_mensal_persistente
from medicos.relatorios.apuracao_csll import montar_relatorio_csll_persistente

# Helpers
def _obter_mes_ano(request):
    """
    Obtém e padroniza o mês/ano do contexto.
    """
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    return mes_ano

def _contexto_base(request, empresa, menu_nome='Relatórios', cenario_nome=None):
    """
    Monta o contexto base padronizado para todas as views de relatório.
    """
    if empresa is None:
        raise ValueError("empresa deve ser passado explicitamente como objeto Empresa pela view.")
    
    mes_ano = _obter_mes_ano(request)
    request.session['menu_nome'] = menu_nome
    request.session['user_id'] = request.user.id
    
    return {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome,
        'empresa': empresa,
        'empresa_id': empresa.id,
        'user': request.user,
    }

# Views
@login_required
def relatorio_executivo(request, empresa_id):
    """
    View para relatório executivo anual da empresa com dados reais de notas fiscais, impostos e sócios.
    Integra com builders de PIS, COFINS, ISSQN e IRPJ para cálculos precisos.
    Fonte: docs/exemplo_relatorio_anual.html adaptado com dados reais
    Template: relatorios/relatorio_executivo.html
    """
    from django.db.models import Sum, Count, Q
    from datetime import datetime
    from decimal import Decimal
    from medicos.models.fiscal import NotaFiscal
    from medicos.models.base import Socio, Empresa
    from medicos.models.despesas import DespesaRateada, DespesaSocio
    from medicos.models.financeiro import Financeiro
    from medicos.models.relatorios_apuracao_pis import ApuracaoPIS
    from medicos.models.relatorios_apuracao_cofins import ApuracaoCOFINS
    from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente
    from medicos.relatorios.apuracao_cofins import montar_relatorio_cofins_persistente
    
    empresa = Empresa.objects.get(id=empresa_id)
    ano_atual = datetime.now().year
    
    # Dados de notas fiscais por mês (ano atual)
    notas_emitidas_mes = {}
    notas_recebidas_mes = {}
    notas_pendentes_mes = {}
    
    for mes in range(1, 13):
        # Notas emitidas pela empresa (receita) - considera mês de emissão
        notas_emitidas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano_atual,
            dtEmissao__month=mes
        )
        emitidas = notas_emitidas.aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        notas_emitidas_mes[mes] = emitidas
        
        # Notas recebidas pela empresa (receita recebida) - considera mês de recebimento
        notas_recebidas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,  # Empresa é destinatária (emitiu a nota)
            dtRecebimento__year=ano_atual,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False,  # Apenas notas com data de recebimento definida
            status_recebimento='recebido'  # Apenas notas efetivamente recebidas
        )
        recebidas = notas_recebidas.aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        notas_recebidas_mes[mes] = recebidas
        
        # Notas pendentes: status de recebimento diferente de recebido
        pendentes = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano_atual,
            dtEmissao__month=mes,
            status_recebimento__in=['pendente', 'parcial']
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        notas_pendentes_mes[mes] = pendentes
    
    # Dados de despesas coletivas por mês (ano atual)
    despesas_coletivas_mes = {}
    
    for mes in range(1, 13):
        # Despesas coletivas (DespesaRateada) da empresa no mês
        despesas_coletivas = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa=empresa,
            data__year=ano_atual,
            data__month=mes
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
        despesas_coletivas_mes[mes] = despesas_coletivas
    
    # Totais anuais
    total_emitidas = sum(notas_emitidas_mes.values())
    total_recebidas = sum(notas_recebidas_mes.values())
    total_pendentes = sum(notas_pendentes_mes.values())
    total_despesas_coletivas = sum(despesas_coletivas_mes.values())
    percentual_pendencias = float(total_pendentes / total_emitidas * 100) if total_emitidas > 0 else 0
    
    # Dados dos sócios ativos com cálculos reais de impostos
    socios_data = []
    socios = Socio.objects.filter(empresa=empresa, ativo=True).select_related('pessoa').order_by('pessoa__name')
    
    for socio in socios:
        socio_meses = {}
        receita_bruta_anual = Decimal('0')
        total_impostos_anual = Decimal('0')
        despesas_anual = Decimal('0')
        
        for mes in range(1, 13):
            # Buscar dados reais de notas fiscais do sócio no mês através dos rateios
            notas_socio = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                rateios_medicos__medico=socio,
                dtEmissao__year=ano_atual,
                dtEmissao__month=mes
            ).distinct()
            
            receita_bruta = notas_socio.aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
            receita_bruta_anual += receita_bruta
            
            # Calcular impostos usando os valores reais das notas fiscais
            impostos_agregados = notas_socio.aggregate(
                total_iss=Sum('val_ISS'),
                total_pis=Sum('val_PIS'), 
                total_cofins=Sum('val_COFINS'),
                total_ir=Sum('val_IR'),
                total_csll=Sum('val_CSLL')
            )
            
            total_impostos_mes = (
                (impostos_agregados['total_iss'] or Decimal('0')) +
                (impostos_agregados['total_pis'] or Decimal('0')) +
                (impostos_agregados['total_cofins'] or Decimal('0')) +
                (impostos_agregados['total_ir'] or Decimal('0')) +
                (impostos_agregados['total_csll'] or Decimal('0'))
            )
            total_impostos_anual += total_impostos_mes
            
            # Receita líquida
            receita_liquida = receita_bruta - total_impostos_mes
            
            # Saldo das movimentações financeiras do sócio no mês (dados reais)
            movimentacoes_financeiras = Financeiro.objects.filter(
                socio=socio,
                data_movimentacao__year=ano_atual,
                data_movimentacao__month=mes
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
            
            # Despesas do sócio no mês (dados reais)
            # Despesas diretas do sócio (DespesaSocio)
            despesas_diretas = DespesaSocio.objects.filter(
                socio=socio,
                data__year=ano_atual,
                data__month=mes
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
            
            # Despesas rateadas: calcular a parte do sócio nas despesas rateadas
            from medicos.models.despesas import ItemDespesaRateioMensal
            data_referencia = datetime(ano_atual, mes, 1).date()
            
            despesas_rateadas_valor = Decimal('0')
            despesas_rateadas = DespesaRateada.objects.filter(
                data__year=ano_atual,
                data__month=mes,
                item_despesa__grupo_despesa__empresa=empresa
            )
            
            for despesa_rateada in despesas_rateadas:
                # Verificar se o sócio tem configuração de rateio para esta despesa no mês
                config_rateio = ItemDespesaRateioMensal.objects.filter(
                    item_despesa=despesa_rateada.item_despesa,
                    socio=socio,
                    data_referencia=data_referencia,
                    ativo=True
                ).first()
                
                if config_rateio and config_rateio.percentual_rateio:
                    valor_rateio = despesa_rateada.valor * (config_rateio.percentual_rateio / 100)
                    despesas_rateadas_valor += valor_rateio
            
            despesas = despesas_diretas + despesas_rateadas_valor
            despesas_anual += despesas
            
            # Rateio mensal do adicional de IR: usar a mesma lógica do ESPELHO DO ADICIONAL DE IR MENSAL
            from medicos.models.fiscal import NotaFiscal, Aliquotas
            
            # Buscar alíquotas da empresa para o cálculo de adicional de IR
            try:
                aliquota = Aliquotas.objects.filter(empresa=empresa).first()
                valor_base_adicional = 0
                aliquota_adicional = 0
                
                if aliquota and hasattr(aliquota, 'IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL'):
                    valor_base_adicional = float(aliquota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL)
                    aliquota_adicional = float(aliquota.IRPJ_ADICIONAL) / 100
                
                # Calcular receita bruta do sócio no mês através dos rateios
                receita_bruta_socio_mes = notas_socio.aggregate(
                    total_rateio=Sum('rateios_medicos__valor_bruto_medico')
                )['total_rateio'] or Decimal('0')
                
                # Separar receita do sócio por tipo de serviço para aplicar presunções corretas
                receita_consultas_socio = notas_socio.filter(
                    tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
                ).aggregate(
                    total_rateio=Sum('rateios_medicos__valor_bruto_medico')
                )['total_rateio'] or Decimal('0')
                
                receita_outros_socio = notas_socio.filter(
                    tipo_servico=NotaFiscal.TIPO_SERVICO_OUTROS
                ).aggregate(
                    total_rateio=Sum('rateios_medicos__valor_bruto_medico')
                )['total_rateio'] or Decimal('0')
                
                # Calcular base de cálculo do IR do sócio conforme presunção de lucro
                if aliquota:
                    base_consultas_socio = receita_consultas_socio * (Decimal(str(aliquota.IRPJ_PRESUNCAO_CONSULTA)) / 100)
                    base_outros_socio = receita_outros_socio * (Decimal(str(aliquota.IRPJ_PRESUNCAO_OUTROS)) / 100)
                    base_calculo_ir_socio = base_consultas_socio + base_outros_socio
                    
                    # Calcular adicional de IR baseado na base individual do sócio
                    excedente_adicional_socio = max(base_calculo_ir_socio - Decimal(str(valor_base_adicional)), Decimal('0'))
                    rateio_ir = excedente_adicional_socio * Decimal(str(aliquota_adicional))
                else:
                    rateio_ir = Decimal('0')
                
            except Exception:
                rateio_ir = Decimal('0')
            
            saldo_transferir = receita_liquida + movimentacoes_financeiras - despesas - rateio_ir
            
            socio_meses[mes] = {
                'receita_bruta': receita_bruta,
                'total_impostos': total_impostos_mes,
                'receita_liquida': receita_liquida,
                'movimentacoes_financeiras': movimentacoes_financeiras,
                'despesas': despesas,
                'rateio_ir': rateio_ir,
                'saldo_transferir': saldo_transferir
            }
        
        # Totais do semestre (Jan-Jun)
        receita_semestral = sum(socio_meses[m]['receita_bruta'] for m in range(1, 7))
        saldo_acumulado = sum(socio_meses[m]['saldo_transferir'] for m in range(1, 7))
        
        # Carga tributária real baseada nos cálculos
        carga_tributaria = float(total_impostos_anual / receita_bruta_anual * 100) if receita_bruta_anual > 0 else 0
        
        socios_data.append({
            'socio': socio,
            'meses': socio_meses,
            'receita_semestral': receita_semestral,
            'saldo_acumulado': saldo_acumulado,
            'carga_tributaria': carga_tributaria,
            'receita_bruta_anual': receita_bruta_anual,
            'total_impostos_anual': total_impostos_anual,
            'despesas_anual': despesas_anual
        })
    
    context = _contexto_base(request, empresa=empresa, menu_nome='Apuração', cenario_nome='Relatório Executivo')
    context.update({
        'titulo_pagina': 'Relatório Executivo Anual',
        'ano_atual': ano_atual,
        'notas_emitidas_mes': notas_emitidas_mes,
        'notas_recebidas_mes': notas_recebidas_mes,
        'notas_pendentes_mes': notas_pendentes_mes,
        'despesas_coletivas_mes': despesas_coletivas_mes,
        'total_emitidas': total_emitidas,
        'total_recebidas': total_recebidas,
        'total_pendentes': total_pendentes,
        'total_despesas_coletivas': total_despesas_coletivas,
        'percentual_pendencias': percentual_pendencias,
        'socios_data': socios_data,
    })
    return render(request, 'relatorios/relatorio_executivo.html', context)


@login_required
def relatorio_mensal_empresa(request, empresa_id):
    """
    View padronizada para relatório mensal da empresa.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_empresa.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Empresa')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Relatório Mensal da Empresa',
    })
    return render(request, 'relatorios/relatorio_mensal_empresa.html', context)

def _obter_socio_selecionado(empresa, socio_id_raw):
    """
    Obtém o sócio selecionado ou o primeiro disponível.
    """
    socios = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
    socio_selecionado = None
    socio_id = None
    
    if socio_id_raw:
        try:
            socio_id = int(socio_id_raw)
            socio_selecionado = socios.filter(id=socio_id).first()
        except (ValueError, TypeError):
            socio_selecionado = None
    
    if not socio_selecionado:
        socio_selecionado = socios.first()
        socio_id = socio_selecionado.id if socio_selecionado else None
    
    return socios, socio_selecionado, socio_id

def _processar_movimentacoes_financeiras(relatorio_obj):
    """
    Processa e normaliza movimentações financeiras.
    """
    lista_movimentacoes = getattr(relatorio_obj, 'lista_movimentacoes_financeiras', [])
    for mov in lista_movimentacoes:
        if isinstance(mov, dict):
            if 'tipo' not in mov or mov['tipo'] in (None, ''):
                mov['tipo'] = mov.get('descricao', '-')
        else:
            if not hasattr(mov, 'tipo') or mov.tipo in (None, ''):
                mov.tipo = getattr(mov, 'descricao', '-')
    return lista_movimentacoes

def _obter_contexto_aliquotas(empresa, base_calculo_ir):
    """
    Obtém contexto de alíquotas para cálculos de IR.
    """
    try:
        aliquota = Aliquotas.objects.filter(empresa=empresa).first()
        if aliquota:
            valor_base_adicional = aliquota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL
            aliquota_adicional = aliquota.IRPJ_ADICIONAL
            excedente = max(base_calculo_ir - float(valor_base_adicional), 0)
            return {
                'valor_base_adicional': valor_base_adicional,
                'aliquota_adicional': aliquota_adicional,
                'base_calculo_ir': base_calculo_ir,
                'excedente_adicional': excedente,
            }
    except Exception:
        pass
    
    return {
        'valor_base_adicional': 0,
        'aliquota_adicional': 0,
        'base_calculo_ir': 0,
        'excedente_adicional': 0,
    }

@login_required
def relatorio_mensal_socio(request, empresa_id):
    """
    View padronizada para relatório mensal do sócio.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_socio.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    
    # Obter sócio selecionado
    socio_id_raw = request.GET.get('socio_id')
    socios, socio_selecionado, socio_id = _obter_socio_selecionado(empresa, socio_id_raw)
    
    # Obter dados do relatório
    relatorio_dict = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)
    relatorio_obj = relatorio_dict['relatorio']
    
    # Processar movimentações financeiras
    lista_movimentacoes = _processar_movimentacoes_financeiras(relatorio_obj)
    
    # Montar dicionário do relatório com todos os dados necessários
    relatorio = {
        'socios': list(socios),
        'socio_id': socio_id,
        'socio_nome': socio_selecionado.pessoa.name if socio_selecionado else '',
        'competencia': mes_ano,
        'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M'),
        # Dados financeiros básicos
        'despesas_com_rateio': getattr(relatorio_obj, 'lista_despesas_com_rateio', []),
        'despesas_sem_rateio': getattr(relatorio_obj, 'lista_despesas_sem_rateio', []),
        'despesa_com_rateio': getattr(relatorio_obj, 'despesa_com_rateio', 0),
        'despesa_sem_rateio': getattr(relatorio_obj, 'despesa_sem_rateio', 0),
        'despesas_total': getattr(relatorio_obj, 'despesas_total', 0),
        'movimentacoes_financeiras': lista_movimentacoes,
        'saldo_movimentacao_financeira': getattr(relatorio_obj, 'saldo_movimentacao_financeira', 0),
        'notas_fiscais': getattr(relatorio_obj, 'lista_notas_fiscais', []),
        # Totais da empresa
        'total_notas_emitidas_mes': getattr(relatorio_obj, 'total_notas_emitidas_mes', 0),
        'total_notas_bruto': getattr(relatorio_obj, 'total_notas_bruto', 0),
        'total_notas_liquido': getattr(relatorio_obj, 'total_notas_liquido', 0),
        # Impostos do sócio
        'total_iss': getattr(relatorio_obj, 'total_iss', 0),
        'total_pis': getattr(relatorio_obj, 'total_pis', 0),
        'total_cofins': getattr(relatorio_obj, 'total_cofins', 0),
        'total_irpj': getattr(relatorio_obj, 'total_irpj', 0),
        'total_irpj_adicional': getattr(relatorio_obj, 'total_irpj_adicional', 0),
        'total_csll': getattr(relatorio_obj, 'total_csll', 0),
        # Dados de apuração
        'receita_bruta_recebida': getattr(relatorio_obj, 'receita_bruta_recebida', 0),
        'receita_liquida': getattr(relatorio_obj, 'receita_liquida', 0),
        'impostos_total': getattr(relatorio_obj, 'impostos_total', 0),
        'saldo_apurado': getattr(relatorio_obj, 'saldo_apurado', 0),
        'saldo_a_transferir': getattr(relatorio_obj, 'saldo_a_transferir', 0),
        # Totais das notas fiscais do sócio (para linha de totais da tabela)
        'total_nf_valor_bruto': getattr(relatorio_obj, 'total_nf_valor_bruto', 0),
        'total_nf_iss': getattr(relatorio_obj, 'total_nf_iss', 0),
        'total_nf_pis': getattr(relatorio_obj, 'total_nf_pis', 0),
        'total_nf_cofins': getattr(relatorio_obj, 'total_nf_cofins', 0),
        'total_nf_irpj': getattr(relatorio_obj, 'total_nf_irpj', 0),
        'total_nf_csll': getattr(relatorio_obj, 'total_nf_csll', 0),
        'total_nf_valor_liquido': getattr(relatorio_obj, 'total_nf_valor_liquido', 0),
        # Campos específicos para o cálculo de IRPJ utilizados no template
        'base_calculo_consultas': relatorio_dict.get('base_calculo_consultas', 0),
        'base_calculo_outros': relatorio_dict.get('base_calculo_outros', 0),
        'base_calculo_ir_total': relatorio_dict.get('base_calculo_ir_total', 0),
        # Faturamento por tipo de serviço
        'faturamento_consultas': getattr(relatorio_obj, 'faturamento_consultas', 0),
        'faturamento_plantao': getattr(relatorio_obj, 'faturamento_plantao', 0),
        'faturamento_outros': getattr(relatorio_obj, 'faturamento_outros', 0),
    }
    
    # Montar contexto final
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Sócio')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Relatório Mensal do Sócio',
        'valor_adicional_rateio': relatorio_dict.get('valor_adicional_rateio', 0),
        'participacao_socio_percentual': relatorio_dict.get('participacao_socio_percentual', 0),
        'receita_bruta_socio': relatorio_dict.get('receita_bruta_socio', 0),
    })
    
    # Adicionar contexto de alíquotas
    base_calculo_ir = relatorio.get('base_calculo_ir_total', 0)
    context.update(_obter_contexto_aliquotas(empresa, base_calculo_ir))
    
    # Adicionar campos específicos do espelho de cálculo
    context.update({
        'base_calculo_consultas_ir': relatorio_dict.get('base_calculo_consultas_ir', 0),
        'base_calculo_outros_ir': relatorio_dict.get('base_calculo_outros_ir', 0),
        'base_consultas_medicas': relatorio_dict.get('base_consultas_medicas', 0),
        'base_outros_servicos': relatorio_dict.get('base_outros_servicos', 0),
        'valor_base_adicional': relatorio_dict.get('valor_base_adicional', 0),
        'excedente_adicional': relatorio_dict.get('excedente_adicional', 0),
        'aliquota_adicional': relatorio_dict.get('aliquota_adicional', 0),
    })
    
    return render(request, 'relatorios/relatorio_mensal_socio.html', context)

@login_required
def relatorio_apuracao(request, empresa_id):
    """
    View padronizada para apuração de impostos (ISSQN, PIS, COFINS, etc).
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/apuracao_de_impostos.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    ano = mes_ano.split('-')[0] if '-' in mes_ano else mes_ano[:4]
    competencias = [f'{mes:02d}/{ano}' for mes in range(1, 13)]
    trimestres = [f'T{n}' for n in range(1, 5)]
    
    # Relatório ISSQN
    relatorio_issqn = montar_relatorio_issqn(empresa_id, mes_ano)
    # Obter alíquota ISSQN para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_issqn = relatorio_issqn['linhas'][0].get('aliquota', 0) if relatorio_issqn['linhas'] else 0
    linhas_issqn = [
        {'descricao': 'Base cálculo', 'valores': [linha['valor_bruto'] for linha in relatorio_issqn['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_issqn}%)', 'valores': [linha['valor_iss'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha['imposto_retido_nf'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha['valor_iss'] - linha['imposto_retido_nf'] for linha in relatorio_issqn['linhas']]},
    ]

    # Relatório PIS
    relatorio_pis = montar_relatorio_pis_persistente(empresa_id, ano)
    # Obter alíquota PIS para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_pis = relatorio_pis['linhas'][0].get('aliquota', 0) if relatorio_pis['linhas'] else 0
    linhas_pis = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_pis}%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_pis['linhas']]},
    ]

    # Relatório COFINS
    relatorio_cofins = montar_relatorio_cofins_persistente(empresa_id, ano)
    # Obter alíquota COFINS para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_cofins = relatorio_cofins['linhas'][0].get('aliquota', 0) if relatorio_cofins['linhas'] else 0
    linhas_cofins = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_cofins}%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_cofins['linhas']]},
    ]

    # Relatório IRPJ Mensal
    relatorio_irpj_mensal = montar_relatorio_irpj_mensal_persistente(empresa_id, ano)
    # Obter alíquota IRPJ para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_irpj = relatorio_irpj_mensal['linhas'][0].get('aliquota', 0) if relatorio_irpj_mensal['linhas'] else 0
    linhas_irpj_mensal = [
        {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Receita bruta', 'valores': [linha.get('receita_bruta', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_irpj}%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Adicional', 'valores': [linha.get('adicional', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_irpj_mensal['linhas']]},
    ]

    # Relatório IRPJ
    relatorio_irpj = montar_relatorio_irpj_persistente(empresa_id, ano)
    linhas_irpj = [
        {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Receita bruta', 'valores': [linha.get('receita_bruta', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Rendimentos aplicações', 'valores': [linha.get('rendimentos_aplicacoes', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Base cálculo total', 'valores': [linha.get('base_calculo_total', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Adicional', 'valores': [linha.get('adicional', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Retenção aplicação financeira', 'valores': [linha.get('retencao_aplicacao_financeira', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_irpj['linhas']]},
    ]

    # Relatório CSLL
    relatorio_csll = montar_relatorio_csll_persistente(empresa_id, ano)
    linhas_csll = [
        {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Receita bruta', 'valores': [linha.get('receita_bruta', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Rendimentos aplicações', 'valores': [linha.get('rendimentos_aplicacoes', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Base cálculo total', 'valores': [linha.get('base_calculo_total', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_csll['linhas']]},
    ]

    # Espelho do Adicional de IR Trimestral
    espelho_adicional_trimestral = []
    limite_trimestral = Decimal('60000.00')  # R$ 60.000,00/trimestre
    aliquota_adicional = Decimal('10.00')  # 10%
    
    for linha in relatorio_irpj['linhas']:
        receita_consultas = linha.get('receita_consultas', 0)
        receita_outros = linha.get('receita_outros', 0)
        receita_bruta = linha.get('receita_bruta', 0)
        
        # Cálculo das bases com presunções corretas
        base_calculo_consultas = Decimal(str(receita_consultas)) * Decimal('0.32')  # 32% para consultas
        base_calculo_outros = Decimal(str(receita_outros)) * Decimal('0.08')  # 8% para outros (não 32%!)
        base_calculo_total = base_calculo_consultas + base_calculo_outros
        
        excedente = max(Decimal('0'), base_calculo_total - limite_trimestral)
        adicional_devido = excedente * (aliquota_adicional / Decimal('100'))
        
        espelho_adicional_trimestral.append({
            'competencia': linha.get('competencia', ''),
            'receita_bruta': receita_bruta,
            'receita_consultas': receita_consultas,
            'receita_outros': receita_outros,
            'base_calculo_consultas': base_calculo_consultas,
            'base_calculo_outros': base_calculo_outros,
            'base_calculo_total': base_calculo_total,
            'limite_isencao': limite_trimestral,
            'excedente': excedente,
            'aliquota_adicional': aliquota_adicional,
            'adicional_devido': adicional_devido,
        })

    # Espelho do Adicional de IR Mensal (exemplo para julho/2025)
    from medicos.models.base import Socio
    from medicos.models.fiscal import NotaFiscalRateioMedico, NotaFiscal, Aliquotas
    from django.db.models import Sum
    
    espelho_adicional_mensal = []
    mes_exemplo = 7  # Julho
    ano_exemplo = 2025
    limite_mensal = Decimal('20000.00')  # R$ 20.000,00/mês (base para adicional)
    
    # Buscar sócios ativos da empresa
    socios_ativos = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
    
    for socio in socios_ativos:
        # Buscar rateios do sócio em julho/2025
        rateios_mes = NotaFiscalRateioMedico.objects.filter(
            nota_fiscal__empresa_destinataria=empresa,
            nota_fiscal__dtEmissao__year=ano_exemplo,
            nota_fiscal__dtEmissao__month=mes_exemplo,
            medico=socio
        )
        
        # Calcular receita do sócio por tipo de serviço
        receita_consultas_socio = rateios_mes.filter(
            nota_fiscal__tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
        ).aggregate(total=Sum('valor_bruto_medico'))['total'] or Decimal('0')
        
        receita_outros_socio = rateios_mes.filter(
            nota_fiscal__tipo_servico=NotaFiscal.TIPO_SERVICO_OUTROS
        ).aggregate(total=Sum('valor_bruto_medico'))['total'] or Decimal('0')
        
        receita_total_socio = receita_consultas_socio + receita_outros_socio
        
        # Só incluir sócios que tiveram receita no mês
        if receita_total_socio > 0:
            # Buscar alíquotas para cálculo
            aliquota_config = Aliquotas.objects.filter(empresa=empresa).first()
            if aliquota_config:
                # Calcular base de cálculo individual do sócio
                base_consultas_socio = receita_consultas_socio * (Decimal(str(aliquota_config.IRPJ_PRESUNCAO_CONSULTA)) / 100)
                base_outros_socio = receita_outros_socio * (Decimal(str(aliquota_config.IRPJ_PRESUNCAO_OUTROS)) / 100)
                base_total_socio = base_consultas_socio + base_outros_socio
                
                # Usar o valor configurado na empresa para limite
                limite_adicional = Decimal(str(aliquota_config.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL))
                excedente_socio = max(base_total_socio - limite_adicional, Decimal('0'))
                adicional_socio = excedente_socio * (Decimal(str(aliquota_config.IRPJ_ADICIONAL)) / 100)
                
                espelho_adicional_mensal.append({
                    'socio_nome': socio.pessoa.name,
                    'receita_consultas': receita_consultas_socio,
                    'receita_outros': receita_outros_socio,
                    'receita_total': receita_total_socio,
                    'base_consultas': base_consultas_socio,
                    'base_outros': base_outros_socio,
                    'base_total': base_total_socio,
                    'limite_adicional': limite_adicional,
                    'excedente': excedente_socio,
                    'aliquota_adicional': Decimal(str(aliquota_config.IRPJ_ADICIONAL)),
                    'adicional_devido': adicional_socio,
                })
    
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração de Impostos')
    context.update({
        'ano': ano,
        'competencias': competencias,
        'trimestres': trimestres,
        'linhas_issqn': linhas_issqn,
        'linhas_pis': linhas_pis,
        'totais_pis': relatorio_pis.get('totais', {}),
        'linhas_cofins': linhas_cofins,
        'totais_cofins': relatorio_cofins.get('totais', {}),
        'linhas_irpj_mensal': linhas_irpj_mensal,
        'linhas_irpj': linhas_irpj,
        'linhas_csll': linhas_csll,
        'espelho_adicional_trimestral': espelho_adicional_trimestral,
        'espelho_adicional_mensal': espelho_adicional_mensal,
        'titulo_pagina': 'Apuração de Impostos',
    })
    return render(request, 'relatorios/apuracao_de_impostos.html', context)


@login_required
def relatorio_outros(request, empresa_id):
    """
    View padronizada para apuração de outros relatórios.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_outros.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_outros(empresa_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração Outros')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Apuração Outros',
    })
    return render(request, 'relatorios/relatorio_outros.html', context)


@login_required
def relatorio_executivo_pdf(request, conta_id):
    """
    View padronizada para geração do PDF do relatório executivo.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_executivo.html
    """
    empresa = Empresa.objects.get(id=conta_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_mensal_empresa(conta_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo PDF')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Relatório Executivo PDF',
    })
    return render(request, 'relatorios/relatorio_executivo.html', context)
