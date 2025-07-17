from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from medicos.models.fiscal import NotaFiscal
from .tables_recebimento_notafiscal import NotaFiscalRecebimentoTable
from .filters_recebimento_notafiscal import NotaFiscalRecebimentoFilter
from .forms_notafiscal import NotaFiscalForm

@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoListView(SingleTableMixin, FilterView):
    model = NotaFiscal
    table_class = NotaFiscalRecebimentoTable
    filterset_class = NotaFiscalRecebimentoFilter
    template_name = 'financeiro/recebimento_notas_fiscais.html'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return NotaFiscal.objects.none()
        return NotaFiscal.objects.filter(empresa_destinataria__id=int(empresa_id)).order_by('-dtEmissao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Recebimento de Notas Fiscais'
        context['cenario_nome'] = 'Financeiro'
        context['menu_nome'] = 'Recebimento de Notas'
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoUpdateView(UpdateView):
    model = NotaFiscal
    from .forms_recebimento_notafiscal import NotaFiscalRecebimentoForm
    form_class = NotaFiscalRecebimentoForm
    template_name = 'financeiro/editar_recebimento_nota_fiscal.html'
    success_url = reverse_lazy('medicos:recebimento_notas_fiscais')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Recebimento de Nota Fiscal'
        context['cenario_nome'] = 'Financeiro'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Recebimento atualizado com sucesso!')
        return super().form_valid(form)
