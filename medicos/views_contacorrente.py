from django.db import models
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models.conta_corrente import MovimentacaoContaCorrente
from .tables_contacorrente import MovimentacaoContaCorrenteTable
from .filters_contacorrente import MovimentacaoContaCorrenteFilter
from .forms_contacorrente import MovimentacaoContaCorrenteForm
from core.context_processors import empresa_context
from medicos.models.base import Empresa


class MovimentacaoContaCorrenteListView(SingleTableMixin, FilterView):
    """
    View para listagem de lançamentos bancários.
    Exibe tabela filtrável e injeta empresa no contexto para o header.

    REGRA OBRIGATÓRIA DE TITULAÇÃO DE PÁGINA:
    - O título da página deve ser passado via variável de contexto 'titulo_pagina' na view.
    - O template filho NÃO pode definir título fixo ou duplicado; o layout base exibe o título automaticamente.
    - Toda tela deve seguir este fluxo, sem exceções ou dubiedade.
    """
    model = MovimentacaoContaCorrente
    table_class = MovimentacaoContaCorrenteTable
    filterset_class = MovimentacaoContaCorrenteFilter
    template_name = 'conta_corrente/lista_lancamentos_bancarios.html'
    paginate_by = 25

    def get_queryset(self):
        """
        Filtra movimentações bancárias apenas da empresa selecionada.
        """
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            # Filtrar por empresa através dos relacionamentos disponíveis
            return MovimentacaoContaCorrente.objects.filter(
                models.Q(socio__empresa=empresa) |  # Através do sócio
                models.Q(descricao_movimentacao__empresa=empresa)  # Através da descrição
            ).distinct().order_by('-data_movimentacao')
        return MovimentacaoContaCorrente.objects.none()

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
        context['titulo_pagina'] = 'Lançamentos de conta corrente'
        context['cenario_nome'] = 'Conta Corrente'
        
        # Adiciona totalizações das movimentações filtradas
        from django.db.models import Sum, Count
        filterset = context['filter']
        if filterset.qs:
            totais = filterset.qs.aggregate(
                total_movimentacoes=Count('id'),
                total_entradas=Sum('valor', filter=models.Q(valor__gt=0)),  # Débitos bancários (entradas)
                total_saidas=Sum('valor', filter=models.Q(valor__lt=0)),   # Créditos bancários (saídas)
                saldo_total=Sum('valor')
            )
            
            # Garante que valores None sejam convertidos para 0
            context['total_movimentacoes'] = totais['total_movimentacoes'] or 0
            context['total_entradas'] = totais['total_entradas'] or 0
            context['total_saidas'] = abs(totais['total_saidas'] or 0)  # Valor absoluto para saídas
            context['saldo_total'] = totais['saldo_total'] or 0
        else:
            context['total_movimentacoes'] = 0
            context['total_entradas'] = 0
            context['total_saidas'] = 0
            context['saldo_total'] = 0
            
        return context


class MovimentacaoContaCorrenteCreateView(CreateView):
    """
    View para criação de movimentação bancária.
    """
    model = MovimentacaoContaCorrente
    form_class = MovimentacaoContaCorrenteForm
    template_name = 'conta_corrente/form_lancamento_bancario.html'

    def get_success_url(self):
        """Redireciona de volta para a listagem mantendo os filtros originais"""
        from django.http import QueryDict
        
        # Captura os parâmetros de filtro da query string atual
        filtros = self.request.GET.copy()
        
        # Remove parâmetros que não são filtros (se houver)
        parametros_filtro = ['tipo_valor', 'descricao_movimentacao', 'data_movimentacao_mes']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        # Constrói a URL de retorno com os filtros
        url_base = reverse_lazy('medicos:contacorrente_lancamentos', kwargs={'empresa_id': self.kwargs['empresa_id']})
        if filtros_limpos:
            return f"{url_base}?{filtros_limpos.urlencode()}"
        
        return url_base

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Novo Lançamento Bancário'
        context['cenario_nome'] = 'Conta Corrente'
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            form.add_error(None, 'Nenhuma empresa selecionada.')
            return self.form_invalid(form)
        # A relação com a empresa é feita através do sócio ou descrição_movimentacao
        instance.save()
        return super().form_valid(form)


class MovimentacaoContaCorrenteUpdateView(UpdateView):
    """
    View para atualização de movimentação bancária.
    """
    model = MovimentacaoContaCorrente
    form_class = MovimentacaoContaCorrenteForm
    template_name = 'conta_corrente/form_lancamento_bancario.html'

    def get_success_url(self):
        """Redireciona de volta para a listagem mantendo os filtros originais"""
        from django.http import QueryDict
        
        # Captura os parâmetros de filtro da query string atual
        filtros = self.request.GET.copy()
        
        # Remove parâmetros que não são filtros (se houver)
        parametros_filtro = ['tipo_valor', 'descricao_movimentacao', 'data_movimentacao_mes']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        # Constrói a URL de retorno com os filtros
        url_base = reverse_lazy('medicos:contacorrente_lancamentos', kwargs={'empresa_id': self.kwargs['empresa_id']})
        if filtros_limpos:
            return f"{url_base}?{filtros_limpos.urlencode()}"
        
        return url_base

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Lançamento Bancário'
        context['cenario_nome'] = 'Conta Corrente'
        return context


class MovimentacaoContaCorrenteDeleteView(DeleteView):
    """
    View para exclusão de movimentação bancária.
    """
    model = MovimentacaoContaCorrente
    template_name = 'conta_corrente/confirm_delete_lancamento.html'

    def get_success_url(self):
        """Redireciona de volta para a listagem mantendo os filtros originais"""
        from django.http import QueryDict
        
        # Captura os parâmetros de filtro da query string atual
        filtros = self.request.GET.copy()
        
        # Remove parâmetros que não são filtros (se houver)
        parametros_filtro = ['tipo_valor', 'descricao_movimentacao', 'data_movimentacao_mes']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        # Constrói a URL de retorno com os filtros
        url_base = reverse_lazy('medicos:contacorrente_lancamentos', kwargs={'empresa_id': self.kwargs['empresa_id']})
        if filtros_limpos:
            return f"{url_base}?{filtros_limpos.urlencode()}"
        
        return url_base

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs['empresa_id']
        context['titulo_pagina'] = 'Excluir Lançamento Bancário'
        context['cenario_nome'] = 'Conta Corrente'
        return context
