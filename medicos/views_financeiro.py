from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models.financeiro import DescricaoMovimentacaoFinanceira
from .forms import DescricaoMovimentacaoFinanceiraForm

class DescricaoMovimentacaoFinanceiraListView(LoginRequiredMixin, ListView):
    model = DescricaoMovimentacaoFinanceira
    template_name = 'financeiro/lista_descricoes_movimentacao.html'
    context_object_name = 'descricoes'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.kwargs.get('empresa_id')
        return DescricaoMovimentacaoFinanceira.objects.filter(conta_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

class DescricaoMovimentacaoFinanceiraCreateView(LoginRequiredMixin, CreateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'

    def form_valid(self, form):
        empresa_id = self.kwargs.get('empresa_id')
        descricao = form.save(commit=False)
        descricao.conta_id = empresa_id
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

    def get_success_url(self):
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': self.kwargs.get('empresa_id')})

class DescricaoMovimentacaoFinanceiraDeleteView(LoginRequiredMixin, DeleteView):
    model = DescricaoMovimentacaoFinanceira
    template_name = 'financeiro/descricao_movimentacao_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

    def get_success_url(self):
        return reverse_lazy('financeiro:lista_descricoes_movimentacao', kwargs={'empresa_id': self.kwargs.get('empresa_id')})
