from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home_cenario(request):
    from datetime import datetime
    mes_ano = request.GET.get('mes_ano')
    if mes_ano:
        request.session['mes_ano'] = mes_ano
    else:
        mes_ano = request.session.get('mes_ano')
        if not mes_ano:
            mes_ano = datetime.now().strftime('%Y-%m')
            request.session['mes_ano'] = mes_ano
    return render(request, 'layouts/base_cenario_home.html', {'mes_ano': mes_ano})
