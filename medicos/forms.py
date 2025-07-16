from django import forms
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.base import Socio
import django_filters

# Formulário para rateio de nota fiscal
class NotaFiscalRateioMedicoForm(forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Só calcula percentual se nota_fiscal estiver presente
        if hasattr(instance, 'nota_fiscal') and instance.nota_fiscal and instance.valor_bruto_medico is not None:
            total = instance.nota_fiscal.val_bruto
            if total and total > 0:
                instance.percentual_participacao = (instance.valor_bruto_medico / total) * 100
        if commit:
            instance.save()
        return instance
    class Meta:
        model = NotaFiscalRateioMedico
        fields = [
            'medico', 'valor_bruto_medico'
        ]


# Filter para listagem de notas fiscais para rateio
import django_filters
from medicos.models.fiscal import NotaFiscal

class NotaFiscalRateioFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(field_name="numero", lookup_expr="icontains", label="Nº NF")
    tomador = django_filters.CharFilter(field_name="tomador", lookup_expr="icontains", label="Tomador")
    cnpj_tomador = django_filters.CharFilter(field_name="cnpj_tomador", lookup_expr="icontains", label="CNPJ do Tomador")
    class Meta:
        model = NotaFiscal
        fields = ['numero', 'tomador', 'cnpj_tomador']

# Filter para rateio de nota fiscal por médico
class NotaFiscalRateioMedicoFilter(django_filters.FilterSet):
    medico = django_filters.ModelChoiceFilter(queryset=Socio.objects.all(), label="Médico")
    class Meta:
        model = NotaFiscalRateioMedico
        fields = ['medico']

from django import forms
from .models.base import Socio, Pessoa

class SocioPessoaCompletaForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = ['name', 'cpf', 'rg', 'data_nascimento', 'telefone', 'celular', 'email', 'crm', 'especialidade', 'pessoa_ativo', 'socio_ativo', 'data_entrada', 'data_saida', 'observacoes']
    """
    Formulário único para cadastro de sócio e pessoa.
    """
    name = forms.CharField(label='Nome', max_length=255)
    cpf = forms.CharField(label='CPF', max_length=14)
    rg = forms.CharField(label='RG', max_length=20, required=False)
    data_nascimento = forms.DateField(label='Data de Nascimento', widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)
    celular = forms.CharField(label='Celular', max_length=20, required=False)
    email = forms.EmailField(label='Email', required=False)
    crm = forms.CharField(label='CRM', max_length=20, required=False)
    especialidade = forms.CharField(label='Especialidade', max_length=100, required=False)
    pessoa_ativo = forms.BooleanField(label='Pessoa Ativa', required=False)
    socio_ativo = forms.BooleanField(label='Sócio Ativo', required=False)
    data_entrada = forms.DateField(label='Data de Entrada', widget=forms.DateInput(attrs={'type': 'date'}))
    data_saida = forms.DateField(label='Data de Saída', widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    observacoes = forms.CharField(label='Observações', widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_entrada'].input_formats = ['%Y-%m-%d']
        self.fields['data_saida'].input_formats = ['%Y-%m-%d']

    def save(self, empresa, commit=True):
        pessoa_data = {
            'name': self.cleaned_data['name'],
            'cpf': self.cleaned_data['cpf'],
            'rg': self.cleaned_data.get('rg'),
            'data_nascimento': self.cleaned_data.get('data_nascimento'),
            'telefone': self.cleaned_data.get('telefone'),
            'celular': self.cleaned_data.get('celular'),
            'email': self.cleaned_data.get('email'),
            'crm': self.cleaned_data.get('crm'),
            'especialidade': self.cleaned_data.get('especialidade'),
            'ativo': self.cleaned_data.get('pessoa_ativo', True),
            'conta': empresa.conta,
        }
        pessoa, _ = Pessoa.objects.update_or_create(cpf=pessoa_data['cpf'], defaults=pessoa_data)
        socio = Socio(
            empresa=empresa,
            conta=empresa.conta,
            pessoa=pessoa,
            ativo=self.cleaned_data.get('socio_ativo', True),
            data_entrada=self.cleaned_data['data_entrada'],
            data_saida=self.cleaned_data.get('data_saida'),
            observacoes=self.cleaned_data.get('observacoes', ''),
        )
        if commit:
            socio.save()
        return socio

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

class SocioForm(forms.ModelForm):
    """
    Formulário de cadastro/edição de sócio. Apenas campos editáveis pelo usuário.
    Os vínculos (conta, empresa, pessoa) são definidos na view.
    """
    class Meta:
        model = Socio
        fields = ['ativo', 'data_entrada', 'data_saida', 'observacoes']
        widgets = {
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_entrada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Observações'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_entrada'].input_formats = ['%Y-%m-%d']
        self.fields['data_saida'].input_formats = ['%Y-%m-%d']

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
        # Garante que a empresa seja definida
        if self.empresa:
            instance.empresa = self.empresa
        if commit:
            instance.save()
        return instance

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
        self.empresa = kwargs.pop('empresa', None)
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
        self.fields['codigo'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Código',
            'style': 'max-width: 100px;'
        })
        self.fields['grupo'].widget.attrs.update({
            'class': 'form-select',
            'style': 'max-width: 300px;'
        })
        self.fields['descricao'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Descrição detalhada',
            'style': 'min-width: 400px; max-width: 900px;'
        })

    class Meta:
        model = ItemDespesa
        fields = ['codigo', 'grupo', 'descricao']  # 'grupo' já está acima de 'descricao'
        widgets = {
            'codigo': forms.TextInput(),
            'grupo': forms.Select(),
            'descricao': forms.Textarea(),
        }

class DescricaoMovimentacaoFinanceiraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.empresa:
            instance.empresa = self.empresa
        if commit:
            instance.save()
        return instance

    class Meta:
        model = DescricaoMovimentacaoFinanceira
        fields = [
            'descricao', 'codigo_contabil', 'observacoes'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'style': 'min-width: 400px; max-width: 900px;',
                'placeholder': 'Descrição detalhada'
            }),
            'codigo_contabil': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'max-width: 200px;',
                'placeholder': 'Código contábil'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'style': 'min-width: 300px; max-width: 600px;',
                'placeholder': 'Observações'
            }),
        }
