
import datetime
import django_filters
from django import forms
from medicos.models.despesas import ItemDespesaRateioMensal, ItemDespesa
from medicos.models.base import Socio
from medicos.models.fiscal import NotaFiscalRateioMedico


# Filtro para configuração de rateio mensal de item de despesa
class ItemDespesaRateioMensalFilter(django_filters.FilterSet):
    item_despesa = django_filters.ModelChoiceFilter(queryset=ItemDespesa.objects.all(), label="Item de Despesa")
    socio = django_filters.ModelChoiceFilter(queryset=Socio.objects.all(), label="Sócio")
    data_referencia = django_filters.DateFilter(field_name="data_referencia", lookup_expr="exact", label="Mês de Competência")

    class Meta:
        model = ItemDespesaRateioMensal
        fields = ['item_despesa', 'socio', 'data_referencia']


class NotaFiscalRateioMedicoFilter(django_filters.FilterSet):
    medico = django_filters.ModelChoiceFilter(queryset=Socio.objects.filter(ativo=True), label="Médico")
    nota_fiscal = django_filters.CharFilter(field_name='nota_fiscal__numero', lookup_expr='icontains', label="Nota Fiscal")
    competencia = django_filters.CharFilter(
        label='Competência',
        method='filter_competencia',
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control',
            'value': datetime.date.today().strftime('%Y-%m')
        })
    )

    def filter_competencia(self, queryset, name, value):
        # value esperado: 'YYYY-MM'
        try:
            year, month = value.split('-')
            return queryset.filter(nota_fiscal__dtEmissao__year=year, nota_fiscal__dtEmissao__month=month)
        except Exception:
            return queryset

    class Meta:
        model = NotaFiscalRateioMedico
        fields = ['medico', 'nota_fiscal', 'competencia']
