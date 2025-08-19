from django import forms
from .models.financeiro import AplicacaoFinanceira

class AplicacaoFinanceiraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Corrige o valor do campo vindo do input type=month para o formato aceito pelo DateField
        if 'data_referencia' in self.data:
            val = self.data['data_referencia']
            if len(val) == 7 and val[4] == '-':
                self.data = self.data.copy()
                self.data['data_referencia'] = f"{val}-01"
        # Ajusta o valor inicial para o formato YYYY-MM ao editar
        if self.instance and self.instance.pk and self.instance.data_referencia:
            self.initial['data_referencia'] = self.instance.data_referencia.strftime('%Y-%m')
    def clean_data_referencia(self):
        """
        Aceita input 'YYYY-MM' (type=month) e converte para date 'YYYY-MM-01'.
        Aceita também objetos date/datetime.
        """
        data = self.cleaned_data['data_referencia']
        import datetime
        if isinstance(data, str) and len(data) == 7 and data[4] == '-' and data[:4].isdigit() and data[5:7].isdigit():
            try:
                return datetime.date(int(data[:4]), int(data[5:7]), 1)
            except Exception:
                raise forms.ValidationError('Informe uma data válida (mês/ano).')
        elif isinstance(data, datetime.datetime):
            return data.date()
        elif isinstance(data, datetime.date):
            return data
        raise forms.ValidationError('Informe uma data válida (mês/ano).')
    class Meta:
        model = AplicacaoFinanceira
        fields = ['data_referencia', 'saldo', 'rendimentos', 'ir_cobrado', 'descricao']
        widgets = {
            'data_referencia': forms.DateInput(attrs={'type': 'month', 'class': 'form-control form-control-sm', 'style': 'max-width: 140px;'}),
            'saldo': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'style': 'max-width: 120px;'}),
            'rendimentos': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'style': 'max-width: 120px;'}),
            'ir_cobrado': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'style': 'max-width: 120px;'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'maxlength': '60', 'style': 'max-width: 300px;'}),
        }
