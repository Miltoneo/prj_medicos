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
        qs = MeioPagamento.objects.filter(conta=empresa.conta)
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(nome__icontains=nome)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.empresa_id
        context['titulo_pagina'] = 'Meios de Pagamento'
        return context

class MeioPagamentoCreateView(CreateView):
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/criar_meio_pagamento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
        context['titulo_pagina'] = 'Novo Meio de Pagamento'
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa_id = int(self.kwargs.get('empresa_id'))
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        conta = empresa.conta
        form.instance.conta = conta
        return form

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        empresa = Empresa.objects.filter(conta=self.object.conta).first()
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        return reverse_lazy('medicos:empresas')

class MeioPagamentoUpdateView(UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Meio de Pagamento'
        return context
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/editar_meio_pagamento.html'

    def get_success_url(self):
        conta = self.object.conta
        empresa = conta.empresas.first() if conta else None
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.id})
        else:
            return reverse_lazy('medicos:empresas')

class MeioPagamentoDeleteView(DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Excluir Meio de Pagamento'
        return context
    model = MeioPagamento
    template_name = 'cadastro/excluir_meio_pagamento.html'

    def get_success_url(self):
        # Tenta obter a primeira empresa vinculada à conta
        conta = self.object.conta
        empresa = conta.empresas.first() if conta else None
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.id})
        else:
            return reverse_lazy('medicos:empresas')  # Redireciona para lista geral de empresas
