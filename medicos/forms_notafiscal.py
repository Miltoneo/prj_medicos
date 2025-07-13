from django import forms
from medicos.models.fiscal import NotaFiscal

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        exclude = ['dtVencimento', 'descricao_servicos', 'serie', 'created_by', 'aliquotas']
