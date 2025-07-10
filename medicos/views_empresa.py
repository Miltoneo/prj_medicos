from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models.base import Conta, Empresa

@login_required
def set_empresa(request):
    empresa_id = request.GET.get('empresa_id')
    if empresa_id:
        request.session['empresa_id'] = int(empresa_id)
    # Redireciona para a página anterior ou dashboard
    next_url = request.META.get('HTTP_REFERER') or reverse('medicos:dashboard')
    return redirect(next_url)

@login_required
def empresa_list(request):
    conta_id = request.session.get('conta_id')
    empresas = Empresa.objects.filter(conta_id=conta_id)
    return render(request, 'empresa/empresa_list.html', {'empresas': empresas})

@login_required
def empresa_create(request):
    if request.method == 'POST':
        nome = request.POST.get('name')
        conta_id = request.session.get('conta_id')
        if nome and conta_id:
            Empresa.objects.create(name=nome, conta_id=conta_id, cnpj='00.000.000/0000-00')
            return redirect('medicos:empresa_list')
    return render(request, 'empresa/empresa_create.html')
