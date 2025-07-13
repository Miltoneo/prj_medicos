from django import forms
from medicos.models.fiscal import NotaFiscal

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        exclude = ['dtVencimento', 'descricao_servicos', 'serie', 'created_by', 'aliquotas']
        widgets = {
            'dtEmissao': forms.DateInput(attrs={'type': 'date'}),
            'dtRecebimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'meio_pagamento' in self.fields:
            self.fields['meio_pagamento'].required = False
