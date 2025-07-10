from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from medicos.models.base import Empresa
from medicos.models.despesas import GrupoDespesa
from medicos.forms import GrupoDespesaForm
from django.contrib import messages
from django.core.paginator import Paginator
from medicos.filters import GrupoDespesaFilter

@login_required
def lista_grupos_despesa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    sort = request.GET.get('sort', 'codigo')
    if sort not in ['codigo', 'descricao', '-codigo', '-descricao']:
        sort = 'codigo'
    qs = GrupoDespesa.objects.filter(conta=empresa.conta).order_by(sort, 'descricao')
    filtro = GrupoDespesaFilter(request.GET, queryset=qs)
    grupos_list = filtro.qs
    paginator = Paginator(grupos_list, 20)
    page_number = request.GET.get('page')
    grupos = paginator.get_page(page_number)
    context = {
        'empresa': empresa,
        'grupos': grupos,
        'filter': filtro,
        'request': request
    }
    return render(request, 'empresa/lista_grupos_despesa.html', context)

@login_required
def grupo_despesa_edit(request, empresa_id, grupo_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    grupo = None
    if grupo_id != 0:
        grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    form = GrupoDespesaForm(request.POST or None, instance=grupo)
    if request.method == 'POST' and form.is_valid():
        grupo = form.save(commit=False)
        grupo.conta = empresa.conta
        grupo.save()
        messages.success(request, 'Grupo de despesas salvo com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa.id)
    context = {
        'empresa': empresa,
        'form': form,
        'grupo': grupo
    }
    return render(request, 'empresa/grupo_despesa_form.html', context)
