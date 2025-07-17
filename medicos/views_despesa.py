from datetime import datetime
# Imports: Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# Imports: Third Party
from django_tables2 import SingleTableView
# Imports: Local
from medicos.models.base import Empresa
from medicos.models.despesas import GrupoDespesa
from .models import ItemDespesa, GrupoDespesa
from medicos.forms import GrupoDespesaForm, ItemDespesaForm
from medicos.filters import GrupoDespesaFilter, ItemDespesaFilter
from medicos.tables import ItemDespesaTable

def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'Despesas'
    request.session['cenario_nome'] = cenario_nome or 'Despesas'
    request.session['user_id'] = request.user.id if hasattr(request, 'user') else None
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Despesas',
        'cenario_nome': cenario_nome or 'Despesas',
        'empresa': empresa,
        'user': getattr(request, 'user', None),
    }
    return context


# Views
@login_required
def lista_grupos_despesa(request, empresa_id):
    from core.context_processors import empresa_context
    empresa = empresa_context(request).get('empresa')
    sort = request.GET.get('sort', 'codigo')
    if sort not in ['codigo', 'descricao', '-codigo', '-descricao']:
        sort = 'codigo'
    qs = GrupoDespesa.objects.filter(conta=empresa.conta).order_by(sort, 'descricao')
    filtro = GrupoDespesaFilter(request.GET, queryset=qs)
    grupos_list = filtro.qs
    paginator = Paginator(grupos_list, 20)
    page_number = request.GET.get('page')
    grupos = paginator.get_page(page_number)
    context = main(request, empresa=empresa, menu_nome='Despesas', cenario_nome='Grupos de Despesa')
    context['grupos'] = grupos
    context['filter'] = filtro
    return render(request, 'empresa/lista_grupos_despesa.html', context)


@login_required
def grupo_despesa_edit(request, empresa_id, grupo_id):
    from core.context_processors import empresa_context
    empresa = empresa_context(request).get('empresa')
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
    context = main(request, empresa=empresa, menu_nome='Despesas', cenario_nome='Editar Grupo de Despesa')
    context['form'] = form
    context['grupo'] = grupo
    return render(request, 'empresa/grupo_despesa_form.html', context)


@login_required
def item_despesa_create(request, empresa_id, grupo_id):
    from core.context_processors import empresa_context
    empresa = empresa_context(request).get('empresa')
    grupos = GrupoDespesa.objects.filter(conta=empresa.conta)
    grupo_inicial = None
    if int(grupo_id) != 0:
        grupo_inicial = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    if request.method == 'POST':
        form = ItemDespesaForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.grupo = form.cleaned_data['grupo']
            item.conta = item.grupo.conta
            if request.user.is_authenticated:
                item.created_by = request.user
            # Validação: código único por conta
            if ItemDespesa.objects.filter(conta=item.conta, codigo=item.codigo).exists():
                form.add_error('codigo', 'Já existe um item com este código para esta conta.')
            else:
                item.save()
                messages.success(request, 'Item de despesa cadastrado com sucesso!')
                # Redireciona para o grupo correto
                return redirect('medicos:lista_itens_despesa', empresa_id=empresa_id, grupo_id=item.grupo.id)
    else:
        initial = {'grupo': grupo_inicial} if grupo_inicial else {}
        form = ItemDespesaForm(initial=initial)
    context = main(request, empresa=empresa, menu_nome='Despesas', cenario_nome='Novo Item de Despesa')
    context['form'] = form
    context['grupo'] = grupo_inicial
    context['empresa_id'] = empresa_id
    context['grupos'] = grupos
    return render(request, 'empresa/item_despesa_create.html', context)


