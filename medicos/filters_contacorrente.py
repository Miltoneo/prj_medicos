import django_filters
from .models.conta_corrente import MovimentacaoContaCorrente
from .models.financeiro import DescricaoMovimentacaoFinanceira
from django import forms

class MovimentacaoContaCorrenteFilter(django_filters.FilterSet):
    tipo_valor = django_filters.ChoiceFilter(
        choices=[
            ('', 'Todos os tipos'),
            ('positivo', 'Débito Bancário (Entrada)'),
            ('negativo', 'Crédito Bancário (Saída)'),
        ],
        label='Tipo de Movimentação',
        widget=forms.Select(attrs={'class': 'form-control'}),
        method='filter_tipo_valor'
    )
    
    descricao_movimentacao = django_filters.ModelChoiceFilter(
        field_name='descricao_movimentacao',
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
        # Filtrar descrições pela empresa do contexto
        from core.context_processors import empresa_context
        from .models.financeiro import DescricaoMovimentacaoFinanceira
        
        request = kwargs.get('request')
        if request:
            empresa = empresa_context(request).get('empresa')
            if empresa:
                self.filters['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa).order_by('descricao')
            else:
                # Se não há empresa, usar queryset vazio mas válido
                self.filters['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.none()
        else:
            # Se não há request, usar queryset vazio mas válido  
            from .models.financeiro import DescricaoMovimentacaoFinanceira
            self.filters['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.none()

    def filter_by_month(self, queryset, name, value):
        if value:
            year, month = value.split('-')
            return queryset.filter(data_movimentacao__year=year, data_movimentacao__month=month)
        return queryset

    def filter_tipo_valor(self, queryset, name, value):
        if value == 'positivo':
            return queryset.filter(valor__gt=0)  # Débitos bancários (entradas)
        elif value == 'negativo':
            return queryset.filter(valor__lt=0)  # Créditos bancários (saídas)
        return queryset

    class Meta:
        model = MovimentacaoContaCorrente
        fields = ['tipo_valor', 'descricao_movimentacao']
