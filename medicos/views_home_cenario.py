
# Imports: Standard Library
from datetime import datetime

# Imports: Django
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Helpers
def main_context(request, empresa=None, menu_nome=None, cenario_nome=None):
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or '',
        'cenario_nome': cenario_nome or 'Home',
    }
    if empresa:
        context['empresa'] = empresa
    return context

# Views
@login_required
def home_cenario(request):
    context = main_context(request, menu_nome='Home', cenario_nome='Home')
    return render(request, 'layouts/base_cenario_home.html', context)
