from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models.base import Empresa, Socio, Pessoa
from .models.fiscal import Aliquotas
from .models.despesas import GrupoDespesa, ItemDespesa
from .models.financeiro import DescricaoMovimentacaoFinanceira

User = get_user_model()

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active']

class TenantLoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput)

class AccountSelectionForm(forms.Form):
    conta_id = forms.IntegerField(widget=forms.HiddenInput)

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)  # só email, remova 'username' se não for usado

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def save(self, commit=True):
        user = super().save(commit=commit)
        from medicos.models import Conta, ContaMembership, Licenca
        # Cria Conta com nome baseado no e-mail do usuário
        conta_nome = f"Conta de {user.email.split('@')[0]}"
        conta = Conta.objects.create(name=conta_nome, created_by=user)
        # Cria vínculo admin
        ContaMembership.objects.create(conta=conta, user=user, role='admin', created_by=user)
        # Cria licença básica válida
        from datetime import date, timedelta
        hoje = date.today()
        Licenca.objects.create(
            conta=conta,
            plano='BASICO',
            data_inicio=hoje - timedelta(days=1),
            data_fim=hoje + timedelta(days=365),
            ativa=True,
            limite_usuarios=10,
            created_by=user
        )
        # Desativa usuário até confirmação
        user.is_active = False
        user.save()
        # Envia e-mail de ativação
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.SITE_URL}/medicos/auth/activate/{uid}/{token}/"
        send_mail(
            'Ative sua conta',
            f'Clique no link para ativar sua conta: {activation_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return user

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'name',  # Razão social
            'cnpj',
            'regime_tributario',
        ]
        widgets = {
            'cnpj': forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        from crispy_forms.layout import Layout, Row, Column, Submit
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('cnpj', css_class='col-md-6'),
            ),
            Row(
                Column('regime_tributario', css_class='col-md-6'),
            ),
        )
        # Garante que o botão sempre aparece
        if not any(isinstance(inp, Submit) for inp in getattr(self.helper, 'inputs', [])):
            self.helper.add_input(Submit('submit', 'Salvar', css_class='btn btn-primary'))

class SocioCPFForm(forms.Form):
    cpf = forms.CharField(label='CPF', max_length=14, widget=forms.TextInput(attrs={'placeholder': '000.000.000-00'}))

class SocioPessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ['name', 'cpf', 'rg', 'data_nascimento', 'telefone', 'celular', 'email', 'crm', 'especialidade', 'ativo']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        self.empresa = empresa

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Garante que a conta seja definida
        if self.empresa:
            instance.conta = self.empresa.conta
        if commit:
            instance.save()
        return instance

class SocioForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = ['ativo', 'data_entrada', 'data_saida', 'observacoes']
        widgets = {
            'data_entrada': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_entrada'].input_formats = ['%Y-%m-%d']
        self.fields['data_saida'].input_formats = ['%Y-%m-%d']

class AliquotaForm(forms.ModelForm):
    class Meta:
        model = Aliquotas
        fields = [
            'ISS', 'PIS', 'COFINS',
            'IRPJ_BASE_CAL', 'IRPJ_ALIQUOTA_OUTROS', 'IRPJ_ALIQUOTA_CONSULTA',
            'IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL', 'IRPJ_ADICIONAL',
            'CSLL_BASE_CAL', 'CSLL_ALIQUOTA_OUTROS', 'CSLL_ALIQUOTA_CONSULTA',
            'ativa', 'data_vigencia_inicio', 'data_vigencia_fim',
            'observacoes'
        ]
        widgets = {
            'data_vigencia_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_vigencia_fim': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_vigencia_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['data_vigencia_fim'].input_formats = ['%Y-%m-%d']
        # Garante que os valores iniciais sejam exibidos corretamente
        if self.instance and self.instance.pk:
            if self.instance.data_vigencia_inicio:
                self.fields['data_vigencia_inicio'].initial = self.instance.data_vigencia_inicio.strftime('%Y-%m-%d')
            if self.instance.data_vigencia_fim:
                self.fields['data_vigencia_fim'].initial = self.instance.data_vigencia_fim.strftime('%Y-%m-%d')

class GrupoDespesaForm(forms.ModelForm):
    class Meta:
        model = GrupoDespesa
        fields = ['codigo', 'descricao', 'tipo_rateio']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 2}),
        }

class ItemDespesaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].label_from_instance = lambda obj: obj.descricao
    class Meta:
        model = ItemDespesa
        fields = ['codigo', 'descricao', 'grupo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'grupo': forms.Select(attrs={'class': 'form-control'}),
        }

class DescricaoMovimentacaoFinanceiraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = DescricaoMovimentacaoFinanceira
        fields = [
            'descricao', 'tipo_movimentacao', 'exige_documento', 'exige_aprovacao',
            'codigo_contabil', 'possui_retencao_ir', 'percentual_retencao_ir', 'uso_frequente', 'observacoes'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }
