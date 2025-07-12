def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    from datetime import datetime
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'Dashboard Empresa'
    request.session['cenario_nome'] = cenario_nome or 'Dashboard Empresa'
    request.session['user_id'] = request.user.id
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Dashboard Empresa',
        'cenario_nome': cenario_nome or 'Dashboard Empresa',
        'empresa': empresa,
        'user': request.user,
    }
    return context
from django.shortcuts import render, get_object_or_404
from medicos.models.base import Empresa, Socio
from django.contrib.auth.decorators import login_required
from .tables_socio import SocioTable
from .tables_socio_lista import SocioListaTable
from .filters_socio import SocioFilter
from django_tables2 import RequestConfig

@login_required

def main_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    socios_qs = Socio.objects.filter(empresa=empresa)
    socio_filter = SocioFilter(request.GET, queryset=socios_qs)
    table = SocioTable(socio_filter.qs)
    RequestConfig(request, paginate={'per_page': 20}).configure(table)
    
    context = main(request, empresa=empresa, menu_nome='Dashboard', cenario_nome='Dashboard Empresa')
    context['table'] = table
    context['socio_filter'] = socio_filter
    return render(request, 'empresa/dashboard_empresa.html', context)

