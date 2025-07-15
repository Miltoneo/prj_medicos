from django import forms
from .models.financeiro import Financeiro

class FinanceiroForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostra a descrição detalhada no select
        if 'descricao_movimentacao_financeira' in self.fields:
            self.fields['descricao_movimentacao_financeira'].label_from_instance = lambda obj: obj.descricao or f"DescriçãoMovimentacaoFinanceira #{obj.pk}"
        if 'data_movimentacao' in self.fields:
            self.fields['data_movimentacao'].input_formats = ['%Y-%m-%d']

    class Meta:
        model = Financeiro
        exclude = ['conta', 'criado_por', 'created_by']
        widgets = {
            'data_movimentacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
