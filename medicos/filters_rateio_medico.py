import django_filters
from medicos.models.fiscal import NotaFiscalRateioMedico
from medicos.models.base import Socio
from django import forms
import datetime

class NotaFiscalRateioMedicoFilter(django_filters.FilterSet):
    medico = django_filters.ModelChoiceFilter(queryset=Socio.objects.filter(ativo=True), label="Médico")
    nota_fiscal = django_filters.NumberFilter(label="Nota Fiscal")
    competencia = django_filters.DateFilter(
        field_name='nota_fiscal__dtEmissao',
        label="Competência",
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control',
            'value': datetime.date.today().strftime('%Y-%m')
        })
    )

    class Meta:
        model = NotaFiscalRateioMedico
        fields = ['medico', 'nota_fiscal', 'competencia']
