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
from .models.financeiro import CategoriaMovimentacao

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
            empresa_choices = kwargs.pop('empresa_choices',())
            data_inicial= kwargs.pop('data_inicial',())

            super().__init__(*args, **kwargs)
            if empresa_choices:
                self.fields['empresa_destinataria'].choices = empresa_choices
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
                    Column('empresa_destinataria', css_class='col-md-4'),              
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
                   'empresa_destinataria', # changed from 'socio'
                   'tipo_aliquota',
                   "numero", 
                   "serie",
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
                    'empresa_destinataria': Select2Widget,
                    }
        localized_fiels = '__all__'

#-------------------------------------------------------------
class Edit_Financeiro_Form(ModelForm):
    
    data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        socio_choices = kwargs.pop('socio_choices', ())
        meio_pagamento_choices = kwargs.pop('meio_pagamento_choices', ())
        descricao_choices = kwargs.pop('descricao_choices', ())
        data = kwargs.pop('data_inicial', ())

        super().__init__(*args, **kwargs)
        self.fields['socio'].choices = socio_choices
        
        # Configurar choices para meio de pagamento se fornecidas
        if meio_pagamento_choices:
            self.fields['meio_pagamento'].choices = meio_pagamento_choices
            
        # Configurar choices para descrições se fornecidas
        if descricao_choices:
            self.fields['descricao'].choices = descricao_choices

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('data', css_class='col-md-4'),
                Column('tipo', css_class='col-md-4'),
            ),
            Row(
                Column('descricao', css_class='col-md-8'),
                Column('socio', css_class='col-md-4'),
            ),
            Row(
                Column('valor', css_class='col-md-4'),
                Column('meio_pagamento', css_class='col-md-4'),
                Column('numero_documento', css_class='col-md-4'),
            ),
            Row(
                Column('taxa_aplicada', css_class='col-md-4'),
                Column('valor_liquido_recebido', css_class='col-md-4'),
            ),
            Row(
                Column('observacoes', css_class='col-md-12'),
            ),
        )

    class Meta:
        model = Financeiro
        fields = [
            'data', 'tipo', 'descricao', 'socio', 'valor',
            'meio_pagamento', 'taxa_aplicada', 'valor_liquido_recebido',
            'numero_documento', 'observacoes'
        ]
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
        localized_fields = '__all__'

# Edit_Desc_Mov_Financeira_Form removed - replaced by DescricaoMovimentacaoForm

