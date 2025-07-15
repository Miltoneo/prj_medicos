import django_filters
from .models.financeiro import Financeiro
from django import forms

class FinanceiroFilter(django_filters.FilterSet):
    from .models.base import Socio
    socio = django_filters.ModelChoiceFilter(
        field_name='socio',
        queryset=Socio.objects.all(),
        label='Médico/Sócio',
        widget=forms.Select
    )
    descricao_movimentacao_financeira = django_filters.CharFilter(field_name='descricao_movimentacao_financeira__descricao', lookup_expr='icontains', label='Descrição')
    data_movimentacao_mes = django_filters.CharFilter(
        field_name='data_movimentacao',
        label='Mês/Ano',
        method='filter_by_month',
        widget=forms.TextInput(attrs={'type': 'month'})
    )

    def filter_by_month(self, queryset, name, value):
        if value:
            year, month = value.split('-')
            return queryset.filter(data_movimentacao__year=year, data_movimentacao__month=month)
        return queryset
    tipo = django_filters.ChoiceFilter(field_name='tipo', choices=Financeiro.TIPOS_MOVIMENTACAO, label='Tipo')

    class Meta:
        model = Financeiro
        fields = ['socio', 'descricao_movimentacao_financeira', 'data_movimentacao', 'tipo']
