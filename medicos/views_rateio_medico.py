from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from .tables_rateio_medico import NotaFiscalRateioMedicoTable
from .filters_rateio_medico import NotaFiscalRateioMedicoFilter
from medicos.models.fiscal import NotaFiscalRateioMedico

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoListView(FilterView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/lista_notas_rateio_medicos.html'
    filterset_class = NotaFiscalRateioMedicoFilter
    table_class = NotaFiscalRateioMedicoTable
    context_object_name = 'table'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = self.table_class(self.get_queryset())
        context['table'] = table
        context['titulo_pagina'] = 'Notas Fiscais Rateadas por Médico'
        return context
