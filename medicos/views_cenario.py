from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def cenario_cadastro(request):
    request.session['menu_nome'] = 'Cadastro'
    request.session['cenario_nome'] = 'Cadastro'
    # Assume que sempre haverá empresa selecionada
    empresa_id = request.session.get('empresa_id')
    return redirect('medicos:lista_socios_empresa', empresa_id=empresa_id)


