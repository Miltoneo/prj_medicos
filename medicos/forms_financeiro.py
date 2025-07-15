from django import forms
from .models.financeiro import Financeiro

class FinanceiroForm(forms.ModelForm):
    class Meta:
        model = Financeiro
        fields = '__all__'
