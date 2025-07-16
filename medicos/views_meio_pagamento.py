from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, DeleteView
from django_tables2.views import SingleTableView
from django.shortcuts import get_object_or_404
from medicos.models.financeiro import MeioPagamento, Conta
from medicos.models.base import Empresa
from .forms_meio_pagamento import MeioPagamentoForm

from medicos.tables_meio_pagamento import MeioPagamentoTable

class MeioPagamentoListView(SingleTableView):
    model = MeioPagamento
    table_class = MeioPagamentoTable
    template_name = 'cadastro/lista_meios_pagamento.html'
    paginate_by = 10

    def get_queryset(self):
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        self.empresa_id = empresa_id
        qs = MeioPagamento.objects.filter(empresa=empresa)
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(nome__icontains=nome)
        return qs

    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']) ou pelo parâmetro da URL.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete também 'titulo_pagina' para exibição do título padrão no header.
        - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
        """
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id') or self.request.session.get('empresa_id')
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Meios de Pagamento'
        return context

class MeioPagamentoCreateView(CreateView):
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/criar_meio_pagamento.html'

    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']) ou pelo parâmetro da URL.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete também 'titulo_pagina' para exibição do título padrão no header.
        - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
        """
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id') or self.request.session.get('empresa_id')
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Novo Meio de Pagamento'
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa_id = int(self.kwargs.get('empresa_id'))
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        form.instance.empresa = empresa
        return form

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        empresa = self.object.empresa
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        return reverse_lazy('medicos:empresas')

class MeioPagamentoUpdateView(UpdateView):
    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']) ou pelo parâmetro da URL.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete também 'titulo_pagina' para exibição do título padrão no header.
        - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
        """
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id') or self.request.session.get('empresa_id')
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Editar Meio de Pagamento'
        return context
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/editar_meio_pagamento.html'

    def get_success_url(self):
        empresa = self.object.empresa
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        else:
            return reverse_lazy('medicos:empresas')

class MeioPagamentoDeleteView(DeleteView):
    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']) ou pelo parâmetro da URL.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete também 'titulo_pagina' para exibição do título padrão no header.
        - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
        """
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id') or self.request.session.get('empresa_id')
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Excluir Meio de Pagamento'
        return context
    model = MeioPagamento
    template_name = 'cadastro/excluir_meio_pagamento.html'

    def get_success_url(self):
        empresa = self.object.empresa
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        else:
            return reverse_lazy('medicos:empresas')  # Redireciona para lista geral de empresas
