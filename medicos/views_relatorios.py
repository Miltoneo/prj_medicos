
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from medicos.relatorios.builders import (
    montar_relatorio_mensal_empresa,
    montar_relatorio_mensal_socio,
    montar_relatorio_issqn,
    montar_relatorio_outros,
)

# Helpers
def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    # Preparar variáveis de contexto essenciais para o sistema
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano

    # Menu e cenário
    request.session['menu_nome'] = menu_nome or 'Relatórios'
    # cenario_nome agora deve ser passado no contexto, não na sessão

    # Usuário
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

# Views
@login_required
def relatorio_executivo(request, empresa_id):
    """
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_executivo.html
    """
    from medicos.models.base import Empresa
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo')
    context['relatorio'] = relatorio
    return render(request, 'relatorios/relatorio_executivo.html', context)


# Relatórios mensais e apuração
@login_required
def relatorio_mensal_empresa(request, empresa_id):
    """
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_empresa.html
    """
    from medicos.models.base import Empresa
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Empresa')
    context['relatorio'] = relatorio
    return render(request, 'relatorios/relatorio_mensal_empresa.html', context)

@login_required
def relatorio_mensal_socio(request, empresa_id):
    """
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_socio.html
    """
    from medicos.models.base import Empresa
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_socio(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Sócio')
    context['relatorio'] = relatorio
    return render(request, 'relatorios/relatorio_mensal_socio.html', context)

@login_required
def relatorio_issqn(request, empresa_id):
    """
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_issqn.html
    """
    from medicos.models.base import Empresa
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_issqn(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração de ISSQN')
    context['relatorio'] = relatorio
    return render(request, 'relatorios/relatorio_issqn.html', context)

@login_required
def relatorio_outros(request, empresa_id):
    """
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_outros.html
    """
    from medicos.models.base import Empresa
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_outros(empresa_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração Outros')
    context['relatorio'] = relatorio
    return render(request, 'relatorios/relatorio_outros.html', context)


@login_required
def relatorio_executivo_pdf(request, conta_id):
    from medicos.models.base import Empresa
    empresa = Empresa.objects.get(id=conta_id)
    mes_ano = request.session.get('mes_ano')
    relatorio = montar_relatorio_mensal_empresa(conta_id, mes_ano)['relatorio']
    context = main(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo PDF')
    context['relatorio'] = relatorio
    return render(request, 'relatorios/relatorio_executivo.html', context)
