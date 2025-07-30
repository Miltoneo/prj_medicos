from django import forms
from medicos.models.financeiro import MeioPagamento

class MeioPagamentoForm(forms.ModelForm):
    class Meta:
        model = MeioPagamento
        fields = ['codigo', 'nome']

    def save(self, commit=True, conta=None):
        instance = super().save(commit=False)
        if conta is not None:
            instance.conta = conta
        if commit:
            instance.save()
        return instance
