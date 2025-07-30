from django import forms
from medicos.models.base import CustomUser

class UserInviteForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'nome']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail do usuário'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
        }
