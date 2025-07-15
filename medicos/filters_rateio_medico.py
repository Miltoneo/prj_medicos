import django_filters
from medicos.models.fiscal import NotaFiscalRateioMedico
from medicos.models.base import Socio
from django import forms
import datetime

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
