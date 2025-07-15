import django_filters
from .models.financeiro import Financeiro
from django import forms

class FinanceiroFilter(django_filters.FilterSet):
    socio = django_filters.CharFilter(field_name='socio__pessoa__name', lookup_expr='icontains', label='Médico/Sócio')
    descricao_movimentacao_financeira = django_filters.CharFilter(field_name='descricao_movimentacao_financeira__nome', lookup_expr='icontains', label='Descrição')
    data_movimentacao = django_filters.DateFromToRangeFilter(
        field_name='data_movimentacao',
        label='Período',
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'})
    )
    tipo = django_filters.ChoiceFilter(field_name='tipo', choices=Financeiro.TIPOS_MOVIMENTACAO, label='Tipo')

    class Meta:
        model = Financeiro
        fields = ['socio', 'descricao_movimentacao_financeira', 'data_movimentacao', 'tipo']
