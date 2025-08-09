import django_filters
from .models.financeiro import Financeiro
from django import forms

class FinanceiroFilter(django_filters.FilterSet):
    from .models.base import Socio
    socio = django_filters.ModelChoiceFilter(
        field_name='socio',
        queryset=Socio.objects.none(),  # Será populado no __init__
        label='Médico/Sócio',
        widget=forms.Select
    )
    descricao_movimentacao_financeira = django_filters.ModelChoiceFilter(
        field_name='descricao_movimentacao_financeira',
        queryset=None,  # Será populado no __init__
        label='Descrição',
        widget=forms.Select,
        empty_label="Todas as descrições"
    )
    data_movimentacao_mes = django_filters.CharFilter(
        field_name='data_movimentacao',
        label='Mês/Ano',
        method='filter_by_month',
        widget=forms.TextInput(attrs={'type': 'month'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar sócios e descrições pela empresa do contexto
        from core.context_processors import empresa_context
        from .models.base import Socio
        from .models.financeiro import DescricaoMovimentacaoFinanceira
        
        request = kwargs.get('request')
        if request:
            empresa = empresa_context(request).get('empresa')
            if empresa:
                self.filters['socio'].queryset = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
                self.filters['descricao_movimentacao_financeira'].queryset = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa).order_by('descricao')

    def filter_by_month(self, queryset, name, value):
        if value:
            year, month = value.split('-')
            return queryset.filter(data_movimentacao__year=year, data_movimentacao__month=month)
        return queryset
    # Filtro 'tipo' removido: campo não existe mais no modelo Financeiro

    class Meta:
        model = Financeiro
        fields = ['socio', 'descricao_movimentacao_financeira', 'nota_fiscal', 'data_movimentacao']
