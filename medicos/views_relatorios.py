
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
    View padronizada para relatório executivo da empresa.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_executivo.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Relatório Executivo',
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
    linhas_issqn = [
        {'descricao': 'Base cálculo', 'valores': [linha['valor_bruto'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha['valor_iss'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha['imposto_retido_nf'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha['valor_iss'] - linha['imposto_retido_nf'] for linha in relatorio_issqn['linhas']]},
    ]

    # Relatório PIS
    relatorio_pis = montar_relatorio_pis_persistente(empresa_id, ano)
    linhas_pis = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_pis['linhas']]},
    ]

    # Relatório COFINS
    relatorio_cofins = montar_relatorio_cofins_persistente(empresa_id, ano)
    linhas_cofins = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_cofins['linhas']]},
    ]

    # Relatório IRPJ Mensal
    relatorio_irpj_mensal = montar_relatorio_irpj_mensal_persistente(empresa_id, ano)
    linhas_irpj_mensal = [
        {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Receita bruta', 'valores': [linha.get('receita_bruta', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Rendimentos aplicações', 'valores': [linha.get('rendimentos_aplicacoes', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Base cálculo total', 'valores': [linha.get('base_calculo_total', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Adicional', 'valores': [linha.get('adicional', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_irpj_mensal['linhas']]},
        {'descricao': 'Retenção aplicação financeira', 'valores': [linha.get('retencao_aplicacao_financeira', 0) for linha in relatorio_irpj_mensal['linhas']]},
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
