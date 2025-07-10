from django.shortcuts import render, get_object_or_404
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas
from django.contrib.auth.decorators import login_required
from medicos.forms import AliquotaForm
from django.contrib import messages
from django.shortcuts import redirect

@login_required
def lista_aliquotas(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    aliquotas = Aliquotas.objects.filter(conta=empresa.conta)
    context = {
        'empresa': empresa,
        'aliquotas': aliquotas
    }
    return render(request, 'empresa/lista_aliquotas.html', context)

@login_required
def aliquota_edit(request, empresa_id, aliquota_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if aliquota_id == 0:
        aliquota = None
        form = AliquotaForm(request.POST or None)
    else:
        aliquota = get_object_or_404(Aliquotas, id=aliquota_id, conta=empresa.conta)
        form = AliquotaForm(request.POST or None, instance=aliquota)
    if request.method == 'POST' and form.is_valid():
        aliquota = form.save(commit=False)
        aliquota.conta = empresa.conta
        aliquota.save()
        return redirect('lista_aliquotas', empresa_id=empresa.id)
    context = {
        'empresa': empresa,
        'form': form,
        'aliquota': aliquota
    }
    return render(request, 'empresa/aliquota_form.html', context)
