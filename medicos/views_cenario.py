from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def cenario_faturamento(request):
    request.session['menu_nome'] = 'Faturamento'
    request.session['cenario_nome'] = 'Faturamento'
    request.session['titulo_pagina'] = 'Notas Fiscais'

    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        # Redireciona para seleção de empresa se nenhuma estiver selecionada
        return redirect('medicos:empresas')
    return redirect('medicos:lista_notas_fiscais')


