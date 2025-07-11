from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from .models.financeiro import DescricaoMovimentacaoFinanceira
from .forms import DescricaoMovimentacaoFinanceiraForm
from .tables import DescricaoMovimentacaoFinanceiraTable
from .filters import DescricaoMovimentacaoFinanceiraFilter

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
        return DescricaoMovimentacaoFinanceira.objects.filter(conta=empresa.conta)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        context['table'] = context.get('table')
        context['filter'] = context.get('filter')
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
        descricao.conta = empresa.conta
        descricao.created_by = self.request.user
        descricao.save()
        messages.success(self.request, 'Descrição cadastrada com sucesso!')
        return redirect('financeiro:lista_descricoes_movimentacao', empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

class DescricaoMovimentacaoFinanceiraUpdateView(LoginRequiredMixin, UpdateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'

    def _get_empresa_id_by_conta(self, conta):
        from medicos.models.base import Empresa
        empresa = Empresa.objects.filter(conta=conta).first()
        return empresa.id if empresa else None

    def form_valid(self, form):
        descricao = form.save(commit=False)
        if not descricao.conta:
            empresa_id = self.kwargs.get('empresa_id')
            from medicos.models.base import Empresa
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                descricao.conta = empresa.conta
            except Empresa.DoesNotExist:
                messages.error(self.request, f'Empresa com id {empresa_id} não existe.')
                return self.form_invalid(form)
        descricao.save()
        messages.success(self.request, 'Descrição atualizada com sucesso!')
        empresa_id = self._get_empresa_id_by_conta(descricao.conta)
        return redirect('financeiro:lista_descricoes_movimentacao', empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

    def get_success_url(self):
        empresa_id = self._get_empresa_id_by_conta(self.object.conta)
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})

class DescricaoMovimentacaoFinanceiraDeleteView(LoginRequiredMixin, DeleteView):
    model = DescricaoMovimentacaoFinanceira
    template_name = 'financeiro/descricao_movimentacao_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

    def get_success_url(self):
        # Garante que o redirect usa o empresa_id correto vinculado à conta da descrição
        empresa_id = None
        if hasattr(self, '_get_empresa_id_by_conta'):
            empresa_id = self._get_empresa_id_by_conta(self.object.conta)
        else:
            from medicos.models.base import Empresa
            empresa = Empresa.objects.filter(conta=self.object.conta).first()
            empresa_id = empresa.id if empresa else self.kwargs.get('empresa_id')
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})
