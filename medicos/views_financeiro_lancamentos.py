
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
        - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']).
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete também 'titulo_pagina' para exibição do título padrão no header.
        - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
        """
        context = super().get_context_data(**kwargs)
        empresa_id = self.request.session.get('empresa_id')
        if empresa_id:
            try:
                context['empresa'] = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                context['empresa'] = None
        else:
            context['empresa'] = None
        # O nome da empresa será exibido automaticamente pelo base_header.html
        context['titulo_pagina'] = 'Lançamentos'
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
        empresa_ctx = empresa_context(self.request)
        empresa = empresa_ctx.get('empresa')
        if not empresa:
            form.add_error(None, 'Nenhuma empresa selecionada.')
            return self.form_invalid(form)
        # Relaciona a movimentação à empresa selecionada
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
