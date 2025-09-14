import django_filters
from .models.conta_corrente import MovimentacaoContaCorrente
from .models.financeiro import DescricaoMovimentacaoFinanceira
from django import forms

class MovimentacaoContaCorrenteFilter(django_filters.FilterSet):
    socio = django_filters.ModelChoiceFilter(
        field_name='socio',
        queryset=None,  # Será populado no __init__
        label='Médico/Sócio',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Todos os médicos/sócios"
    )
    
    tipo_valor = django_filters.ChoiceFilter(
        choices=[
            ('', 'Todos os tipos'),
            ('positivo', 'Entrada na conta'),
            ('negativo', 'Saída da conta'),
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
        # Filtrar descrições e sócios pela empresa do contexto
        from core.context_processors import empresa_context
        from .models.financeiro import DescricaoMovimentacaoFinanceira
        from .models.base import Socio
        
        request = kwargs.get('request')
        if request:
            empresa = empresa_context(request).get('empresa')
            if empresa:
                self.filters['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa).order_by('descricao')
                self.filters['socio'].queryset = Socio.objects.filter(empresa=empresa, ativo=True).select_related('pessoa').order_by('pessoa__name')
            else:
                # Se não há empresa, usar queryset vazio mas válido
                self.filters['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.none()
                self.filters['socio'].queryset = Socio.objects.none()
        else:
            # Se não há request, usar queryset vazio mas válido  
            from .models.financeiro import DescricaoMovimentacaoFinanceira
            from .models.base import Socio
            self.filters['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.none()
            self.filters['socio'].queryset = Socio.objects.none()

    def filter_by_month(self, queryset, name, value):
        if value:
            year, month = value.split('-')
            return queryset.filter(data_movimentacao__year=year, data_movimentacao__month=month)
        return queryset

    def filter_tipo_valor(self, queryset, name, value):
        if value == 'positivo':
            return queryset.filter(valor__gt=0)  # Entradas na conta
        elif value == 'negativo':
            return queryset.filter(valor__lt=0)  # Saídas da conta
        return queryset

    class Meta:
        model = MovimentacaoContaCorrente
        fields = ['socio', 'tipo_valor', 'descricao_movimentacao', 'data_movimentacao_mes']
