from django import forms
from medicos.models.fiscal import NotaFiscal

class NotaFiscalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['meio_pagamento', 'dtRecebimento', 'status_recebimento']:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        serie = cleaned_data.get('serie', '1')
        empresa = cleaned_data.get('empresa_destinataria')
        # Se empresa não está no cleaned_data, pega da instância (preenchida na view)
        if not empresa:
            empresa = getattr(self.instance, 'empresa_destinataria', None)
        # Se ainda não encontrou, pega do atributo empresa_id_sessao passado pela view
        if not empresa and hasattr(self, 'empresa_id_sessao') and self.empresa_id_sessao:
            from medicos.models.base import Empresa
            try:
                empresa = Empresa.objects.get(id=int(self.empresa_id_sessao))
            except Exception:
                empresa = None
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
        fields = [
            'numero', 'tomador', 'cnpj_tomador', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento',
            'val_bruto', 'val_ISS', 'val_PIS', 'val_COFINS', 'val_IR', 'val_CSLL', 'val_liquido'
        ]
        widgets = {
            'dtEmissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'dtRecebimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'meio_pagamento' in self.fields:
            self.fields['meio_pagamento'].required = False
        # Os campos de impostos e valor líquido voltam a ser editáveis pelo usuário
        # Os campos de impostos e valor líquido voltam a ser editáveis pelo usuário
