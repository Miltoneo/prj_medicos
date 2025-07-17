from django import forms
from .models.financeiro import AplicacaoFinanceira

class AplicacaoFinanceiraForm(forms.ModelForm):
    class Meta:
        model = AplicacaoFinanceira
        fields = ['data_referencia', 'saldo', 'ir_cobrado', 'descricao']
        widgets = {
            'data_referencia': forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
            'saldo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ir_cobrado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }
