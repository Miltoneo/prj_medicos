

from django import forms
from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesa, GrupoDespesa

# Formulário para Despesa de Sócio
class DespesaSocioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar itens apenas da empresa correta e sem rateio
        if empresa_id:
            self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
                grupo_despesa__empresa_id=empresa_id,
                grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
            )
        else:
            # Fallback: filtrar apenas por tipo_rateio se empresa_id não fornecida
            self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
                grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
            )
        
        self.fields['item_despesa'].required = True
        # Não sobrescrever o widget após definir o queryset, mantendo o padrão do ModelForm

    class Meta:
        model = DespesaSocio
        fields = ['item_despesa', 'data', 'valor', 'tipo_classificacao']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tipo_classificacao': forms.Select(attrs={'class': 'form-control'}),
        }


class DespesaEmpresaForm(forms.ModelForm):
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError('O valor não pode ser negativo.')
        return valor

    class Meta:
        model = DespesaRateada
        fields = ['item_despesa', 'data', 'valor', 'tipo_classificacao']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tipo_classificacao': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        import sys
        empresa_id = kwargs.pop('empresa_id', None)
        print(f"[DespesaEmpresaForm] empresa_id recebido: {empresa_id}", file=sys.stderr)
        super().__init__(*args, **kwargs)
        initial_item_id = None
        if self.instance and self.instance.pk and self.instance.item_despesa_id:
            initial_item_id = self.instance.item_despesa_id
            print(f"[DespesaEmpresaForm] item_despesa_id inicial: {initial_item_id}", file=sys.stderr)
            self.initial['item_despesa'] = initial_item_id
        else:
            print(f"[DespesaEmpresaForm] Nenhum item_despesa_id inicial detectado.", file=sys.stderr)
        queryset = ItemDespesa.objects.filter(
            grupo_despesa__empresa_id=empresa_id,
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
        )
        print(f"[DespesaEmpresaForm] itens encontrados: {queryset.count()}", file=sys.stderr)
        print(f"[DespesaEmpresaForm] IDs dos itens: {[i.id for i in queryset]}", file=sys.stderr)
        self.fields['item_despesa'].queryset = queryset
        # Não sobrescrever o widget após definir o queryset, mantendo o padrão do ModelForm
        if self.instance and self.instance.pk and self.instance.data:
            print(f"[DespesaEmpresaForm] Data inicial: {self.instance.data}", file=sys.stderr)
            self.initial['data'] = self.instance.data.strftime('%Y-%m-%d')
