
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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

    # Retorna contexto para renderização
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Relatórios',
        # 'cenario_nome': cenario_nome or 'Relatórios',  # Removed from context
        'empresa': empresa,
        'user': request.user,
    }
    return context

# Views
@login_required
def relatorio_executivo(request):
    context = main(request, menu_nome='Relatórios', cenario_nome='Relatório Executivo')
    context['cenario_nome'] = 'Relatórios'
    return render(request, 'relatorios/relatorio_executivo.html', context)


@login_required
def relatorio_executivo_pdf(request, conta_id):
    context = main(request, menu_nome='Relatórios', cenario_nome='Relatório Executivo PDF')
    context['cenario_nome'] = 'Relatórios'
    context['conta_id'] = conta_id
    return render(request, 'relatorios/relatorio_executivo.html', context)
