import django_filters
from medicos.models.despesas import DespesaRateada, ItemDespesa, DespesaBase

class DespesaEmpresaFilter(django_filters.FilterSet):
    competencia = django_filters.DateFromToRangeFilter(field_name='data', label='Competência (mês)')
    item_despesa__descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')
    item_despesa__grupo_despesa__descricao = django_filters.CharFilter(lookup_expr='icontains', label='Grupo')
    tipo_classificacao = django_filters.ChoiceFilter(
        choices=DespesaBase.TipoClassificacao.choices,
        label='Classificação',
        empty_label="Todas as classificações"
    )

    class Meta:
        model = DespesaRateada
        fields = ['competencia', 'item_despesa__descricao', 'item_despesa__grupo_despesa__descricao', 'tipo_classificacao']
