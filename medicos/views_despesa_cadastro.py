from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView
from medicos.models.base import Empresa
from medicos.models.despesas import GrupoDespesa
from .models import ItemDespesa
from medicos.forms import GrupoDespesaForm, ItemDespesaForm
from medicos.filters import GrupoDespesaFilter, ItemDespesaFilter
from medicos.tables import ItemDespesaTable

def main(request, empresa=None, menu_nome='Despesas', cenario_nome='Despesas'):
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano') or datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome
    request.session['cenario_nome'] = cenario_nome
    request.session['user_id'] = getattr(request.user, 'id', None)
    return {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome,
        'cenario_nome': cenario_nome,
        'empresa': empresa,
        'user': getattr(request, 'user', None),
    }


# Views

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class GrupoDespesaListView(ListView):
    model = GrupoDespesa
    template_name = 'empresa/lista_grupos_despesa.html'
    context_object_name = 'grupos'
    paginate_by = 20

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'codigo')
        if sort not in ['codigo', 'descricao', '-codigo', '-descricao']:
            sort = 'codigo'
        qs = GrupoDespesa.objects.all().order_by(sort, 'descricao')
        self.filter = GrupoDespesaFilter(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Grupos de Despesa'))
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        context['filter'] = getattr(self, 'filter', None)
        return context



@method_decorator(login_required, name='dispatch')
class GrupoDespesaCreateView(CreateView):
    model = GrupoDespesa
    form_class = GrupoDespesaForm
    template_name = 'empresa/grupo_despesa_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Novo Grupo de Despesa'))
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        return context

    def form_valid(self, form):
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        grupo = form.save(commit=False)
        grupo.conta = empresa.conta
        grupo.empresa = empresa  # Garante que o campo empresa nunca fique nulo
        grupo.save()
        messages.success(self.request, 'Grupo de despesas salvo com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa.id)

@method_decorator(login_required, name='dispatch')
class GrupoDespesaUpdateView(UpdateView):
    model = GrupoDespesa
    form_class = GrupoDespesaForm
    template_name = 'empresa/grupo_despesa_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(GrupoDespesa, id=self.kwargs.get('grupo_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Editar Grupo de Despesa'))
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        return context

    def form_valid(self, form):
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        grupo = form.save(commit=False)
        grupo.conta = empresa.conta
        grupo.empresa = empresa  # Garante que o campo empresa nunca fique nulo
        grupo.save()
        messages.success(self.request, 'Grupo de despesas salvo com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa.id)



from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView

@method_decorator(login_required, name='dispatch')
class ItemDespesaCreateView(CreateView):
    model = ItemDespesa
    form_class = ItemDespesaForm
    template_name = 'empresa/item_despesa_create.html'


    def get_initial(self):
        initial = super().get_initial()
        # Não há mais grupo_id na URL, inicialização padrão
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        context.update({
            'empresa_id': empresa_id,
            'empresa': empresa,
            'grupos': GrupoDespesa.objects.all(),
            'grupo': self.get_initial().get('grupo_despesa'),
            'edit_mode': False,
        })
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Novo Item de Despesa'))
        return context

    def form_valid(self, form):
        item = form.save(commit=False)
        item.grupo_despesa = form.cleaned_data['grupo_despesa']
        if self.request.user.is_authenticated:
            item.created_by = self.request.user
        if ItemDespesa.objects.filter(grupo_despesa=item.grupo_despesa, codigo=item.codigo).exists():
            form.add_error('codigo', 'Já existe um item com este código para este grupo de despesa.')
            return self.form_invalid(form)
        item.save()
        messages.success(self.request, 'Item de despesa cadastrado com sucesso!')
        return redirect('medicos:lista_itens_despesa', empresa_id=self.kwargs['empresa_id'])

@method_decorator(login_required, name='dispatch')
class ItemDespesaUpdateView(UpdateView):
    model = ItemDespesa
    form_class = ItemDespesaForm
    template_name = 'empresa/item_despesa_create.html'


    def get_object(self, queryset=None):
        return get_object_or_404(ItemDespesa, id=self.kwargs.get('item_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        context.update({
            'empresa_id': empresa_id,
            'empresa': empresa,
            'edit_mode': True,
        })
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Editar Item de Despesa'))
        return context

    def form_valid(self, form):
        item = form.save(commit=False)
        item.grupo_despesa = form.cleaned_data['grupo_despesa']
        if ItemDespesa.objects.filter(grupo_despesa=item.grupo_despesa, codigo=item.codigo).exclude(id=item.id).exists():
            form.add_error('codigo', 'Já existe um item com este código para este grupo de despesa.')
            return self.form_invalid(form)
        item.save()
        messages.success(self.request, 'Item de despesa atualizado com sucesso!')
        return redirect('medicos:lista_itens_despesa', empresa_id=self.kwargs['empresa_id'])

@method_decorator(login_required, name='dispatch')
class ItemDespesaDeleteView(DeleteView):
    model = ItemDespesa
    template_name = 'empresa/item_despesa_confirm_delete.html'


    def get_object(self, queryset=None):
        return get_object_or_404(ItemDespesa, id=self.kwargs.get('item_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        context.update({
            'empresa_id': empresa_id,
            'empresa': empresa,
        })
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Excluir Item de Despesa'))
        return context

    def get_success_url(self):
        return reverse_lazy('medicos:lista_itens_despesa', kwargs={'empresa_id': self.kwargs['empresa_id']})


class ItemDespesaListView(LoginRequiredMixin, SingleTableView):
    model = ItemDespesa
    table_class = ItemDespesaTable
    template_name = 'empresa/lista_itens_despesa.html'
    paginate_by = 20
    filterset_class = ItemDespesaFilter

    def get_table_data(self):
        qs = ItemDespesa.objects.all()
        self.filter = self.filterset_class(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        context.update({
            'empresa': empresa,
            'empresa_id': empresa_id,
            'titulo_pagina': 'Itens de Despesa',
            'filter': getattr(self, 'filter', None),
        })
        return context




@method_decorator(login_required, name='dispatch')
class GrupoDespesaDeleteView(DeleteView):
    model = GrupoDespesa
    template_name = 'empresa/grupo_despesa_confirm_delete.html'

    def get_object(self, queryset=None):
        return get_object_or_404(GrupoDespesa, id=self.kwargs.get('grupo_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        context.update(main(self.request, empresa=empresa, menu_nome='Despesas', cenario_nome='Excluir Grupo de Despesa'))
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        return context

    def get_success_url(self):
        return reverse_lazy('medicos:lista_grupos_despesa', kwargs={'empresa_id': self.kwargs['empresa_id']})

@login_required
def lista_grupos_despesa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    sort = request.GET.get('sort', 'codigo')
    if sort not in ['codigo', 'descricao', '-codigo', '-descricao']:
        sort = 'codigo'
    qs = GrupoDespesa.objects.all().order_by(sort, 'descricao')
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
        grupo = get_object_or_404(GrupoDespesa, id=grupo_id)
    form = GrupoDespesaForm(request.POST or None, instance=grupo)
    if request.method == 'POST' and form.is_valid():
        grupo = form.save(commit=False)
        grupo.conta = empresa.conta
        grupo.empresa = empresa  # Garante que o campo empresa nunca fique nulo
        grupo.save()
        messages.success(request, 'Grupo de despesas salvo com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa.id)
    context = {
        'empresa': empresa,
        'form': form,
        'grupo': grupo
    }
    return render(request, 'empresa/grupo_despesa_form.html', context)


# NOVA VIEW: Lista de Itens de Despesa com django-tables2 e paginação
from django.contrib.auth.mixins import LoginRequiredMixin

class ItemDespesaListView(LoginRequiredMixin, SingleTableView):
    model = ItemDespesa
    table_class = ItemDespesaTable
    template_name = 'empresa/lista_itens_despesa.html'
    paginate_by = 20
    filterset_class = ItemDespesaFilter

    def get_table_data(self):
        # Não há mais grupo_id na URL, sempre retorna todos os itens
        qs = ItemDespesa.objects.all()
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
def grupo_despesa_delete(request, empresa_id, grupo_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id)
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de despesa excluído com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa_id)
    return render(request, 'empresa/grupo_despesa_confirm_delete.html', {'grupo': grupo, 'empresa_id': empresa_id})
