from django.core.exceptions import ValidationError
from medicos.models import NotaFiscal
from django import forms
from medicos.models.fiscal import NotaFiscal
from medicos.models.financeiro import MeioPagamento

class NotaFiscalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Verificar se existe recebimento para configurar campos readonly
        has_recebimento = getattr(self, 'has_recebimento', False) or (
            self.instance and self.instance.pk and self.instance.dtRecebimento
        )
        
        # Aplicar classes CSS para todos os campos
        for field_name, field in self.fields.items():
            if field_name not in ['meio_pagamento', 'status_recebimento']:
                field.widget.attrs.update({'class': 'form-control'})
        
        # Configuração específica para campos de recebimento
        for field in ['meio_pagamento', 'dtRecebimento', 'status_recebimento']:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Tornar campos de recebimento sempre readonly
        readonly_fields = ['meio_pagamento', 'status_recebimento', 'dtRecebimento']
        for field_name in readonly_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'readonly': True,
                    'style': 'background-color: #f8f9fa; cursor: not-allowed;',
                    'class': 'form-control'
                })
                if field_name in ['meio_pagamento', 'status_recebimento']:
                    self.fields[field_name].disabled = True

        if has_recebimento:
            # Campos adicionais ficam readonly quando já existe recebimento
            additional_readonly_fields = ['val_liquido']
            for field_name in additional_readonly_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs.update({
                        'readonly': True,
                        'style': 'background-color: #f8f9fa; cursor: not-allowed;',
                        'class': 'form-control'
                    })
        
        # Filtrar meio de pagamento pela empresa da nota fiscal
        if 'meio_pagamento' in self.fields:
            empresa = None
            if self.instance and self.instance.pk:
                empresa = getattr(self.instance, 'empresa_destinataria', None)
            elif hasattr(self, 'empresa_sessao'):
                empresa = self.empresa_sessao
            
            if empresa:
                self.fields['meio_pagamento'].queryset = MeioPagamento.objects.filter(
                    empresa=empresa
                ).order_by('nome')
            else:
                self.fields['meio_pagamento'].queryset = MeioPagamento.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        serie = cleaned_data.get('serie', '1')
        empresa = cleaned_data.get('empresa_destinataria')
        
        # Se empresa não está no cleaned_data, pega da instância
        if not empresa:
            empresa = getattr(self.instance, 'empresa_destinataria', None)
            
        # Se ainda não encontrou, pega do atributo empresa_id_sessao passado pela view
        if not empresa and hasattr(self, 'empresa_id_sessao') and self.empresa_id_sessao:
            from medicos.models.base import Empresa
            try:
                empresa = Empresa.objects.get(id=int(self.empresa_id_sessao))
            except Exception:
                empresa = None
        
        # Validação de unicidade
        if numero and serie and empresa:
            qs = NotaFiscal.objects.filter(
                numero=numero,
                serie=serie,
                empresa_destinataria=empresa
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    'Já existe uma nota fiscal com este número, série e empresa. Escolha outro número ou série.'
                )
                
        # Validação de campos de recebimento
        dtRecebimento = cleaned_data.get('dtRecebimento')
        meio_pagamento = cleaned_data.get('meio_pagamento')
        status_recebimento = cleaned_data.get('status_recebimento')
        
        # Se há data de recebimento, deve ter meio de pagamento
        if dtRecebimento and not meio_pagamento:
            raise forms.ValidationError({
                'meio_pagamento': 'Meio de pagamento é obrigatório quando há data de recebimento.'
            })
            
        # Se há meio de pagamento, deve ter data de recebimento
        if meio_pagamento and not dtRecebimento:
            raise forms.ValidationError({
                'dtRecebimento': 'Data de recebimento é obrigatória quando há meio de pagamento.'
            })
            
        # Se há data de recebimento, status deve ser "recebido"
        if dtRecebimento and status_recebimento and status_recebimento.lower() not in ['recebido', 'completo']:
            raise forms.ValidationError({
                'status_recebimento': 'Status deve ser "Recebido" quando há data de recebimento.'
            })
        
        # Validação do cálculo do valor líquido
        val_bruto = cleaned_data.get('val_bruto')
        val_iss = cleaned_data.get('val_ISS')
        val_pis = cleaned_data.get('val_PIS')
        val_cofins = cleaned_data.get('val_COFINS')
        val_ir = cleaned_data.get('val_IR')
        val_csll = cleaned_data.get('val_CSLL')
        val_outros = cleaned_data.get('val_outros')
        val_liquido = cleaned_data.get('val_liquido')
        
        if all([val_bruto, val_iss is not None, val_pis is not None, val_cofins is not None, 
                val_ir is not None, val_csll is not None, val_outros is not None, val_liquido]):
            
            # Calcular valor líquido esperado
            total_impostos = (val_iss or 0) + (val_pis or 0) + (val_cofins or 0) + (val_ir or 0) + (val_csll or 0)
            valor_liquido_esperado = val_bruto - total_impostos - (val_outros or 0)
            
            # Corrigir automaticamente o valor líquido se estiver incorreto
            if abs(val_liquido - valor_liquido_esperado) > 0.01:
                cleaned_data['val_liquido'] = round(valor_liquido_esperado, 2)
        
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
