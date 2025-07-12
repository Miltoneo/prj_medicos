from django.shortcuts import render, get_object_or_404
from medicos.models.base import Empresa, Socio
from django.contrib.auth.decorators import login_required
from .tables_socio import SocioTable
from .tables_socio_lista import SocioListaTable
from .filters_socio import SocioFilter
from django_tables2 import RequestConfig

@login_required
def dashboard_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    socios_qs = Socio.objects.filter(empresa=empresa)
    socio_filter = SocioFilter(request.GET, queryset=socios_qs)
    table = SocioTable(socio_filter.qs)
    RequestConfig(request, paginate={'per_page': 20}).configure(table)
    from datetime import datetime
    mes_ano = request.GET.get('mes_ano')
    if mes_ano:
        request.session['mes_ano'] = mes_ano
    else:
        mes_ano = request.session.get('mes_ano')
        if not mes_ano:
            mes_ano = datetime.now().strftime('%Y-%m')
            request.session['mes_ano'] = mes_ano
    return render(request, 'empresa/dashboard_empresa.html', {
        'empresa': empresa,
        'table': table,
        'socio_filter': socio_filter,
        'menu_nome': 'Dashboard',
        'mes_ano': mes_ano,
    })

@login_required
def lista_socios_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    socios_qs = Socio.objects.filter(empresa=empresa)
    socio_filter = SocioFilter(request.GET, queryset=socios_qs)
    table = SocioListaTable(socio_filter.qs)
    RequestConfig(request, paginate={'per_page': 20}).configure(table)
    return render(request, 'empresa/lista_socios_empresa.html', {
        'empresa': empresa,
        'table': table,
        'socio_filter': socio_filter,
    })
