

# Imports: Django
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# Imports: Third Party
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

# Imports: Local
from medicos.models.fiscal import NotaFiscal
from .tables_notafiscal_lista import NotaFiscalListaTable
from .filters_notafiscal import NotaFiscalFilter

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
