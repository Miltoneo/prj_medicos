from django import forms
from medicos.models.fiscal import NotaFiscal
from medicos.models.financeiro import MeioPagamento

class NotaFiscalRecebimentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marca a instância para indicar que é um contexto de recebimento
        # Isso será usado pelo modelo para pular certas validações
        if self.instance:
            self.instance._skip_value_validation = True
        
        for field in self.fields.values():
            field.required = False
        
        # Campo val_liquido não deve ser editável no contexto de recebimento
        if 'val_liquido' in self.fields:
            self.fields['val_liquido'].disabled = True
            self.fields['val_liquido'].widget.attrs['readonly'] = True
        
        # Filtrar meio de pagamento pela empresa da nota fiscal
        if self.instance and self.instance.empresa_destinataria:
            queryset = MeioPagamento.objects.filter(
                empresa=self.instance.empresa_destinataria,
                ativo=True
            ).order_by('nome')
            
            self.fields['meio_pagamento'].queryset = queryset
        else:
            # Se não há instância ou empresa, não exibe nenhum meio de pagamento
            self.fields['meio_pagamento'].queryset = MeioPagamento.objects.none()
            
        # Força o valor inicial do campo dtRecebimento no formato ISO para o input type=date
        if 'dtRecebimento' in self.fields and self.instance and self.instance.dtRecebimento:
            self.initial['dtRecebimento'] = self.instance.dtRecebimento.strftime('%Y-%m-%d')

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
        
        # Se há data de recebimento, automaticamente define status como "recebido"
        if dtRecebimento:
            cleaned_data['status_recebimento'] = 'recebido'
        else:
            # Se não há data de recebimento, mantém status como "pendente"
            cleaned_data['status_recebimento'] = 'pendente'
            
        if errors:
            from django.core.exceptions import ValidationError
            raise ValidationError(errors)
        return cleaned_data
        
    class Meta:
        model = NotaFiscal
        fields = ['meio_pagamento', 'dtRecebimento', 'val_liquido']
        widgets = {
            'dtRecebimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'meio_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'val_liquido': forms.HiddenInput(),  # Campo oculto para evitar erro de validação
        }
