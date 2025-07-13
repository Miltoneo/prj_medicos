from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from medicos.models.financeiro import MeioPagamento, Conta
from medicos.models.base import Empresa
from .forms_meio_pagamento import MeioPagamentoForm

class MeioPagamentoListView(ListView):
    model = MeioPagamento
    template_name = 'cadastro/lista_meios_pagamento.html'
    context_object_name = 'meios_pagamento'

    def get_queryset(self):
        conta_id = self.kwargs.get('empresa_id')
        self.empresa_id = conta_id
        return MeioPagamento.objects.filter(conta_id=conta_id)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.empresa_id
        return context

class MeioPagamentoCreateView(CreateView):
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/criar_meio_pagamento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_id'] = self.kwargs.get('empresa_id')
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
        return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': self.object.conta_id})

class MeioPagamentoUpdateView(UpdateView):
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/editar_meio_pagamento.html'

    def get_success_url(self):
        return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': self.object.conta_id})

class MeioPagamentoDeleteView(DeleteView):
    model = MeioPagamento
    template_name = 'cadastro/excluir_meio_pagamento.html'

    def get_success_url(self):
        return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': self.object.conta_id})
