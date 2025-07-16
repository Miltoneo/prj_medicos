# =========================
# Imports
# =========================
# Python Standard
from datetime import datetime

# Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

# Third Party
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

# Local
from .models.financeiro import DescricaoMovimentacaoFinanceira
from .forms import DescricaoMovimentacaoFinanceiraForm
from .tables import DescricaoMovimentacaoFinanceiraTable
from .filters import DescricaoMovimentacaoFinanceiraFilter

# =========================
# Helpers
# =========================
def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    """
    Helper para contexto global das views financeiras.
    """
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'Financeiro'
    request.session['cenario_nome'] = cenario_nome or 'Financeiro'
    request.session['user_id'] = request.user.id if hasattr(request, 'user') else None
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Financeiro',
        'empresa': empresa,
        'user': getattr(request, 'user', None),
    }
    return context

##############################
# Views
##############################

class DescricaoMovimentacaoFinanceiraListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = DescricaoMovimentacaoFinanceira
    table_class = DescricaoMovimentacaoFinanceiraTable
    template_name = 'financeiro/lista_descricoes_movimentacao.html'
    filterset_class = DescricaoMovimentacaoFinanceiraFilter
    context_object_name = 'descricoes'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return DescricaoMovimentacaoFinanceira.objects.none()
        return DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        main_context = main(self.request, empresa=empresa, menu_nome='Financeiro', cenario_nome='Lista de Movimentações')
        context.update(main_context)
        context['empresa'] = empresa
        context['titulo_pagina'] = 'Descrições de Movimentação Financeira'
        context['empresa_id'] = empresa_id
        context['table'] = context.get('table')
        context['filter'] = context.get('filter')
        # Garantir que empresa e titulo_pagina estejam sempre presentes
        if 'empresa' not in context or not context['empresa']:
            context['empresa'] = context.get('empresa')
        if 'titulo_pagina' not in context or not context['titulo_pagina']:
            context['titulo_pagina'] = 'Movimentação Financeira'
        return context

class DescricaoMovimentacaoFinanceiraCreateView(LoginRequiredMixin, CreateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'

    def form_valid(self, form):
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            messages.error(self.request, f'Empresa com id {empresa_id} não existe.')
            return self.form_invalid(form)
        form.empresa = empresa
        descricao = form.save(commit=False)
        descricao.created_by = self.request.user
        descricao.save()
        messages.success(self.request, 'Descrição cadastrada com sucesso!')
        return redirect('financeiro:lista_descricoes_movimentacao', empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        main_context = main(self.request, empresa=empresa, menu_nome='Financeiro', cenario_nome='Nova Movimentação')
        context.update(main_context)
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Nova Descrição de Movimentação Financeira'
        if 'empresa' not in context or not context['empresa']:
            context['empresa'] = context.get('empresa')
        if 'titulo_pagina' not in context or not context['titulo_pagina']:
            context['titulo_pagina'] = 'Movimentação Financeira'
        return context

class DescricaoMovimentacaoFinanceiraUpdateView(LoginRequiredMixin, UpdateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'


    def form_valid(self, form):
        descricao = form.save(commit=False)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            descricao.empresa = empresa
        except Empresa.DoesNotExist:
            messages.error(self.request, f'Empresa com id {empresa_id} não existe.')
            return self.form_invalid(form)
        descricao.save()
        messages.success(self.request, 'Descrição atualizada com sucesso!')
        return redirect('financeiro:lista_descricoes_movimentacao', empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        main_context = main(self.request, empresa=empresa, menu_nome='Financeiro', cenario_nome='Editar Movimentação')
        context.update(main_context)
        context['empresa'] = empresa
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Editar Descrição de Movimentação Financeira'
        if 'empresa' not in context or not context['empresa']:
            context['empresa'] = context.get('empresa')
        if 'titulo_pagina' not in context or not context['titulo_pagina']:
            context['titulo_pagina'] = 'Movimentação Financeira'
        return context

    def get_success_url(self):
        empresa_id = self.object.empresa.id
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})

class DescricaoMovimentacaoFinanceiraDeleteView(LoginRequiredMixin, DeleteView):
    model = DescricaoMovimentacaoFinanceira
    template_name = 'financeiro/descricao_movimentacao_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        main_context = main(self.request, empresa=empresa, menu_nome='Financeiro', cenario_nome='Excluir Movimentação')
        context.update(main_context)
        context['empresa_atual'] = empresa
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Excluir Descrição de Movimentação Financeira'
        if 'empresa_atual' not in context or not context['empresa_atual']:
            context['empresa_atual'] = context.get('empresa')
        if 'titulo_pagina' not in context or not context['titulo_pagina']:
            context['titulo_pagina'] = 'Movimentação Financeira'
        return context

    def get_success_url(self):
        empresa_id = self.object.empresa.id
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})

class DescricaoMovimentacaoFinanceiraListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = DescricaoMovimentacaoFinanceira
    table_class = DescricaoMovimentacaoFinanceiraTable
    template_name = 'financeiro/lista_descricoes_movimentacao.html'
    filterset_class = DescricaoMovimentacaoFinanceiraFilter
    context_object_name = 'descricoes'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return DescricaoMovimentacaoFinanceira.objects.none()
        return DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        context['empresa_id'] = empresa_id
        context['empresa'] = empresa
        context['table'] = context.get('table')
        context['filter'] = context.get('filter')
        context['mes_ano'] = self.request.session.get('mes_ano')
        context['titulo_pagina'] = 'Descrições de Movimentação Financeira'
        return context

class DescricaoMovimentacaoFinanceiraCreateView(LoginRequiredMixin, CreateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'

    def form_valid(self, form):
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            messages.error(self.request, f'Empresa com id {empresa_id} não existe.')
            return self.form_invalid(form)
        descricao = form.save(commit=False)
        descricao.empresa = empresa
        descricao.created_by = self.request.user
        descricao.save()
        messages.success(self.request, 'Descrição cadastrada com sucesso!')
        return redirect('financeiro:lista_descricoes_movimentacao', empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        context['empresa_id'] = empresa_id
        context['empresa'] = empresa
        context['titulo_pagina'] = 'Nova Descrição de Movimentação Financeira'
        return context

class DescricaoMovimentacaoFinanceiraUpdateView(LoginRequiredMixin, UpdateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'


    def form_valid(self, form):
        descricao = form.save(commit=False)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            descricao.empresa = empresa
        except Empresa.DoesNotExist:
            messages.error(self.request, f'Empresa com id {empresa_id} não existe.')
            return self.form_invalid(form)
        descricao.save()
        messages.success(self.request, 'Descrição atualizada com sucesso!')
        return redirect('financeiro:lista_descricoes_movimentacao', empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        context['empresa_id'] = empresa_id
        context['empresa'] = empresa
        context['titulo_pagina'] = 'Editar Descrição de Movimentação Financeira'
        return context

    def get_success_url(self):
        empresa_id = self._get_empresa_id_by_conta(self.object.conta)
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})

class DescricaoMovimentacaoFinanceiraDeleteView(LoginRequiredMixin, DeleteView):
    model = DescricaoMovimentacaoFinanceira
    template_name = 'financeiro/descricao_movimentacao_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        context['empresa_id'] = empresa_id
        context['empresa'] = empresa
        context['titulo_pagina'] = 'Excluir Descrição de Movimentação Financeira'
        return context

    def get_success_url(self):
        empresa_id = self.object.empresa.id
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})
