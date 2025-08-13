from django.views.generic import CreateView, UpdateView
from django_tables2.views import SingleTableMixin
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from .models.financeiro import AplicacaoFinanceira
from .forms_aplicacoes_financeiras import AplicacaoFinanceiraForm
from .tables_aplicacoes_financeiras import AplicacaoFinanceiraTable

class AplicacaoFinanceiraListView(LoginRequiredMixin, SingleTableMixin, ListView):
    model = AplicacaoFinanceira
    table_class = AplicacaoFinanceiraTable
    template_name = 'financeiro/aplicacoes_financeiras_list.html'
    paginate_by = 20

    def get_table_data(self):
        from medicos.models.base import Empresa
        ano = self.request.GET.get('ano')
        try:
            ano_str = str(ano).replace('.', '').replace(',', '').strip()
            ano_int = int(ano_str)
        except (TypeError, ValueError):
            ano_int = timezone.now().year
        empresa_id = self.kwargs.get('empresa_id')
        if not empresa_id:
            return AplicacaoFinanceira.objects.none()
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return AplicacaoFinanceira.objects.none()
        return AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano_int
        ).order_by('-data_referencia')

    def get_table(self, **kwargs):
        """Passa o contexto da request para a tabela poder acessar os filtros"""
        table = super().get_table(**kwargs)
        table.context = {'request': self.request}
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ano_param = self.request.GET.get('ano')
        try:
            ano_str = str(ano_param).replace('.', '').replace(',', '').strip()
            ano = int(ano_str)
        except (TypeError, ValueError):
            ano = timezone.now().year
        context['ano'] = ano
        context['anos'] = list(range(timezone.now().year - 5, timezone.now().year + 2))
        context['titulo_pagina'] = 'Aplicações Financeiras'
        context['cenario_nome'] = 'Financeiro'
        context['menu_nome'] = 'aplicacoes_financeiras'
        context['empresa_id'] = self.kwargs.get('empresa_id')
        return context

class AplicacaoFinanceiraCreateView(LoginRequiredMixin, CreateView):
    model = AplicacaoFinanceira
    form_class = AplicacaoFinanceiraForm
    template_name = 'financeiro/aplicacoes_financeiras_form.html'

    def get_success_url(self):
        """Redireciona de volta para a listagem mantendo os filtros originais"""
        from django.http import QueryDict
        
        # Captura os parâmetros de filtro da query string atual
        filtros = self.request.GET.copy()
        
        # Remove parâmetros que não são filtros (se houver)
        parametros_filtro = ['ano']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        # Constrói a URL de retorno com os filtros
        url_base = reverse_lazy('medicos:aplicacoes_financeiras', kwargs={'empresa_id': self.kwargs.get('empresa_id')})
        if filtros_limpos:
            return f"{url_base}?{filtros_limpos.urlencode()}"
        
        return url_base

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nova Aplicação Financeira'
        context['cenario_nome'] = 'Financeiro'
        context['menu_nome'] = 'aplicacoes_financeiras'
        context['empresa_id'] = self.kwargs.get('empresa_id')
        
        # Adiciona informações sobre os filtros para debug/referência
        filtros_ativos = {}
        for param in ['ano']:
            if param in self.request.GET:
                filtros_ativos[param] = self.request.GET[param]
        context['filtros_originais'] = filtros_ativos
        
        return context

    def form_valid(self, form):
        from django.db import IntegrityError
        from django.contrib import messages
        empresa_id = self.kwargs.get('empresa_id')
        from medicos.models.base import Empresa
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                form.instance.empresa = empresa
            except Empresa.DoesNotExist:
                pass
        form.instance.created_by = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('data_referencia', 'Já existe uma aplicação financeira para este mês/ano nesta empresa.')
            messages.error(self.request, 'Já existe uma aplicação financeira para este mês/ano nesta empresa.')
            return self.form_invalid(form)

class AplicacaoFinanceiraUpdateView(LoginRequiredMixin, UpdateView):
    model = AplicacaoFinanceira
    form_class = AplicacaoFinanceiraForm
    template_name = 'financeiro/aplicacoes_financeiras_form.html'

    def get_success_url(self):
        """Redireciona de volta para a listagem mantendo os filtros originais"""
        from django.http import QueryDict
        
        # Captura os parâmetros de filtro da query string atual
        filtros = self.request.GET.copy()
        
        # Remove parâmetros que não são filtros (se houver)
        parametros_filtro = ['ano']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        # Determina o empresa_id
        empresa_id = self.kwargs.get('empresa_id')
        if not empresa_id or str(empresa_id).strip() == '':
            empresa_id = getattr(self.object, 'empresa_id', None)
        if not empresa_id:
            raise Exception('empresa_id não encontrado para redirecionamento')
        
        # Constrói a URL de retorno com os filtros
        url_base = reverse_lazy('medicos:aplicacoes_financeiras', kwargs={'empresa_id': int(empresa_id)})
        if filtros_limpos:
            return f"{url_base}?{filtros_limpos.urlencode()}"
        
        return url_base

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Aplicação Financeira'
        context['cenario_nome'] = 'Financeiro'
        context['menu_nome'] = 'aplicacoes_financeiras'
        context['empresa_id'] = self.kwargs.get('empresa_id')
        
        # Adiciona informações sobre os filtros para debug/referência
        filtros_ativos = {}
        for param in ['ano']:
            if param in self.request.GET:
                filtros_ativos[param] = self.request.GET[param]
        context['filtros_originais'] = filtros_ativos
        
        return context

    def get_queryset(self):
        from medicos.models.base import Empresa
        empresa_id = self.kwargs.get('empresa_id')
        if not empresa_id:
            return AplicacaoFinanceira.objects.none()
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return AplicacaoFinanceira.objects.none()
        return AplicacaoFinanceira.objects.filter(empresa=empresa)
