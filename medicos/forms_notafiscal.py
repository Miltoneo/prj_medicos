from django import forms
from medicos.models.fiscal import NotaFiscal

class NotaFiscalForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        serie = cleaned_data.get('serie', '1')
        empresa = cleaned_data.get('empresa_destinataria')
        if numero and serie and empresa:
            from medicos.models.fiscal import NotaFiscal
            qs = NotaFiscal.objects.filter(
                numero=numero,
                serie=serie,
                empresa_destinataria=empresa
            )
            # Exclui o registro atual se for edição
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    'Já existe uma nota fiscal com este número, série e empresa. Escolha outro número ou série.'
                )
        return cleaned_data
    class Meta:
        model = NotaFiscal
        exclude = ['dtVencimento', 'descricao_servicos', 'serie', 'created_by', 'aliquotas']
        widgets = {
            'dtEmissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'dtRecebimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'meio_pagamento' in self.fields:
            self.fields['meio_pagamento'].required = False
