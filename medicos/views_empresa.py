from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models.base import Conta, Empresa
from .models.base import ContaMembership

def get_or_set_conta_id(request):
    conta_id = request.session.get('conta_id')
    if not conta_id:
        membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
        if membership:
            conta_id = membership.conta_id
            request.session['conta_id'] = conta_id
    return conta_id

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
    conta_id = get_or_set_conta_id(request)
    empresas = Empresa.objects.filter(conta_id=conta_id) if conta_id else []
    return render(request, 'empresa/empresa_list.html', {'empresas': empresas})

@login_required
def empresa_create(request):
    from .models.base import Empresa
    error = None
    conta_id = get_or_set_conta_id(request)
    if request.method == 'POST':
        nome = request.POST.get('name')
        cnpj = request.POST.get('cnpj')
        regime = request.POST.get('regime_tributario')
        if not conta_id:
            error = 'Conta não encontrada para este usuário.'
        elif not (nome and cnpj and regime):
            error = 'Preencha todos os campos obrigatórios.'
        else:
            Empresa.objects.create(name=nome, cnpj=cnpj, conta_id=conta_id, regime_tributario=regime)
            return redirect('medicos:empresa_list')
    regimes = Empresa.REGIME_CHOICES
    return render(request, 'empresa/empresa_create.html', {'regimes': regimes, 'error': error})

@login_required
def empresa_detail(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    return render(request, 'empresa/empresa_detail.html', {'empresa': empresa})

@login_required
def empresa_update(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    error = None
    if request.method == 'POST':
        nome = request.POST.get('name')
        cnpj = request.POST.get('cnpj')
        regime = request.POST.get('regime_tributario')
        if not (nome and cnpj and regime):
            error = 'Preencha todos os campos obrigatórios.'
        else:
            empresa.name = nome
            empresa.cnpj = cnpj
            empresa.regime_tributario = regime
            empresa.save()
            return redirect('medicos:empresa_list')
    regimes = Empresa.REGIME_CHOICES
    return render(request, 'empresa/empresa_update.html', {'empresa': empresa, 'regimes': regimes, 'error': error})

@login_required
def empresa_delete(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.delete()
        return redirect('medicos:empresa_list')
    return render(request, 'empresa/empresa_delete.html', {'empresa': empresa})
