# import the standard Django Forms 
# from built-in library 
from django import forms
from django.forms import ModelForm, ChoiceField,  DateField, widgets
from django.forms.widgets import HiddenInput

from django_select2 import forms as s2forms
from django_select2.forms import Select2MultipleWidget, Select2Widget

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, Row, Column

from .models import *

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.contrib.auth import get_user_model

User = get_user_model()

# ---------------------------------------------------------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username')

# ---------------------------------------------------------
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail", max_length=254)

#-------------------------------------------------------------
# creating a form   
class InputForm(forms.Form):  
    
    first_name = forms.CharField(max_length = 200)  
    last_name = forms.CharField(max_length = 200)  
    roll_number = forms.IntegerField(  
                     help_text = "Enter 6 digit roll number"
                     )  
    password = forms.CharField(widget = forms.PasswordInput())  

#-------------------------------------------------------------
class Edit_NotaFiscal_Form(ModelForm):
    
    dtEmissao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    dtRecebimento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
            socio_choices = kwargs.pop('socio_choices',())
            data_inicial= kwargs.pop('data_inicial',())

            super().__init__(*args, **kwargs)
            self.fields['socio'].choices = socio_choices
            self.fields['dtRecebimento'].required = False

            self.helper = FormHelper(self)
            self.helper.layout = Layout(
                Row(
                    Column('numero', css_class='col-md-4'),                    
                    Column('tipo_aliquota', css_class='col-md-4'),

                ),
                Row(
                    Column('dtEmissao', css_class='col-md-4'),
                    Column('dtRecebimento', css_class='col-md-4'),
                ), 

                Row(
                    Column('tomador', css_class='col-md-4'),
                    Column('socio', css_class='col-md-4'),              
                ),  

                 Row(
                    Column('val_bruto', css_class='col-md-4'),
                
                ),  
                              
                Row(
                    Column('val_ISS', css_class='col-md-4'),
                    Column('val_PIS', css_class='col-md-4'),   
                    Column('val_COFINS', css_class='col-md-4'),
                    Column('val_IR', css_class='col-md-4'), 
                    Column('val_CSLL', css_class='col-md-4'),                                     
                ),  
                 Row(
                    Column('val_liquido', css_class='col-md-4'),                    
                ),         

                Div(
                    #Field('numero', wrapper_class='col-md-6 '), #css_class 
                    #Field('tipo_aliquota', wrapper_class='col-md-6 '),
                    #css_class='row',  # Optional, apply a row class to the entire div
                ))


    class Meta:
        model = NotaFiscal
        fields = [

                   'socio', #new
                   'tipo_aliquota',
                   "numero", 
                   "tomador", 
                   "dtEmissao",
                   'dtRecebimento', 
                   "val_bruto",
                   'val_ISS', 
                   'val_PIS', 
                   'val_COFINS', 
                   'val_IR', 
                   'val_CSLL',
                   'val_liquido', 
                  ]
        #exclude = ('fornecedor',)
        widgets = {
                    #'dtEmissao': widgets.DateInput(attrs={'type': 'date'}),
                    #'dtRecebimento': widgets.DateInput(attrs={'type': 'date'}),
                    'socio': Select2Widget,
                    }
        localized_fiels = '__all__'

#-------------------------------------------------------------
class Edit_Financeiro_Form(ModelForm):
    
    data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
            socio_choices = kwargs.pop('socio_choices',())
            data= kwargs.pop('data_inicial',())

            super().__init__(*args, **kwargs)
            self.fields['socio'].choices = socio_choices
            #self.fields['dtRecebimento'].required = False

            self.helper = FormHelper(self)
            self.helper.layout = Layout(
                Row(
                    Column('data', css_class='col-md-4'),                    
                    Column('tipo', css_class='col-md-4'),

                ),
                Row(
                    Column('descricao', css_class='col-md-10'),
                ), 

                 Row(
                    Column('socio', css_class='col-md-10'),
                ),  

                 Row(
                    Column('valor', css_class='col-md-4'),

                ),  
                              
                Div(
                    #Field('numero', wrapper_class='col-md-6 '), #css_class 
                    #Field('tipo_aliquota', wrapper_class='col-md-6 '),
                    #css_class='row',  # Optional, apply a row class to the entire div
                ))


    class Meta:
        model = Financeiro
        fields = [
                   'data', 
                   'tipo',
                   "descricao", 
                   "socio", 
                   "valor",
                  ]
        #exclude = ('fornecedor',)
        widgets = {
                    #'dtEmissao': widgets.DateInput(attrs={'type': 'date'}),
                    #'dtRecebimento': widgets.DateInput(attrs={'type': 'date'}),
                    #'notafiscal': Select2Widget,
                    }
        localized_fiels = '__all__'

