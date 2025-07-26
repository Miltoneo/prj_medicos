from django import forms
from medicos.models.base import CustomUser

class UserInviteForm(forms.ModelForm):
    def validate_unique(self):
        # Ignora validação de unicidade se usuário já existe e está inativo
        if hasattr(self, '_user_existente') and self._user_existente and not self._user_existente.is_active:
            return
        super().validate_unique()
    class Meta:
        model = CustomUser
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = CustomUser.objects.filter(email=email).first()
        self._user_existente = user
        # Permite reenvio para usuário inativo, bloqueia apenas ativos
        if user and user.is_active:
            raise forms.ValidationError('Já existe um usuário ativo com este endereço de e-mail.')
        return email

    def save(self, commit=True):
        # Se já existe usuário inativo, apenas retorna o usuário, não altera nome
        if hasattr(self, '_user_existente') and self._user_existente and not self._user_existente.is_active:
            user = self._user_existente
            user.is_active = False
            if commit:
                user.save()
            return user
        return super().save(commit=commit)
