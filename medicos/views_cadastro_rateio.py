from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from medicos.models.despesas import ItemDespesaRateioMensal, ItemDespesa, GrupoDespesa, Socio
from medicos.forms import ItemDespesaRateioMensalForm
from django_filters.views import FilterView
import django_tables2 as tables
from django_tables2.views import SingleTableMixin
from medicos.filters_rateio_medico import ItemDespesaRateioMensalFilter

class ItemDespesaRateioMensalTable(tables.Table):
    class Meta:
        model = ItemDespesaRateioMensal
        template_name = "django_tables2/bootstrap4.html"
        fields = ("data_referencia", "item_despesa", "socio", "percentual_rateio", "observacoes", "ativo")
        attrs = {"class": "table table-striped table-bordered"}

class CadastroRateioView(SingleTableMixin, FilterView):
    model = ItemDespesaRateioMensal
    table_class = ItemDespesaRateioMensalTable
    template_name = "cadastro/rateio_list.html"
    filterset_class = ItemDespesaRateioMensalFilter
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = _(u"Configuração de Rateio Mensal")
        context['itens_despesa'] = ItemDespesa.objects.all()
        context['socios'] = Socio.objects.all()
        return context

class CadastroRateioCreateView(CreateView):
    model = ItemDespesaRateioMensal
    form_class = ItemDespesaRateioMensalForm
    template_name = "cadastro/rateio_form.html"
    success_url = reverse_lazy('cadastro_rateio')

    def form_valid(self, form):
        messages.success(self.request, _(u"Configuração de rateio criada com sucesso."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = _(u"Nova Configuração de Rateio")
        return context

class CadastroRateioUpdateView(UpdateView):
    model = ItemDespesaRateioMensal
    form_class = ItemDespesaRateioMensalForm
    template_name = "cadastro/rateio_form.html"
    success_url = reverse_lazy('cadastro_rateio')

    def form_valid(self, form):
        messages.success(self.request, _(u"Configuração de rateio atualizada com sucesso."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = _(u"Editar Configuração de Rateio")
        return context

class CadastroRateioDeleteView(DeleteView):
    model = ItemDespesaRateioMensal
    template_name = "cadastro/rateio_confirm_delete.html"
    success_url = reverse_lazy('cadastro_rateio')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _(u"Configuração de rateio removida com sucesso."))
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = _(u"Remover Configuração de Rateio")
        return context
