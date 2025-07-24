# Helpers
def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    """
    Monta o contexto base para todas as views de relatório.
    """
    # Preparar variáveis de contexto essenciais para o sistema
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'Relatórios'
    request.session['user_id'] = request.user.id
    if empresa is None:
        raise ValueError("empresa deve ser passado explicitamente como objeto Empresa pela view.")
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Relatórios',
        'empresa': empresa,
        'empresa_id': empresa.id,
        'user': request.user,
    }
    return context
"""
Views dos relatórios do sistema Medicos
Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
"""

# Imports padrão Python
from datetime import datetime

# Imports de terceiros
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone


# Imports locais
from medicos.models.base import Empresa, Socio
from medicos.relatorios.builders import (
    montar_relatorio_mensal_empresa,
    montar_relatorio_mensal_socio,
    montar_relatorio_issqn,
    montar_relatorio_outros,
)

from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente

# Views
@login_required
def relatorio_executivo(request, empresa_id):
    """
    View padronizada para relatório executivo da empresa.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_executivo.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo')
    context['relatorio'] = relatorio
    context['titulo_pagina'] = 'Relatório Executivo'
    return render(request, 'relatorios/relatorio_executivo.html', context)


# Relatórios mensais e apuração
@login_required
def relatorio_mensal_empresa(request, empresa_id):
    """
    View padronizada para relatório mensal da empresa.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_empresa.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Empresa')
    context['relatorio'] = relatorio
    context['titulo_pagina'] = 'Relatório Mensal da Empresa'
    return render(request, 'relatorios/relatorio_mensal_empresa.html', context)

@login_required
def relatorio_mensal_socio(request, empresa_id):
    """
    View padronizada para relatório mensal do sócio.
    Monta o dicionário relatorio com todos os campos globais e dados do sócio selecionado.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_socio.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    # Lê mes_ano do GET, senão session, senão mês atual
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano') or datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    socios = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
    socio_id_raw = request.GET.get('socio_id')
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
    relatorio_obj = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)['relatorio']
    lista_movimentacoes = getattr(relatorio_obj, 'lista_movimentacoes_financeiras', [])
    # Garante que cada movimentação tem o campo 'tipo' preenchido
    for mov in lista_movimentacoes:
        # Suporte para dict e objeto
        if isinstance(mov, dict):
            if 'tipo' not in mov or mov['tipo'] in (None, ''):
                mov['tipo'] = mov.get('descricao', '-')
        else:
            if not hasattr(mov, 'tipo') or mov.tipo in (None, ''):
                mov.tipo = getattr(mov, 'descricao', '-')
    relatorio = {
        'socios': list(socios),
        'socio_id': socio_id,
        'socio_nome': socio_selecionado.pessoa.name if socio_selecionado else '',
        'competencia': mes_ano,
        'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M'),
        # Campos esperados pelo template, conforme análise do fluxo
        'despesas_com_rateio': getattr(relatorio_obj, 'lista_despesas_com_rateio', []),
        'despesas_sem_rateio': getattr(relatorio_obj, 'lista_despesas_sem_rateio', []),
        'despesa_com_rateio': getattr(relatorio_obj, 'despesa_com_rateio', 0),
        'despesa_sem_rateio': getattr(relatorio_obj, 'despesa_sem_rateio', 0),
        'despesas_total': getattr(relatorio_obj, 'despesas_total', 0),
        'movimentacoes_financeiras': lista_movimentacoes,
        'saldo_movimentacao_financeira': getattr(relatorio_obj, 'saldo_movimentacao_financeira', 0),
        'notas_fiscais': getattr(relatorio_obj, 'lista_notas_fiscais', []),
        'total_notas_emitidas_mes': getattr(relatorio_obj, 'total_notas_emitidas_mes', 0),
        'total_notas_bruto': getattr(relatorio_obj, 'total_notas_bruto', 0),
        'total_notas_liquido': getattr(relatorio_obj, 'total_notas_liquido', 0),
        'total_iss': getattr(relatorio_obj, 'total_iss', 0),
        'total_pis': getattr(relatorio_obj, 'total_pis', 0),
        'total_cofins': getattr(relatorio_obj, 'total_cofins', 0),
        'total_irpj': getattr(relatorio_obj, 'total_irpj', 0),
        'total_csll': getattr(relatorio_obj, 'total_csll', 0),
        'receita_bruta_recebida': getattr(relatorio_obj, 'receita_bruta_recebida', 0),
        'receita_liquida': getattr(relatorio_obj, 'receita_liquida', 0),
        'impostos_total': getattr(relatorio_obj, 'impostos_total', 0),
        'saldo_apurado': getattr(relatorio_obj, 'saldo_apurado', 0),
        'saldo_a_transferir': getattr(relatorio_obj, 'saldo_a_transferir', 0),
        # Dados do sócio e empresa
        'socio_cpf': getattr(socio_selecionado.pessoa, 'cpf', '') if socio_selecionado else '',
        'socio_email': getattr(socio_selecionado.pessoa, 'email', '') if socio_selecionado else '',
        'empresa_nome': empresa.name,
        'empresa_cnpj': empresa.cnpj,
        'empresa_id': empresa.id,
    }
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Sócio')
    context['relatorio'] = relatorio
    context['titulo_pagina'] = 'Relatório Mensal do Sócio'
    return render(request, 'relatorios/relatorio_mensal_socio.html', context)

@login_required
def relatorio_apuracao(request, empresa_id):
    """
    View padronizada para apuração de impostos (ISSQN, PIS, COFINS, etc).
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/apuracao_de_impostos.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    competencias = [f'{mes:02d}/{mes_ano[:4]}' for mes in range(1, 13)]
    relatorio_issqn = montar_relatorio_issqn(empresa_id, mes_ano)
    linhas_issqn = [
        {'descricao': 'Base cálculo', 'valores': [linha['valor_bruto'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha['valor_iss'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [round(linha['valor_iss']*0.2,2) for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [round(linha['valor_iss']*0.8,2) for linha in relatorio_issqn['linhas']]},
    ]

    # Montagem do relatório PIS
    # Import padronizado no topo do arquivo
    ano = mes_ano.split('-')[0] if '-' in mes_ano else mes_ano[:4]
    relatorio_pis = montar_relatorio_pis_persistente(empresa_id, ano)
    linhas_pis = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_pis['linhas']]},
    ]
    totais_pis = relatorio_pis.get('totais', {})

    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração de Impostos')
    context.update({
        'competencias': competencias,
        'linhas_issqn': linhas_issqn,
        'linhas_pis': linhas_pis,
        'totais_pis': totais_pis,
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
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_outros(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração Outros')
    context['relatorio'] = relatorio
    context['titulo_pagina'] = 'Apuração Outros'
    return render(request, 'relatorios/relatorio_outros.html', context)


@login_required
def relatorio_executivo_pdf(request, conta_id):
    """
    View padronizada para geração do PDF do relatório executivo.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_executivo.html
    """
    empresa = Empresa.objects.get(id=conta_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_empresa(conta_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo PDF')
    context['relatorio'] = relatorio
    context['titulo_pagina'] = 'Relatório Executivo PDF'
    return render(request, 'relatorios/relatorio_executivo.html', context)
