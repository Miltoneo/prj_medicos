
# Imports: Django
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# Imports: Third Party
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

# Imports: Local
from medicos.models.fiscal import NotaFiscal
from .tables_notafiscal_lista import NotaFiscalListaTable
from .filters_notafiscal import NotaFiscalFilter


from .forms_notafiscal import NotaFiscalForm

class NotaFiscalCreateView(CreateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/criar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campos_topo'] = [
            'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
        ]
        context['campos_excluir'] = [
            'numero','tipo_servico','meio_pagamento','status_recebimento','dtEmissao','dtRecebimento','dtVencimento','descricao_servicos','serie','criado_por'
        ]
        return context
 
class NotaFiscalUpdateView(UpdateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/editar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

class NotaFiscalDeleteView(DeleteView):
    model = NotaFiscal
    template_name = 'faturamento/excluir_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

@method_decorator(login_required, name='dispatch')
class NotaFiscalListView(SingleTableMixin, FilterView):
    model = NotaFiscal
    table_class = NotaFiscalListaTable
    filterset_class = NotaFiscalFilter
    template_name = 'faturamento/lista_notas_fiscais.html'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.request.session.get('empresa_id')
        if empresa_id:
            return NotaFiscal.objects.filter(empresa_destinataria_id=empresa_id)
        return NotaFiscal.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Entrada de Notas Fiscais'
        context['menu_nome'] = 'Notas Fiscais'
        context['cenario_nome'] = 'Faturamento'
        context['empresa_atual'] = self.request.session.get('empresa_atual')
        context['mes_ano'] = self.request.session.get('mes_ano')
        return context
