from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django.shortcuts import get_object_or_404
from .tables_rateio_medico import NotaFiscalRateioMedicoTable
from .filters_rateio_medico import NotaFiscalRateioMedicoFilter
from medicos.models.fiscal import NotaFiscalRateioMedico, NotaFiscal

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoListView(FilterView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/lista_notas_rateio_medicos.html'
    filterset_class = NotaFiscalRateioMedicoFilter
    table_class = NotaFiscalRateioMedicoTable
    context_object_name = 'table'
    paginate_by = 20


    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = None
        if 'nota_id' in self.kwargs:
            self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.nota_fiscal:
            qs = NotaFiscalRateioMedico.objects.filter(nota_fiscal=self.nota_fiscal)
        else:
            qs = NotaFiscalRateioMedico.objects.all()
        filter_params = self.request.GET.copy()
        self.filter = self.filterset_class(filter_params, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = self.table_class(self.get_queryset())
        context['table'] = table
        context['filter'] = getattr(self, 'filter', None)
        context['titulo_pagina'] = 'Notas Fiscais Rateadas por Médico'
        if self.nota_fiscal:
            context['nota_fiscal'] = self.nota_fiscal
        return context
