
# Corrigir ordem dos imports para garantir que 'forms' esteja definido antes de ser usado
from django import forms
from medicos.models.despesas import ItemDespesaRateioMensal

# Formulário para configuração de rateio mensal de item de despesa
class ItemDespesaRateioMensalForm(forms.ModelForm):
    class Meta:
        model = ItemDespesaRateioMensal
        fields = ['item_despesa', 'socio', 'data_referencia', 'percentual_rateio', 'ativo', 'observacoes']
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
from django import forms
from datetime import date
from medicos.models.fiscal import NotaFiscal

class NotaFiscalRateioFilter(django_filters.FilterSet):
    mes_emissao = django_filters.CharFilter(
        label='Mês de Emissão',
        method='filter_mes_emissao',
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control'
        })
    )
    numero = django_filters.CharFilter(field_name="numero", lookup_expr="icontains", label="Nº NF")
    tomador = django_filters.CharFilter(field_name="tomador", lookup_expr="icontains", label="Tomador")
    cnpj_tomador = django_filters.CharFilter(field_name="cnpj_tomador", lookup_expr="icontains", label="CNPJ do Tomador")
    
    def filter_mes_emissao(self, queryset, name, value):
        """Filtrar por mês/ano de emissão"""
        if value:
            try:
                # value vem no formato YYYY-MM
                ano, mes = value.split('-')
                return queryset.filter(
                    dtEmissao__year=int(ano),
                    dtEmissao__month=int(mes)
                )
            except (ValueError, AttributeError):
                pass
        return queryset
    
    class Meta:
        model = NotaFiscal
        fields = ['mes_emissao', 'numero', 'tomador', 'cnpj_tomador']

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
        fields = ('email', 'first_name', 'last_name')  # solicita nome e sobrenome no registro

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['first_name'].label = 'Nome'
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self, commit=True, request=None):
        print('DEBUG: Entrou no save do CustomUserCreationForm')
        import logging
        logger = logging.getLogger('auth.debug')
        logger.info('Iniciando fluxo de registro de usuário.')
        user = super().save(commit=False)
        user.is_staff = True  # Garante que todo usuário registrado por este form será staff
        if commit:
            user.save()
        logger.info(f'Usuário criado: {user.email} (id={user.id})')
        from medicos.models import Conta, ContaMembership, Licenca
        from django.core.mail import send_mail
        from django.conf import settings
        from django.contrib import messages
        # Cria Conta com nome baseado no e-mail do usuário
        conta_nome = f"Conta de {user.email.split('@')[0]}"
        conta = Conta.objects.create(name=conta_nome, created_by=user)
        logger.info(f'Conta criada: {conta_nome} (id={conta.id})')
        # Cria vínculo admin
        ContaMembership.objects.create(conta=conta, user=user, role='admin', created_by=user)
        logger.info(f'Vínculo admin criado para usuário {user.email} na conta {conta_nome}')
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
        logger.info(f'Licença criada para conta {conta_nome}')
        # Desativa usuário até confirmação
        user.is_active = False
        user.save()
        logger.info(f'Usuário {user.email} desativado até confirmação.')
        # Envia e-mail de ativação
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.SITE_URL}/medicos/auth/activate/{uid}/{token}/"
        logger.info(f'Link de ativação gerado: {activation_link}')
        try:
            send_mail(
                'Ative sua conta',
                f'Clique no link para ativar sua conta: {activation_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f'E-mail de ativação enviado para {user.email} (remetente: {settings.DEFAULT_FROM_EMAIL})')
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail de ativação para {user.email}: {e}")
            if request is not None:
                messages.error(request, f"Erro ao enviar e-mail de ativação: {e}")
        return user

class EmpresaForm(forms.ModelForm):
    def clean_cnpj(self):
        """Valida o CNPJ informado no formulário."""
        import re
        from django.core.exceptions import ValidationError
        cnpj = self.cleaned_data.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '')
        if not cnpj.isdigit() or len(cnpj) != 14:
            raise ValidationError('CNPJ deve conter 14 dígitos numéricos.')
        if cnpj == cnpj[0] * 14:
            raise ValidationError('CNPJ inválido.')
        def calc_dv(cnpj, peso):
            soma = sum(int(a) * b for a, b in zip(cnpj, peso))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)
        dv1 = calc_dv(cnpj[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
        dv2 = calc_dv(cnpj[:12]+dv1, [6,5,4,3,2,9,8,7,6,5,4,3,2])
        if cnpj[-2:] != dv1+dv2:
            raise ValidationError('CNPJ inválido.')
        return self.cleaned_data['cnpj']
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
            'IRPJ_ALIQUOTA', 'IRPJ_PRESUNCAO_OUTROS', 'IRPJ_PRESUNCAO_CONSULTA',
            'IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL', 'IRPJ_ADICIONAL',
            'CSLL_ALIQUOTA', 'CSLL_PRESUNCAO_OUTROS', 'CSLL_PRESUNCAO_CONSULTA',
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
        # Capturar empresa do kwargs se fornecida
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # CORREÇÃO: Filtrar grupos de despesa apenas da empresa selecionada
        if empresa:
            from medicos.models.despesas import GrupoDespesa
            self.fields['grupo_despesa'].queryset = GrupoDespesa.objects.filter(empresa=empresa)
        
        self.fields['grupo_despesa'].label_from_instance = lambda obj: obj.descricao
        self.fields['codigo'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Código',
            'style': 'max-width: 200px;'
        })
        self.fields['grupo_despesa'].widget.attrs.update({
            'class': 'form-select',
            'style': 'max-width: 300px;'
        })
        self.fields['descricao'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descrição detalhada',
            'style': 'min-width: 400px; max-width: 900px;'
        })

    class Meta:
        model = ItemDespesa
        fields = ['codigo', 'grupo_despesa', 'descricao']  # 'grupo_despesa' já está acima de 'descricao'
        widgets = {
            'codigo': forms.TextInput(),
            'grupo_despesa': forms.Select(),
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
