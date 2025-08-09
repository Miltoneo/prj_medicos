from django import forms
from .models.financeiro import Financeiro

class FinanceiroForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extrair empresa do contexto se fornecida
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar campos por empresa se disponível
        if empresa:
            from .models.base import Socio
            from .models.financeiro import DescricaoMovimentacaoFinanceira
            
            if 'socio' in self.fields:
                self.fields['socio'].queryset = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
            
            if 'descricao_movimentacao_financeira' in self.fields:
                self.fields['descricao_movimentacao_financeira'].queryset = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa).order_by('descricao')
        
        # Mostra a descrição detalhada no select
        if 'descricao_movimentacao_financeira' in self.fields:
            self.fields['descricao_movimentacao_financeira'].label_from_instance = lambda obj: obj.descricao or f"DescriçãoMovimentacaoFinanceira #{obj.pk}"
        if 'data_movimentacao' in self.fields:
            self.fields['data_movimentacao'].input_formats = ['%Y-%m-%d']

    class Meta:
        model = Financeiro
        exclude = ['conta', 'criado_por', 'created_by', 'nota_fiscal']
        widgets = {
            'data_movimentacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
