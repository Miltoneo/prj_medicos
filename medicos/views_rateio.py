from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_tables2 import RequestConfig
from django_filters.views import FilterView
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.base import Empresa, Socio
from .tables_rateio import NotaFiscalRateioTable
from .forms import NotaFiscalRateioMedicoForm, NotaFiscalRateioMedicoFilter

# Mixin para contexto do cenário de faturamento
class RateioContextMixin:
    menu_nome = 'Rateio de Notas'
    cenario_nome = 'Faturamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_nome'] = self.menu_nome
        context['cenario_nome'] = self.cenario_nome
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioListView(RateioContextMixin, FilterView):
    model = NotaFiscal
    template_name = 'faturamento/lista_notas_rateio.html'
    context_object_name = 'table'
    filterset_class = NotaFiscalRateioMedicoFilter
    table_class = NotaFiscalRateioTable
    paginate_by = 20

    def get_queryset(self):
        qs = NotaFiscal.objects.all().order_by('-dtEmissao')
        empresa_id = self.request.GET.get('empresa_id')
        if empresa_id:
            qs = qs.filter(empresa_destinataria_id=empresa_id)
        return qs

    def get_table_data(self):
        return self.get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = self.table_class(self.get_table_data())
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoListView(RateioContextMixin, ListView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/lista_rateio_medicos.html'
    context_object_name = 'table'
    paginate_by = 20
    table_class = NotaFiscalRateioTable

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return NotaFiscalRateioMedico.objects.filter(nota_fiscal=self.nota_fiscal)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        table = self.table_class(self.get_queryset())
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoCreateView(RateioContextMixin, CreateView):
    model = NotaFiscalRateioMedico
    form_class = NotaFiscalRateioMedicoForm
    template_name = 'faturamento/rateio_medico_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.nota_fiscal = self.nota_fiscal
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('medicos:lista_rateio_medicos', kwargs={'nota_id': self.nota_fiscal.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoUpdateView(RateioContextMixin, UpdateView):
    model = NotaFiscalRateioMedico
    form_class = NotaFiscalRateioMedicoForm
    template_name = 'faturamento/rateio_medico_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        self.rateio = get_object_or_404(NotaFiscalRateioMedico, id=self.kwargs['rateio_id'], nota_fiscal=self.nota_fiscal)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.rateio

    def get_success_url(self):
        return reverse('medicos:lista_rateio_medicos', kwargs={'nota_id': self.nota_fiscal.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoDeleteView(RateioContextMixin, DeleteView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/rateio_medico_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        self.rateio = get_object_or_404(NotaFiscalRateioMedico, id=self.kwargs['rateio_id'], nota_fiscal=self.nota_fiscal)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.rateio

    def get_success_url(self):
        return reverse('medicos:lista_rateio_medicos', kwargs={'nota_id': self.nota_fiscal.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        return context