#-------------------------------------------------------------
class Edit_Desc_Mov_Financeira_Form(ModelForm):
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper(self)
            self.helper.layout = Layout(
                Row(
                    Column('id', css_class='col-md-4'),     
                    Column('descricao', css_class='col-md-10'),                    

                ),
                              
                Div(
                    #Field('numero', wrapper_class='col-md-6 '), #css_class 
                    #Field('tipo_aliquota', wrapper_class='col-md-6 '),
                    #css_class='row',  # Optional, apply a row class to the entire div
                ))


    class Meta:
        model = Desc_movimentacao_financeiro
        fields = [
                   'id',
                   'descricao', 
                    ]

#-----------------------------------------------------
class AlicotasForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper(self)
            self.helper.layout = Layout(
                Row(
                    Column('ISS', css_class='col-md-4'),   
                    Column('PIS', css_class='col-md-4'),    
                    Column('COFINS', css_class='col-md-4'),    
                ),
                Row(
                    Column('IRPJ_BASE_CAL', css_class='col-md-4'),   
                    Column('IRPJ_ALIC_1', css_class='col-md-4'),    
                    Column('IRPJ_ALIC_2', css_class='col-md-4'),   
                ),
                Row(
                    Column('CSLL_BASE_CAL', css_class='col-md-4'),   
                    Column('CSLL_ALIC_1', css_class='col-md-4'),    
                    Column('CSLL_ALIC_2', css_class='col-md-4'),      
                ),
                Row(
                    Column('IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL', css_class='col-md-4'),     
                    Column('IRPJ_ADICIONAL', css_class='col-md-4'),    
                ),
            )

    class Meta:
        model = Alicotas
        fields = [
                'ISS', 
                'PIS', 
                'COFINS', 
                'IRPJ_BASE_CAL', 
                'IRPJ_ALIC_1',
                'IRPJ_ALIC_2',  
                'IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL',
                'IRPJ_ADICIONAL',  
                'CSLL_BASE_CAL', 
                'CSLL_ALIC_1',
                'CSLL_ALIC_2',  
        ]

#--------------------------------------------------------
class EmpresaForm(ModelForm):
    class Meta:
        model = Empresa
        fields = [
                'CNPJ', 
                'name', 
                'tipo_regime',
                  ]

#------------------------------------------------------
class PessoaForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(PessoaForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
                            Row(
                                Column('CPF', css_class='col-md-4'),
                                Column('name', css_class='col-md-8'),
                            ))

    class Meta:
        model = Pessoa
        fields = [
                    'CPF', 
                    'name', 
                  ]

#-------------------------------------------------------
class SocioForm(ModelForm):
    class Meta:
        model = Socio
        fields = [
                'empresa', 
                'pessoa', 
                  ]
        
#--------------------------------------------------------
class Despesa_Grupo_Form(ModelForm):
    class Meta:
        model = Despesa_Grupo
        fields =  "__all__"

#--------------------------------------------------------
class Despesa_Item_Form(ModelForm):
    class Meta:
        model = Despesa_Item
        fields =  "__all__"

#--------------------------------------------------------
class MyWidget(s2forms.Select2Widget):
    model= Despesa_Item,
    search_fields = [
        'grupo__icontains',
        'descricao__icontains',
    ]

