from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def cenario_faturamento(request):
    request.session['menu_nome'] = 'Faturamento'
    request.session['cenario_nome'] = 'Cenário Faturamento'
    request.session['titulo_pagina'] = 'Notas Fiscais'
    return redirect('medicos:lista_notas_fiscais')


