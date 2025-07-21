
from django import forms
from medicos.models.despesas import DespesaSocio

# Formulário para Despesa de Sócio
class DespesaSocioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from medicos.models.despesas import ItemDespesa, GrupoDespesa
        self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
        )
        self.fields['item_despesa'].required = True
        self.fields['item_despesa'].widget.attrs['required'] = 'required'
    class Meta:
        model = DespesaSocio
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            'item_despesa': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
from django import forms
from medicos.models.despesas import DespesaRateada

class DespesaEmpresaForm(forms.ModelForm):
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError('O valor não pode ser negativo.')
        return valor
    # Removido o filtro manual do queryset para item_despesa, pois o ModelSelect2Widget faz a busca dinâmica
    class Meta:
        model = DespesaRateada
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            # O widget será setado dinamicamente no __init__
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)
        from medicos.widgets import ItemDespesaSelect2Widget
        self.fields['item_despesa'].widget = ItemDespesaSelect2Widget(
            attrs={'data-placeholder': 'Digite para filtrar o item de despesa', 'class': 'form-select'},
            empresa_id=empresa_id
        )
        # Corrige o valor inicial do campo data para o formato ISO
        if self.instance and self.instance.pk and self.instance.data:
            self.initial['data'] = self.instance.data.strftime('%Y-%m-%d')
