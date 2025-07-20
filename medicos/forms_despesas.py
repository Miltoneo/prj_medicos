from django import forms
from medicos.models.despesas import DespesaRateada

class DespesaEmpresaForm(forms.ModelForm):
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError('O valor não pode ser negativo.')
        return valor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from medicos.models.despesas import ItemDespesa, GrupoDespesa
        self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
        )
    class Meta:
        model = DespesaRateada
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            'item_despesa': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from medicos.models.despesas import ItemDespesa, GrupoDespesa
        self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
        )
        # Corrige o valor inicial do campo data para o formato ISO
        if self.instance and self.instance.pk and self.instance.data:
            self.initial['data'] = self.instance.data.strftime('%Y-%m-%d')
