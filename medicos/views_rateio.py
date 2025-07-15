from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_tables2 import RequestConfig
from django_filters.views import FilterView
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.base import Empresa, Socio
from .tables_rateio import NotaFiscalRateioTable
from .forms import NotaFiscalRateioMedicoForm, NotaFiscalRateioMedicoFilter, NotaFiscalRateioFilter

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
    filterset_class = NotaFiscalRateioFilter
    table_class = NotaFiscalRateioTable
    paginate_by = 20

    def get_queryset(self):
        # Sempre filtra por empresa da sessão
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return NotaFiscal.objects.none()
        return NotaFiscal.objects.filter(empresa_destinataria_id=empresa_id).order_by('-dtEmissao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.request.session.get('empresa_id')
        empresa = None
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa = None
        queryset = self.get_queryset()
        table = self.table_class(queryset)
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        # Selection logic: get nota_id from GET, else default to first nota
        nota_id = self.request.GET.get('nota_id')
        nota_fiscal = None
        if nota_id:
            try:
                nota_fiscal = queryset.get(id=nota_id)
            except (NotaFiscal.DoesNotExist, ValueError):
                nota_fiscal = None
        elif queryset.exists():
            nota_fiscal = queryset.first()
        context.update({
            'empresa_id': empresa_id,
            'empresa': empresa,
            'table': table,
            'nota_fiscal': nota_fiscal,
        })
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
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.nota_fiscal = self.nota_fiscal
        return form
    model = NotaFiscalRateioMedico
    form_class = NotaFiscalRateioMedicoForm
    template_name = 'faturamento/rateio_medico_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Always set nota_fiscal from dispatch (using nota_id)
        form.instance.nota_fiscal = self.nota_fiscal
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

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
