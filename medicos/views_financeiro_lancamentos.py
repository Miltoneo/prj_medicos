
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models
from .models.financeiro import Financeiro, TIPO_MOVIMENTACAO_CONTA_CREDITO, TIPO_MOVIMENTACAO_CONTA_DEBITO
from .tables_financeiro import FinanceiroTable
from .filters_financeiro import FinanceiroFilter
from .forms_financeiro import FinanceiroForm
from core.context_processors import empresa_context


class FinanceiroListView(SingleTableMixin, FilterView):
    model = Financeiro
    table_class = FinanceiroTable
    filterset_class = FinanceiroFilter
    template_name = 'financeiro/lista_lancamentos_financeiros.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_ctx = empresa_context(self.request)
        context['empresa_atual'] = empresa_ctx.get('empresa')
        return context


class FinanceiroCreateView(CreateView):
    model = Financeiro
    form_class = FinanceiroForm
    template_name = 'financeiro/form_movimentacao.html'
    success_url = reverse_lazy('financeiro:lancamentos')

class FinanceiroUpdateView(UpdateView):
    model = Financeiro
    form_class = FinanceiroForm
    template_name = 'financeiro/form_movimentacao.html'
    success_url = reverse_lazy('financeiro:lancamentos')

class FinanceiroDeleteView(DeleteView):
    model = Financeiro
    template_name = 'financeiro/confirm_delete.html'
    success_url = reverse_lazy('financeiro:lancamentos')