#-----------------------------------------------------
class AliquotasForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper(self)
            self.helper.layout = Layout(
                Row(
                    Column('ISS_CONSULTAS', css_class='col-md-4'),   
                    Column('ISS_PLANTAO', css_class='col-md-4'),    
                    Column('ISS_OUTROS', css_class='col-md-4'),    
                ),
                Row(
                    Column('PIS', css_class='col-md-4'),    
                    Column('COFINS', css_class='col-md-4'),    
                    Column('IR', css_class='col-md-4'),   
                ),
                Row(
                    Column('CSLL', css_class='col-md-4'),   
                    Column('data_vigencia_inicio', css_class='col-md-4'),    
                    Column('data_vigencia_fim', css_class='col-md-4'),      
                ),
                Row(
                    Column('observacoes', css_class='col-md-12'),     
                ),
            )

    class Meta:
        model = Aliquotas
        fields = [
                'ISS_CONSULTAS', 
                'ISS_PLANTAO', 
                'ISS_OUTROS', 
                'PIS', 
                'COFINS', 
                'IR',
                'CSLL',
                'data_vigencia_inicio',
                'data_vigencia_fim',
                'observacoes',
        ]
        widgets = {
            'data_vigencia_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_vigencia_fim': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

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


#-------------------------------------------------------------
class MeioPagamentoForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('codigo', css_class='col-md-4'),
                Column('nome', css_class='col-md-8'),
            ),
            Row(
                Column('descricao', css_class='col-md-12'),
            ),
            Row(
                Column('taxa_percentual', css_class='col-md-3'),
                Column('taxa_fixa', css_class='col-md-3'),
                Column('prazo_compensacao_dias', css_class='col-md-3'),
                Column('tipo_movimentacao', css_class='col-md-3'),
            ),
            Row(
                Column('valor_minimo', css_class='col-md-4'),
                Column('valor_maximo', css_class='col-md-4'),
                Column('horario_limite', css_class='col-md-4'),
            ),
            Row(
                Column('data_inicio_vigencia', css_class='col-md-4'),
                Column('data_fim_vigencia', css_class='col-md-4'),
                Column('ativo', css_class='col-md-4'),
            ),
            Row(
                Column('exige_documento', css_class='col-md-4'),
                Column('exige_aprovacao', css_class='col-md-4'),
            ),
            Row(
                Column('observacoes', css_class='col-md-12'),
            ),
        )

    class Meta:
        model = MeioPagamento
        fields = [
            'codigo', 'nome', 'descricao',
            'taxa_percentual', 'taxa_fixa', 
            'valor_minimo', 'valor_maximo',
            'prazo_compensacao_dias', 'horario_limite',
            'tipo_movimentacao', 
            'data_inicio_vigencia', 'data_fim_vigencia',
            'ativo', 'exige_documento', 'exige_aprovacao',
            'observacoes'
        ]
        widgets = {
            'data_inicio_vigencia': forms.DateInput(attrs={'type': 'date'}),
            'data_fim_vigencia': forms.DateInput(attrs={'type': 'date'}),
            'horario_limite': forms.TimeInput(attrs={'type': 'time'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
        localized_fields = '__all__'

#-------------------------------------------------------------
class DescricaoMovimentacaoForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        # Extrair a conta se fornecida
        conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar categorias de movimentação pela conta
        if conta:
            self.fields['categoria_movimentacao'].queryset = CategoriaMovimentacao.objects.filter(
                conta=conta,
                ativa=True
            ).order_by('natureza', 'ordem', 'nome')
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('nome', css_class='col-md-8'),
                Column('categoria_movimentacao', css_class='col-md-4'),
            ),
            Row(
                Column('descricao', css_class='col-md-12'),
            ),
            Row(
                Column('tipo_movimentacao', css_class='col-md-4'),
                Column('uso_frequente', css_class='col-md-2'),
                Column('ativa', css_class='col-md-2'),
                Column('codigo_contabil', css_class='col-md-4'),
            ),
            Row(
                Column('exige_documento', css_class='col-md-3'),
                Column('exige_aprovacao', css_class='col-md-3'),
                Column('possui_retencao_ir', css_class='col-md-3'),
                Column('percentual_retencao_ir', css_class='col-md-3'),
            ),
            Row(
                Column('observacoes', css_class='col-md-12'),
            ),
        )

    class Meta:
        model = DescricaoMovimentacao
        fields = [
            'nome', 'descricao', 'categoria_movimentacao',
            'tipo_movimentacao', 'uso_frequente', 'ativa',
            'exige_documento', 'exige_aprovacao',
            'codigo_contabil', 'possui_retencao_ir', 'percentual_retencao_ir',
            'observacoes'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
        localized_fields = '__all__'

# Formulário para NotaFiscal com sistema integrado de MeioPagamento
class NotaFiscalForm(ModelForm):
    """
    Formulário para criação/edição de Notas Fiscais com sistema 
    integrado de meios de pagamento cadastrados pelo usuário
    """
    
    def __init__(self, *args, **kwargs):
        # Extrair conta se fornecida
        conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        # Configurar helper do Crispy Forms
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('numero', css_class='col-md-4'),
                Column('serie', css_class='col-md-2'),
                Column('tipo_aliquota', css_class='col-md-6'),
            ),
            Row(
                Column('empresa_destinataria', css_class='col-md-8'),
                Column('tomador', css_class='col-md-4'),
            ),
            Row(
                Column('dtEmissao', css_class='col-md-4'),
                Column('dtVencimento', css_class='col-md-4'),
                Column('dtRecebimento', css_class='col-md-4'),
            ),
            Div(
                Row(
                    Column('val_bruto', css_class='col-md-6'),
                    Column('val_liquido', css_class='col-md-6'),
                ),
                Row(
                    Column('val_ISS', css_class='col-md-3'),
                    Column('val_PIS', css_class='col-md-3'),
                    Column('val_COFINS', css_class='col-md-3'),
                    Column('val_IR', css_class='col-md-3'),
                ),
                Row(
                    Column('val_CSLL', css_class='col-md-12'),
                ),
                css_class='border p-3 mb-3',
            ),
            Div(
                Row(
                    Column('status_recebimento', css_class='col-md-4'),
                    Column('meio_pagamento', css_class='col-md-8'),
                ),
                Row(
                    Column('valor_recebido', css_class='col-md-6'),
                    Column('numero_documento_recebimento', css_class='col-md-6'),
                ),
                Row(
                    Column('detalhes_recebimento', css_class='col-md-12'),
                ),
                css_class='border p-3 mb-3',
            ),
            Row(
                Column('descricao_servicos', css_class='col-md-8'),
                Column('observacoes', css_class='col-md-4'),
            ),
        )
        
        # Filtrar meios de pagamento por conta
        if conta:
            self.fields['meio_pagamento'].queryset = MeioPagamento.objects.filter(
                conta=conta,
                ativo=True,
                tipo_movimentacao__in=['credito', 'ambos']
            ).order_by('nome')
        else:
            # Se não há conta, mostrar apenas alguns meios como exemplo
            self.fields['meio_pagamento'].queryset = MeioPagamento.objects.filter(
                ativo=True,
                tipo_movimentacao__in=['credito', 'ambos']
            )[:10]
        
        # Configurar widgets
        self.fields['dtEmissao'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['dtVencimento'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['dtRecebimento'].widget = forms.DateInput(attrs={'type': 'date'})
        
        # Configurar required fields
        self.fields['meio_pagamento'].required = False
        self.fields['valor_recebido'].required = False
        self.fields['dtRecebimento'].required = False
        
        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if field_name.startswith('val_'):
                field.widget.attrs.update({'class': 'form-control money-input'})
    
    def clean(self):
        """Validações personalizadas do formulário"""
        cleaned_data = super().clean()
        status_recebimento = cleaned_data.get('status_recebimento')
        meio_pagamento = cleaned_data.get('meio_pagamento')
        dtRecebimento = cleaned_data.get('dtRecebimento')
        valor_recebido = cleaned_data.get('valor_recebido')
        val_liquido = cleaned_data.get('val_liquido')
        
        # Se status não é pendente, deve ter meio de pagamento
        if status_recebimento != 'pendente' and not meio_pagamento:
            raise forms.ValidationError("Meio de pagamento é obrigatório quando status não é 'pendente'.")
        
        # Se há meio de pagamento, deve ter data de recebimento
        if meio_pagamento and not dtRecebimento:
            raise forms.ValidationError("Data de recebimento é obrigatória quando meio de pagamento é definido.")
        
        # Validar valor recebido vs valor líquido
        if valor_recebido and val_liquido and valor_recebido > val_liquido:
            raise forms.ValidationError("Valor recebido não pode ser maior que o valor líquido da nota.")
        
        return cleaned_data
    
    class Meta:
        model = NotaFiscal
        fields = [
            'numero', 'serie', 'empresa_destinataria', 'tomador',
            'tipo_aliquota', 'dtEmissao', 'dtVencimento', 'dtRecebimento',
            'val_bruto', 'val_liquido', 'val_ISS', 'val_PIS', 'val_COFINS', 
            'val_IR', 'val_CSLL', 'status_recebimento', 'meio_pagamento',
            'valor_recebido', 'numero_documento_recebimento', 'detalhes_recebimento',
            'descricao_servicos', 'observacoes'
        ]
        widgets = {
            'empresa_destinataria': Select2Widget,
            'meio_pagamento': Select2Widget,
            'descricao_servicos': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
            'detalhes_recebimento': forms.Textarea(attrs={'rows': 2}),
        }


class NotaFiscalRecebimentoForm(ModelForm):
    """
    Formulário simplificado para confirmação de recebimento de Nota Fiscal
    """
    
    def __init__(self, *args, **kwargs):
        conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('dtRecebimento', css_class='col-md-6'),
                Column('meio_pagamento', css_class='col-md-6'),
            ),
            Row(
                Column('valor_recebido', css_class='col-md-6'),
                Column('numero_documento_recebimento', css_class='col-md-6'),
            ),
            Row(
                Column('detalhes_recebimento', css_class='col-md-12'),
            ),
            Submit('submit', 'Confirmar Recebimento', css_class='btn btn-success')
        )
        
        # Filtrar meios de pagamento por conta
        if conta:
            self.fields['meio_pagamento'].queryset = MeioPagamento.objects.filter(
                conta=conta,
                ativo=True,
                tipo_movimentacao__in=['credito', 'ambos']
            ).order_by('nome')
        
        # Configurar campos
        self.fields['dtRecebimento'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['meio_pagamento'].required = True
        self.fields['dtRecebimento'].required = True
        
        # Se há instância, pré-preencher valor recebido com valor líquido
        if self.instance and self.instance.pk and not self.instance.valor_recebido:
            self.fields['valor_recebido'].initial = self.instance.val_liquido
    
    def clean_meio_pagamento(self):
        """Validar meio de pagamento"""
        meio = self.cleaned_data.get('meio_pagamento')
        if meio and self.instance:
            # Verificar se pode usar este meio para esta NF
            if not self.instance.pode_usar_meio_pagamento(meio):
                raise forms.ValidationError(f"O meio '{meio.nome}' não pode ser usado para esta nota fiscal.")
        return meio
    
    class Meta:
        model = NotaFiscal
        fields = ['dtRecebimento', 'meio_pagamento', 'valor_recebido', 
                 'numero_documento_recebimento', 'detalhes_recebimento']
        widgets = {
            'meio_pagamento': Select2Widget,
            'detalhes_recebimento': forms.Textarea(attrs={'rows': 2}),
        }