
from django.db import models
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models.financeiro import Financeiro
from .tables_financeiro import FinanceiroTable
from .filters_financeiro import FinanceiroFilter
from .forms_financeiro import FinanceiroForm
from core.context_processors import empresa_context
from medicos.models.base import Empresa


class FinanceiroListView(SingleTableMixin, FilterView):
    """
    View para listagem de lançamentos financeiros.
    Exibe tabela filtrável e injeta empresa no contexto para o header.
    """
    model = Financeiro
    table_class = FinanceiroTable
    filterset_class = FinanceiroFilter
    template_name = 'financeiro/lista_lancamentos_financeiros.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - NÃO injete manualmente a variável 'empresa' no contexto. Ela já estará disponível via context processor.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete apenas 'titulo_pagina' e 'cenario_nome' para exibição correta no header.
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Lançamentos'
        context['cenario_nome'] = 'Financeiro'
        return context



class FinanceiroCreateView(CreateView):
    """
    View para criação de movimentação financeira.
    """
    model = Financeiro
    form_class = FinanceiroForm
    template_name = 'financeiro/form_movimentacao.html'

    def get_success_url(self):
        return reverse_lazy('financeiro:lancamentos', kwargs={'empresa_id': self.kwargs['empresa_id']})

    def form_valid(self, form):
        instance = form.save(commit=False)
        # Use o context processor para obter a empresa
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            form.add_error(None, 'Nenhuma empresa selecionada.')
            return self.form_invalid(form)
        instance.empresa = empresa
        instance.save()
        return super().form_valid(form)


class FinanceiroUpdateView(UpdateView):
    """
    View para atualização de movimentação financeira.
    """
    model = Financeiro
    form_class = FinanceiroForm
    template_name = 'financeiro/form_movimentacao.html'

    def get_success_url(self):
        return reverse_lazy('financeiro:lancamentos', kwargs={'empresa_id': self.kwargs['empresa_id']})


class FinanceiroDeleteView(DeleteView):
    """
    View para exclusão de movimentação financeira.
    """
    model = Financeiro
    template_name = 'financeiro/confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('financeiro:lancamentos', kwargs={'empresa_id': self.kwargs['empresa_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs['empresa_id']
        return context
