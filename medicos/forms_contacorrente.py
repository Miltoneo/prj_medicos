from django import forms
from .models.conta_corrente import MovimentacaoContaCorrente

class MovimentacaoContaCorrenteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extrair empresa do contexto se fornecida
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar campos por empresa se disponível
        if empresa:
            from .models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento
            
            if 'descricao_movimentacao' in self.fields:
                self.fields['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa).order_by('descricao')
            
            if 'meio_pagamento' in self.fields:
                self.fields['meio_pagamento'].queryset = MeioPagamento.objects.filter(empresa=empresa).order_by('nome')
        
        # Mostra a descrição detalhada no select
        if 'descricao_movimentacao' in self.fields:
            self.fields['descricao_movimentacao'].label_from_instance = lambda obj: obj.descricao or f"Descrição #{obj.pk}"
        
        if 'meio_pagamento' in self.fields:
            self.fields['meio_pagamento'].label_from_instance = lambda obj: obj.nome or f"Meio #{obj.pk}"
        
        if 'data_movimentacao' in self.fields:
            self.fields['data_movimentacao'].input_formats = ['%Y-%m-%d']

    class Meta:
        model = MovimentacaoContaCorrente
        exclude = ['empresa', 'created_by', 'conta']
        widgets = {
            'data_movimentacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'instrumento_bancario': forms.TextInput(attrs={'class': 'form-control'}),
        }
