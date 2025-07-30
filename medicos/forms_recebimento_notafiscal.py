from django import forms
from medicos.models.fiscal import NotaFiscal

class NotaFiscalRecebimentoForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        dtRecebimento = cleaned_data.get('dtRecebimento')
        meio_pagamento = cleaned_data.get('meio_pagamento')
        # dtEmissao vem da instância, pois não está no form
        dtEmissao = self.instance.dtEmissao if self.instance else None
        errors = {}
        if dtRecebimento and dtEmissao and dtRecebimento < dtEmissao:
            errors['dtRecebimento'] = 'A data de recebimento não pode ser inferior à data de emissão.'
        if (dtRecebimento and not meio_pagamento) or (meio_pagamento and not dtRecebimento):
            errors['meio_pagamento'] = 'Meio de pagamento e data de recebimento devem ser preenchidos juntos.'
            errors['dtRecebimento'] = 'Meio de pagamento e data de recebimento devem ser preenchidos juntos.'
        status = cleaned_data.get('status_recebimento')
        # Regra: se há data de recebimento, status deve ser RECEBIDO/completo
        if dtRecebimento and status and status.lower() not in ['completo', 'recebido']:
            errors['status_recebimento'] = 'Notas com data de recebimento devem ter o status de Recebido.'
        if errors:
            from django.core.exceptions import ValidationError
            raise ValidationError(errors)
        return cleaned_data
    class Meta:
        model = NotaFiscal
        fields = ['meio_pagamento', 'dtRecebimento', 'status_recebimento']
        widgets = {
            'dtRecebimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'meio_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'status_recebimento': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
        # Força o valor inicial do campo dtRecebimento no formato ISO para o input type=date
        if 'dtRecebimento' in self.fields and self.instance and self.instance.dtRecebimento:
            self.initial['dtRecebimento'] = self.instance.dtRecebimento.strftime('%Y-%m-%d')