class ItemDespesaListView(LoginRequiredMixin, SingleTableView):
    model = ItemDespesa
    table_class = ItemDespesaTable
    template_name = 'empresa/lista_itens_despesa.html'
    paginate_by = 20
    filterset_class = ItemDespesaFilter

    def get_table_data(self):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        qs = ItemDespesa.objects.filter(conta=empresa.conta) if empresa else ItemDespesa.objects.none()
        self.filter = self.filterset_class(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        main_context = main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Itens de Despesa')
        context.update(main_context)
        context['empresa_id'] = empresa.id if empresa else None
        context['filter'] = getattr(self, 'filter', None)
        return context


@login_required
def item_despesa_edit(request, empresa_id, grupo_id, item_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    item = get_object_or_404(ItemDespesa, id=item_id, grupo=grupo)
    if request.method == 'POST':
        form = ItemDespesaForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.grupo = form.cleaned_data['grupo']
            item.conta = item.grupo.conta
            # Validação: código único por conta
            if ItemDespesa.objects.filter(conta=item.conta, codigo=item.codigo).exclude(id=item.id).exists():
                form.add_error('codigo', 'Já existe um item com este código para esta conta.')
            else:
                item.save()
                messages.success(request, 'Item de despesa atualizado com sucesso!')
                return redirect('medicos:lista_itens_despesa', empresa_id=empresa_id, grupo_id=item.grupo.pk)
    else:
        form = ItemDespesaForm(instance=item)
    context = main(request, empresa=empresa, menu_nome='Despesas', cenario_nome='Editar Item de Despesa')
    context['form'] = form
    context['grupo'] = grupo
    context['empresa_id'] = empresa_id
    context['edit_mode'] = True
    return render(request, 'empresa/item_despesa_create.html', context)


@login_required
def item_despesa_delete(request, empresa_id, grupo_id, item_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    item = get_object_or_404(ItemDespesa, id=item_id, grupo=grupo)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item de despesa excluído com sucesso!')
        return redirect('medicos:lista_itens_despesa', empresa_id=empresa_id, grupo_id=grupo_id)
    context = main(request, empresa=empresa, menu_nome='Despesas', cenario_nome='Excluir Item de Despesa')
    context['item'] = item
    context['empresa_id'] = empresa_id
    context['grupo_id'] = grupo_id
    return render(request, 'empresa/item_despesa_confirm_delete.html', context)


@login_required
def grupo_despesa_delete(request, empresa_id, grupo_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de despesa excluído com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa_id)
    context = main(request, empresa=empresa, menu_nome='Despesas', cenario_nome='Excluir Grupo de Despesa')
    context['grupo'] = grupo
    context['empresa_id'] = empresa_id
    return render(request, 'empresa/grupo_despesa_confirm_delete.html', context)

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
        'request': request,
        'titulo_pagina': 'Grupos de Despesa',
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

@login_required
def item_despesa_create(request, empresa_id, grupo_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    grupos = GrupoDespesa.objects.filter(conta=empresa.conta)
    grupo_inicial = None
    if int(grupo_id) != 0:
        grupo_inicial = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    if request.method == 'POST':
        form = ItemDespesaForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.grupo = form.cleaned_data['grupo']
            item.conta = item.grupo.conta
            if request.user.is_authenticated:
                item.created_by = request.user
            # Validação: código único por conta
            if ItemDespesa.objects.filter(conta=item.conta, codigo=item.codigo).exists():
                form.add_error('codigo', 'Já existe um item com este código para esta conta.')
            else:
                item.save()
                messages.success(request, 'Item de despesa cadastrado com sucesso!')
                # Redireciona para o grupo correto
                return redirect('medicos:lista_itens_despesa', empresa_id=empresa_id, grupo_id=item.grupo.id)
    else:
        initial = {'grupo': grupo_inicial} if grupo_inicial else {}
        form = ItemDespesaForm(initial=initial)
    context = {
        'form': form,
        'grupo': grupo_inicial,
        'empresa_id': empresa_id,
        'grupos': grupos,
        'request': request
    }
    return render(request, 'empresa/item_despesa_create.html', context)

# NOVA VIEW: Lista de Itens de Despesa com django-tables2 e paginação
from django.contrib.auth.mixins import LoginRequiredMixin

class ItemDespesaListView(LoginRequiredMixin, SingleTableView):
    model = ItemDespesa
    table_class = ItemDespesaTable
    template_name = 'empresa/lista_itens_despesa.html'
    paginate_by = 20
    filterset_class = ItemDespesaFilter

    def get_table_data(self):
        empresa_id = self.kwargs.get('empresa_id')
        empresa = Empresa.objects.get(pk=empresa_id)
        qs = ItemDespesa.objects.filter(conta=empresa.conta)
        # Aplica filtro se houver
        self.filter = self.filterset_class(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = Empresa.objects.get(pk=empresa_id)
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Itens de Despesa'
        context['filter'] = getattr(self, 'filter', None)
        return context

@login_required
def item_despesa_edit(request, empresa_id, grupo_id, item_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    item = get_object_or_404(ItemDespesa, id=item_id, grupo=grupo)
    if request.method == 'POST':
        form = ItemDespesaForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.grupo = form.cleaned_data['grupo']
            item.conta = item.grupo.conta
            # Validação: código único por conta
            if ItemDespesa.objects.filter(conta=item.conta, codigo=item.codigo).exclude(id=item.id).exists():
                form.add_error('codigo', 'Já existe um item com este código para esta conta.')
            else:
                item.save()
                messages.success(request, 'Item de despesa atualizado com sucesso!')
                return redirect('medicos:lista_itens_despesa', empresa_id=empresa_id, grupo_id=item.grupo.pk)
    else:
        form = ItemDespesaForm(instance=item)
    return render(request, 'empresa/item_despesa_create.html', {'form': form, 'grupo': grupo, 'empresa_id': empresa_id, 'edit_mode': True})

@login_required
def item_despesa_delete(request, empresa_id, grupo_id, item_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    item = get_object_or_404(ItemDespesa, id=item_id, grupo=grupo)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item de despesa excluído com sucesso!')
        return redirect('medicos:lista_itens_despesa', empresa_id=empresa_id, grupo_id=grupo_id)
    return render(request, 'empresa/item_despesa_confirm_delete.html', {'item': item, 'empresa_id': empresa_id, 'grupo_id': grupo_id})

@login_required
def grupo_despesa_delete(request, empresa_id, grupo_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, conta=empresa.conta)
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de despesa excluído com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa_id)
    return render(request, 'empresa/grupo_despesa_confirm_delete.html', {'grupo': grupo, 'empresa_id': empresa_id})
