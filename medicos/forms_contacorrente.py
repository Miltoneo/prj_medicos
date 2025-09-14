from django import forms
from .models.conta_corrente import MovimentacaoContaCorrente

class MovimentacaoContaCorrenteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extrair empresa do contexto se fornecida
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar campos por empresa se disponível
        if empresa:
            from .models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento
            from .models.base import Socio
            from .models.fiscal import NotaFiscal
            
            # Filtrar sócios pela empresa
            if 'socio' in self.fields:
                self.fields['socio'].queryset = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
                self.fields['socio'].empty_label = "Selecione um médico/sócio (opcional)"
            
            # Filtrar descrições pela empresa
            if 'descricao_movimentacao' in self.fields:
                self.fields['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa).order_by('descricao')
                self.fields['descricao_movimentacao'].empty_label = "Selecione uma descrição"
            
            # Filtrar meios de pagamento pela empresa
            if 'instrumento_bancario' in self.fields:
                self.fields['instrumento_bancario'].queryset = MeioPagamento.objects.filter(empresa=empresa).order_by('nome')
                self.fields['instrumento_bancario'].empty_label = "Selecione um instrumento bancário (opcional)"
            
            # Filtrar notas fiscais pela empresa
            if 'nota_fiscal' in self.fields:
                self.fields['nota_fiscal'].queryset = NotaFiscal.objects.filter(empresa_destinataria=empresa).order_by('-dtEmissao')
                self.fields['nota_fiscal'].empty_label = "Selecione uma nota fiscal (opcional)"
        else:
            # Se não há empresa, usar querysets vazios
            from .models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento
            from .models.base import Socio
            from .models.fiscal import NotaFiscal
            
            if 'socio' in self.fields:
                self.fields['socio'].queryset = Socio.objects.none()
            if 'descricao_movimentacao' in self.fields:
                self.fields['descricao_movimentacao'].queryset = DescricaoMovimentacaoFinanceira.objects.none()
            if 'instrumento_bancario' in self.fields:
                self.fields['instrumento_bancario'].queryset = MeioPagamento.objects.none()
            if 'nota_fiscal' in self.fields:
                self.fields['nota_fiscal'].queryset = NotaFiscal.objects.none()
        
        # Configurar labels personalizados
        if 'descricao_movimentacao' in self.fields:
            self.fields['descricao_movimentacao'].label_from_instance = lambda obj: obj.descricao or f"Descrição #{obj.pk}"
        
        if 'instrumento_bancario' in self.fields:
            self.fields['instrumento_bancario'].label_from_instance = lambda obj: obj.nome or f"Instrumento #{obj.pk}"
        
        if 'socio' in self.fields:
            self.fields['socio'].label_from_instance = lambda obj: obj.pessoa.name if obj.pessoa else f"Sócio #{obj.pk}"
        
        if 'nota_fiscal' in self.fields:
            self.fields['nota_fiscal'].label_from_instance = lambda obj: f"NF {obj.numero} - {obj.dtEmissao.strftime('%d/%m/%Y')}" if obj.numero else f"NF #{obj.pk}"
        
        if 'data_movimentacao' in self.fields:
            self.fields['data_movimentacao'].input_formats = ['%Y-%m-%d']
    
    def clean_valor(self):
        """Validação e limpeza do campo valor"""
        valor = self.cleaned_data.get('valor')
        
        if valor is None:
            raise forms.ValidationError('Este campo é obrigatório.')
        
        # Converter string para decimal se necessário
        if isinstance(valor, str):
            # Remover espaços e substituir vírgula por ponto
            valor = valor.strip().replace(',', '.')
            try:
                valor = float(valor)
            except ValueError:
                raise forms.ValidationError('Valor inválido. Use formato: 1500.00 ou -800.50')
        
        # Validar que não seja zero
        if valor == 0:
            raise forms.ValidationError('O valor não pode ser zero.')
        
        return valor

    class Meta:
        model = MovimentacaoContaCorrente
        fields = [
            'data_movimentacao',
            'descricao_movimentacao', 
            'socio',
            'valor',
            'historico_complementar',
            'instrumento_bancario',
            'numero_documento_bancario',
            'nota_fiscal',
            'conciliado',
            'data_conciliacao'
        ]
        widgets = {
            'data_movimentacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'valor': forms.TextInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex: 1500.00 ou -800.50'}),
            'historico_complementar': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'numero_documento_bancario': forms.TextInput(attrs={'class': 'form-control'}),
            'conciliado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_conciliacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