class Despesa_Form(forms.ModelForm):

    """ funciona
    item = forms.ChoiceField(
            widget=s2forms.ModelSelect2Widget(
                model= Despesa_Item,
                search_fields=['descricao__icontains']
            )
        )
    """
    data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):

        data_inicial= kwargs.pop('data_inicial',())
        
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        #self.fields['data'].initial = data_inicial        

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('data', css_class='col-md-4'),                    
                Column('item', css_class='col-md-6'),
                Column('valor', css_class='col-md-4'),                    
                Column('descricao', css_class='col-md-6'),
            ))


    class Meta:
        model = Despesa
        #fields =  "__all__"
        fields =  ('data', 'item','valor','descricao', )
        #exclude = ('empresa',)
        widgets = {
                    #'item': Select2Widget funciona
                    'item': MyWidget,
                    }
        
#-------------------------------------------------------------------
class Despesa_socio_rateio_Form(forms.ModelForm):


    class Meta:
        
        model = Despesa_socio_rateio
        fields =  ('despesa', 'percentual', )

        #exclude = ('empresa',)

#-------------------------------------------------------------------
class Rendimentos(forms.ModelForm):

    #data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', format:'%d/%m/%Y' }))
    data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        data_inicial= kwargs.pop('data_inicial',())
        super(Rendimentos, self).__init__(*args, **kwargs)
        #super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.initial['data'] = self.instance.data.isoformat()  

    class Meta:
        
        model = Aplic_financeiras
        fields =  ('data', 'rendimentos', 'irrf', 'descricao')


# ============================================================
# NOVOS FORMULÁRIOS PARA ORGANIZAÇÃO E MEMBROS
# ============================================================

# Formulário para criar uma nova organização
# class OrganizationCreateForm(forms.ModelForm):
#     class Meta:
#         model = Organization
#         fields = ['name', 'cnpj']
#         labels = {
#             'name': 'Nome da Organização',
#             'cnpj': 'CNPJ (opcional)'
#         }

# # Formulário para convidar novo membro
# class InviteMemberForm(forms.Form):
#     email = forms.EmailField(label="E-mail do novo membro")
#     role = forms.ChoiceField(
#         choices=OrganizationMembership.ROLE_CHOICES,
#         label="Papel na organização"
#     )

# # Formulário para atualizar o papel do membro
# class OrganizationMembershipUpdateForm(forms.ModelForm):
#     class Meta:
#         model = OrganizationMembership
#         fields = ['role']
#         labels = {
#             'role': 'Papel'
#         }

# === MODIFICAÇÃO PARA GESTÃO DE USUÁRIOS ===
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_staff', 'is_active']  # Ajuste conforme seu model


class TenantLoginForm(forms.Form):
    """
    Formulário de login multi-tenant
    """
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com',
            'required': True
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha',
            'required': True
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError('Email ou senha inválidos.')
                
        return cleaned_data


class AccountSelectionForm(forms.Form):
    """
    Formulário para seleção de conta
    """
    conta = forms.ModelChoiceField(
        queryset=Conta.objects.none(),
        label='Selecione a conta',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filtra apenas contas que o usuário tem acesso
            contas_ids = ContaMembership.objects.filter(
                user=user
            ).values_list('conta_id', flat=True)
            
            self.fields['conta'].queryset = Conta.objects.filter(
                id__in=contas_ids,
                licenca__ativa=True
            )


class InviteUserForm(forms.Form):
    """
    Formulário para convidar usuários para a conta
    """
    email = forms.EmailField(
        label='Email do usuário',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario@email.com'
        })
    )
    role = forms.ChoiceField(
        label='Papel na conta',
        choices=ContaMembership.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, conta=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta = conta
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Verifica se o email já é membro da conta
        if self.conta:
            existing_membership = ContaMembership.objects.filter(
                conta=self.conta,
                user__email=email
            ).exists()
            
            if existing_membership:
                raise forms.ValidationError('Este usuário já é membro desta conta.')
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Valida limite de usuários
        if self.conta:
            licenca = self.conta.licenca
            current_users = ContaMembership.objects.filter(conta=self.conta).count()
            
            if current_users >= licenca.limite_usuarios:
                raise forms.ValidationError(
                    f'Limite de usuários atingido. Plano atual permite {licenca.limite_usuarios} usuários.'
                )
        
        return cleaned_data


class UserRoleForm(forms.ModelForm):
    """
    Formulário para alterar papel do usuário na conta
    """
    class Meta:
        model = ContaMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'})
        }