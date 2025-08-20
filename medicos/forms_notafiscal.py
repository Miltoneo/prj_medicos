from django.core.exceptions import ValidationError
from medicos.models import NotaFiscal
from django import forms
from medicos.models.fiscal import NotaFiscal
from medicos.models.financeiro import MeioPagamento

class NotaFiscalForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        serie = cleaned_data.get('serie')
        empresa_destinataria = cleaned_data.get('empresa_destinataria')
        if numero and serie and empresa_destinataria:
            qs = NotaFiscal.objects.filter(
                numero=numero,
                serie=serie,
                empresa_destinataria=empresa_destinataria
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    'Já existe uma nota fiscal com este número, série e empresa destinatária.'
                )
        return cleaned_data
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['meio_pagamento', 'dtRecebimento', 'status_recebimento']:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        if 'meio_pagamento' in self.fields:
            self.fields['meio_pagamento'].required = False
            
            # Filtrar meio de pagamento pela empresa da nota fiscal
            empresa = None
            if self.instance and self.instance.pk:
                # Para instância existente, tentar acessar empresa_destinataria
                empresa = getattr(self.instance, 'empresa_destinataria', None)
            elif hasattr(self, 'empresa_sessao') and self.empresa_sessao:
                # Para nova instância, usar empresa da sessão
                empresa = self.empresa_sessao
                
            if empresa:
                self.fields['meio_pagamento'].queryset = MeioPagamento.objects.filter(
                    empresa=empresa,
                    ativo=True
                ).order_by('nome')
            else:
                # Se não há empresa definida, não exibe nenhum meio de pagamento por enquanto
                self.fields['meio_pagamento'].queryset = MeioPagamento.objects.none()
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
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            # Salvar sem recalcular impostos automaticamente (preserva valores editados manualmente)
            instance.save(pular_recalculo=True)
        return instance

    class Meta:
        model = NotaFiscal
        fields = [
            'numero', 'tomador', 'cnpj_tomador', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento',
            'val_bruto', 'val_ISS', 'val_PIS', 'val_COFINS', 'val_IR', 'val_CSLL', 'val_outros', 'val_liquido'
        ]
        widgets = {
            'dtEmissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'dtRecebimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
