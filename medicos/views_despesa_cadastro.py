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
from medicos.models.despesas import GrupoDespesa, ItemDespesa
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
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        sort = self.request.GET.get('sort', 'codigo')
        if sort not in ['codigo', 'descricao', '-codigo', '-descricao']:
            sort = 'codigo'
        # CORREÇÃO: Filtrar apenas grupos da empresa selecionada
        qs = GrupoDespesa.objects.filter(empresa=empresa).order_by(sort, 'descricao')
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


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        kwargs['empresa'] = empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        context.update({
            'empresa_id': empresa_id,
            'empresa': empresa,
            'grupos': GrupoDespesa.objects.filter(empresa=empresa),
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
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        # CORREÇÃO: Validar que o item pertence a um grupo da empresa selecionada
        return get_object_or_404(ItemDespesa, id=self.kwargs.get('item_id'), grupo_despesa__empresa=empresa)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        kwargs['empresa'] = empresa
        return kwargs

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
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        # CORREÇÃO: Validar que o item pertence a um grupo da empresa selecionada
        return get_object_or_404(ItemDespesa, id=self.kwargs.get('item_id'), grupo_despesa__empresa=empresa)

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
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        # CORREÇÃO: Filtrar apenas itens da empresa selecionada
        qs = ItemDespesa.objects.filter(grupo_despesa__empresa=empresa)
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
    # CORREÇÃO: Filtrar apenas grupos da empresa selecionada
    qs = GrupoDespesa.objects.filter(empresa=empresa).order_by(sort, 'descricao')
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
        # CORREÇÃO: Validar que o grupo pertence à empresa selecionada
        grupo = get_object_or_404(GrupoDespesa, id=grupo_id, empresa=empresa)
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
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        # CORREÇÃO: Filtrar apenas itens da empresa selecionada
        qs = ItemDespesa.objects.filter(grupo_despesa__empresa=empresa)
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
@login_required
def grupo_despesa_delete(request, empresa_id, grupo_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    # CORREÇÃO: Validar que o grupo pertence à empresa selecionada
    grupo = get_object_or_404(GrupoDespesa, id=grupo_id, empresa=empresa)
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de despesa excluído com sucesso!')
        return redirect('medicos:lista_grupos_despesa', empresa_id=empresa_id)
    return render(request, 'empresa/grupo_despesa_confirm_delete.html', {'grupo': grupo, 'empresa_id': empresa_id})


# API Views para importação de grupos de despesa

from django.http import JsonResponse
from django.db import transaction
import json

@login_required
def api_empresas_conta(request):
    """API para listar empresas da conta do usuário"""
    try:
        # Buscar empresas da conta do usuário atual
        conta_id = request.session.get('conta_id')
        if not conta_id:
            return JsonResponse({'success': False, 'message': 'Usuário sem conta ativa'})
        
        empresas = Empresa.objects.filter(conta_id=conta_id).values(
            'id', 'name', 'nome_fantasia', 'cnpj'
        )
        
        return JsonResponse({
            'success': True,
            'empresas': list(empresas)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao buscar empresas: {str(e)}'
        })

@login_required  
def verificar_dados_grupos_despesa(request, empresa_id):
    """API para verificar quantos grupos e itens existem na empresa de origem"""
    try:
        empresa_origem = get_object_or_404(Empresa, id=empresa_id)
        
        # Verificar se a empresa pertence à mesma conta do usuário
        conta_id = request.session.get('conta_id')
        if not conta_id or empresa_origem.conta_id != conta_id:
            return JsonResponse({
                'success': False,
                'message': 'Empresa não pertence à sua conta'
            })
        
        # Contar grupos e itens
        grupos = GrupoDespesa.objects.filter(empresa=empresa_origem)
        total_grupos = grupos.count()
        total_itens = sum(grupo.itens_despesa.count() for grupo in grupos)
        
        return JsonResponse({
            'success': True,
            'total_grupos': total_grupos,
            'total_itens': total_itens,
            'empresa_origem_nome': empresa_origem.nome_fantasia or empresa_origem.name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao verificar dados: {str(e)}'
        })

@login_required
def importar_grupos_despesa(request, empresa_id):
    """Importa grupos de despesa e itens de uma empresa para outra"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    try:
        data = json.loads(request.body)
        empresa_origem_id = data.get('empresa_origem_id')
        
        if not empresa_origem_id:
            return JsonResponse({'success': False, 'message': 'ID da empresa de origem é obrigatório'})
        
        empresa_destino = get_object_or_404(Empresa, id=empresa_id)
        empresa_origem = get_object_or_404(Empresa, id=empresa_origem_id)
        
        # Verificar se ambas as empresas pertencem à mesma conta do usuário
        conta_id = request.session.get('conta_id')
        if (not conta_id or 
            empresa_destino.conta_id != conta_id or 
            empresa_origem.conta_id != conta_id):
            return JsonResponse({
                'success': False,
                'message': 'Empresas não pertencem à sua conta'
            })
        
        # Verificar se não está tentando importar da mesma empresa
        if empresa_origem.id == empresa_destino.id:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível importar da mesma empresa'
            })
        
        grupos_importados = 0
        itens_importados = 0
        
        # Realizar importação dentro de uma transação
        with transaction.atomic():
            # Buscar todos os grupos da empresa de origem
            grupos_origem = GrupoDespesa.objects.filter(empresa=empresa_origem)
            
            for grupo_origem in grupos_origem:
                # Verificar se já existe um grupo com o mesmo código na empresa destino
                grupo_existente = GrupoDespesa.objects.filter(
                    empresa=empresa_destino,
                    codigo=grupo_origem.codigo
                ).first()
                
                if grupo_existente:
                    # Se existe, usar o grupo existente
                    grupo_destino = grupo_existente
                else:
                    # Se não existe, criar novo grupo
                    grupo_destino = GrupoDespesa.objects.create(
                        empresa=empresa_destino,
                        codigo=grupo_origem.codigo,
                        descricao=grupo_origem.descricao,
                        tipo_rateio=grupo_origem.tipo_rateio,
                        created_by=request.user
                    )
                    grupos_importados += 1
                
                # Importar itens do grupo
                itens_origem = grupo_origem.itens_despesa.all()
                for item_origem in itens_origem:
                    # Verificar se já existe um item com o mesmo código no grupo destino
                    item_existente = grupo_destino.itens_despesa.filter(
                        codigo=item_origem.codigo
                    ).first()
                    
                    if not item_existente:
                        # Se não existe, criar novo item
                        ItemDespesa.objects.create(
                            grupo_despesa=grupo_destino,
                            codigo=item_origem.codigo,
                            descricao=item_origem.descricao,
                            created_by=request.user
                        )
                        itens_importados += 1
        
        return JsonResponse({
            'success': True,
            'message': 'Importação realizada com sucesso',
            'grupos_importados': grupos_importados,
            'itens_importados': itens_importados
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro na importação: {str(e)}'
        })
