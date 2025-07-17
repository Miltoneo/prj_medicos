from django import forms
from .models.financeiro import Financeiro

class FinanceiroForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        # Mostra a descrição detalhada no select
        if 'descricao_movimentacao_financeira' in self.fields:
            self.fields['descricao_movimentacao_financeira'].label_from_instance = lambda obj: obj.descricao or f"DescriçãoMovimentacaoFinanceira #{obj.pk}"
        if 'data_movimentacao' in self.fields:
            self.fields['data_movimentacao'].input_formats = ['%Y-%m-%d']
        # Filtra notas fiscais pela empresa corrente
        if 'nota_fiscal' in self.fields and empresa is not None:
            from medicos.models.fiscal import NotaFiscal
            self.fields['nota_fiscal'].queryset = NotaFiscal.objects.filter(empresa_destinataria=empresa)

    class Meta:
        model = Financeiro
        exclude = ['conta', 'criado_por', 'created_by']
        widgets = {
            'data_movimentacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
