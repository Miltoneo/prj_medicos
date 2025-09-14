import django_filters
from .models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from django import forms

class FinanceiroFilter(django_filters.FilterSet):
    from .models.base import Socio
    socio = django_filters.ModelChoiceFilter(
        field_name='socio',
        queryset=Socio.objects.none(),  # Será populado no __init__
        label='Médico/Sócio',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    descricao_movimentacao_financeira = django_filters.ModelChoiceFilter(
        field_name='descricao_movimentacao_financeira',
        queryset=DescricaoMovimentacaoFinanceira.objects.none(),  # Será populado no __init__
        label='Descrição',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Todas as descrições"
    )
    data_movimentacao_mes = django_filters.CharFilter(
        field_name='data_movimentacao',
        label='Mês/Ano',
        method='filter_by_month',
        widget=forms.TextInput(attrs={'type': 'month', 'class': 'form-control'})
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
            else:
                # Se não há empresa, usar querysets vazios mas válidos
                self.filters['socio'].queryset = Socio.objects.none()
                self.filters['descricao_movimentacao_financeira'].queryset = DescricaoMovimentacaoFinanceira.objects.none()
        else:
            # Se não há request, usar querysets vazios mas válidos  
            from .models.base import Socio
            from .models.financeiro import DescricaoMovimentacaoFinanceira
            self.filters['socio'].queryset = Socio.objects.none()
            self.filters['descricao_movimentacao_financeira'].queryset = DescricaoMovimentacaoFinanceira.objects.none()

    def filter_by_month(self, queryset, name, value):
        if value:
            year, month = value.split('-')
            return queryset.filter(data_movimentacao__year=year, data_movimentacao__month=month)
        return queryset
    # Filtro 'tipo' removido: campo não existe mais no modelo Financeiro

    class Meta:
        model = Financeiro
        fields = ['socio', 'descricao_movimentacao_financeira']
