


from datetime import date
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_filters.views import FilterView
import django_tables2 as tables
from django_tables2.views import SingleTableMixin
from medicos.models.despesas import ItemDespesaRateioMensal, ItemDespesa, GrupoDespesa, Socio
from medicos.forms import ItemDespesaRateioMensalForm
from medicos.filters_rateio_medico import ItemDespesaRateioMensalFilter


def cadastro_rateio_list(request):
    # Mês padrão
    default_mes = date.today().strftime('%Y-%m')
    mes_competencia = request.GET.get('mes_competencia', default_mes)
    # Filtrar apenas itens de despesa que pertencem a grupo com rateio
    grupos_com_rateio = GrupoDespesa.objects.filter(rateio=True)
    itens_grupo_rateio = ItemDespesa.objects.filter(grupo__in=grupos_com_rateio)
    # Itens de despesa com rateio para o mês selecionado
    itens_com_rateio_ids = ItemDespesaRateioMensal.objects.filter(data_referencia=mes_competencia).values_list('item_despesa_id', flat=True).distinct()
    itens_com_rateio = itens_grupo_rateio.filter(id__in=itens_com_rateio_ids)
    itens_sem_rateio = itens_grupo_rateio.exclude(id__in=itens_com_rateio_ids)
    # Lista: primeiro os com rateio, depois os demais
    itens_despesa = list(itens_com_rateio) + list(itens_sem_rateio)
    itens_com_rateio_ids = list(itens_com_rateio_ids)
    selected_item_id = request.GET.get('item_despesa')
    rateios = []
    total_percentual = 0
    if selected_item_id:
        rateios_qs = ItemDespesaRateioMensal.objects.filter(item_despesa_id=selected_item_id, data_referencia=mes_competencia)
        for r in rateios_qs:
            rateios.append({
                'id': r.id,
                'socio': r.socio,
                'percentual': r.percentual,
                'observacoes': r.observacoes,
            })
        total_percentual = sum([float(r['percentual']) for r in rateios])
    context = {
        'default_mes': default_mes,
        'mes_competencia': mes_competencia,
        'itens_despesa': itens_despesa,
        'itens_com_rateio_ids': itens_com_rateio_ids,
        'selected_item_id': int(selected_item_id) if selected_item_id else None,
        'rateios': rateios,
        'total_percentual': '{:.2f}'.format(total_percentual),
    }
    return render(request, 'cadastro/rateio_list.html', context)


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
        # Adiciona mes_competencia e default_mes ao contexto para compatibilidade com o template
        from datetime import date
        default_mes = date.today().strftime('%Y-%m')
        mes_competencia = self.request.GET.get('mes_competencia', default_mes)
        context['default_mes'] = default_mes
        context['mes_competencia'] = mes_competencia
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
