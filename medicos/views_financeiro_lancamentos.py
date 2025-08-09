
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

    REGRA OBRIGATÓRIA DE TITULAÇÃO DE PÁGINA:
    - O título da página deve ser passado via variável de contexto 'titulo_pagina' na view.
    - O template filho NÃO pode definir título fixo ou duplicado; o layout base exibe o título automaticamente.
    - Toda tela deve seguir este fluxo, sem exceções ou dubiedade.
    - Exemplo correto:
        context['titulo_pagina'] = 'Lançamentos de movimentações financeiras'
    - Exemplo de exibição no layout:
        <h4 class="fw-bold text-primary">Título: {{ titulo_pagina }}</h4>
    Fonte: medicos/templates/layouts/base_cenario_financeiro.html, linhas 15-25; medicos/views_financeiro_lancamentos.py, método get_context_data.
    """
    model = Financeiro
    table_class = FinanceiroTable
    filterset_class = FinanceiroFilter
    template_name = 'financeiro/lista_lancamentos_financeiros.html'
    paginate_by = 25

    def get_queryset(self):
        """
        Filtra movimentações financeiras apenas da empresa selecionada.
        """
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            # Filtra através do campo socio que pertence à empresa
            return Financeiro.objects.filter(socio__empresa=empresa).order_by('-data_movimentacao')
        return Financeiro.objects.none()

    def get_filterset(self, filterset_class):
        """
        Só aplica o filtro padrão de mês/ano se não houver nenhum filtro na query string.
        """
        import datetime
        data = self.request.GET.copy()
        # Se não há nenhum filtro na query string, aplica o mês atual
        if not data and not self.request.GET.urlencode():
            today = datetime.date.today()
            data['data_movimentacao_mes'] = today.strftime('%Y-%m')
        return filterset_class(data, queryset=self.get_queryset(), request=self.request)

    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - NÃO injete manualmente a variável 'empresa' no contexto. Ela já estará disponível via context processor.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete apenas 'titulo_pagina' e 'cenario_nome' para exibição correta no header.
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Lançamentos de movimentações financeiras'
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            form.add_error(None, 'Nenhuma empresa selecionada.')
            return self.form_invalid(form)
        # O campo empresa não existe no modelo Financeiro
        # A relação com a empresa é feita através do campo socio
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs

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
