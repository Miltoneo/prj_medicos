from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def relatorio_executivo(request):
    # Adapte o contexto conforme necessário
    context = {}
    return render(request, 'relatorios/relatorio_executivo.html', context)

@login_required
def relatorio_executivo_pdf(request, conta_id):
    # Implemente a lógica de PDF conforme necessário
    context = {'conta_id': conta_id}
    return render(request, 'relatorios/relatorio_executivo.html', context)
