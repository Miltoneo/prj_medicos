from django import forms
from medicos.models.despesas import DespesaRateada

class DespesaEmpresaForm(forms.ModelForm):
    class Meta:
        model = DespesaRateada
        fields = ['item_despesa', 'data', 'valor', 'possui_rateio']
