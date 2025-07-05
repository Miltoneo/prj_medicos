from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# CONSTANTES GLOBAIS
app_name = 'medicos'

REGIME_TRIBUTACAO_COMPETENCIA = 1
REGIME_TRIBUTACAO_CAIXA = 2

NFISCAL_ALIQUOTA_CONSULTAS = 1
NFISCAL_ALIQUOTA_PLANTAO = 2
NFISCAL_ALIQUOTA_OUTROS = 3

TIPO_MOVIMENTACAO_CONTA_CREDITO = 1
TIPO_MOVIMENTACAO_CONTA_DEBITO = 2

DESC_MOVIMENTACAO_CREDITO_SALDO_MES_SEGUINTE = 'CREDITO SALDO MES ANTERIOR'
DESC_MOVIMENTACAO_DEBITO_IMPOSTO_PROVISIONADOS = 'DEBITO PAGAMENTO DE IMPOSTOS '

CODIGO_GRUPO_DESPESA_GERAL = 'GERAL'
CODIGO_GRUPO_DESPESA_FOLHA = 'FOLHA'
CODIGO_GRUPO_DESPESA_SOCIO = 'SOCIO'

TIPO_DESPESA_COM_RATEIO = 1
TIPO_DESPESA_SEM_RATEIO = 2

GRUPO_ITEM_COM_RATEIO = 1
GRUPO_ITEM_SEM_RATEIO = 2

#--------------------------------------------------------------
# MANAGERS CUSTOMIZADOS PARA SAAS
#--------------------------------------------------------------
class ContaScopedManager(models.Manager):
    """Manager que filtra automaticamente por conta (tenant)"""
    def get_queryset(self):
        if hasattr(self.model, '_current_conta'):
            return super().get_queryset().filter(conta=self.model._current_conta)
        return super().get_queryset()

    def for_conta(self, conta):
        """Método para filtrar por uma conta específica"""
        return super().get_queryset().filter(conta=conta)

#--------------------------------------------------------------
# MODELO DE USUÁRIO CUSTOMIZADO
class CustomUser(AbstractUser):
    class Meta:
        db_table = 'customUser'

    email = models.EmailField('e-mail address', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

#--------------------------------------------------------------
# MODELO DE CONTA (substitui Organization)
class Conta(models.Model):
    class Meta:
        db_table = 'conta'

    name = models.CharField(max_length=255, unique=True)
    cnpj = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

#--------------------------------------------------------------
# MODELO DE LICENÇA (vinculado à Conta)
class Licenca(models.Model):
    class Meta:
        db_table = 'licenca'

    conta = models.OneToOneField(Conta, on_delete=models.CASCADE, related_name='licenca')
    plano = models.CharField(max_length=50)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativa = models.BooleanField(default=True)
    limite_usuarios = models.PositiveIntegerField(default=1)

    def is_valida(self):
        from django.utils import timezone
        hoje = timezone.now().date()
        return self.ativa and self.data_inicio <= hoje <= self.data_fim

#--------------------------------------------------------------
# ASSOCIAÇÃO USUÁRIOS <-> CONTAS (com papéis)
class ContaMembership(models.Model):
    class Meta:
        db_table = 'conta_membership'
        unique_together = ('conta', 'user')

    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('contabilidade', 'Contabilidade'),
        ('medico', 'Médico'),
        ('readonly', 'Somente Leitura'),
    ]

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conta_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='readonly')
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.conta.name} ({self.role})"

#--------------------------------------------------------------
# MODELO BASE PARA TODOS OS MODELOS QUE PRECISAM DE TENANT ISOLATION
class SaaSBaseModel(models.Model):
    class Meta:
        abstract = True

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, null=False)
    objects = ContaScopedManager()

    def save(self, *args, **kwargs):
        if not self.conta_id:
            raise ValueError("Conta é obrigatória para todos os modelos SaaS")
        super().save(*args, **kwargs)

#--------------------------------------------------------------
# PERFIL PESSOA (pode ser usado para usuários e não-usuários)
class Pessoa(SaaSBaseModel):
    class Meta:
        db_table = 'pessoa'
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

    # Relacionamento com usuário (opcional)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pessoa_profile'
    )

    # Dados pessoais
    name = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, blank=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, verbose_name="RG")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")

    # Contatos
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    celular = models.CharField(max_length=20, blank=True, verbose_name="Celular")
    email = models.EmailField(blank=True, verbose_name="Email")

    # Endereço
    endereco = models.CharField(max_length=255, blank=True, verbose_name="Endereço")
    numero = models.CharField(max_length=10, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    cep = models.CharField(max_length=9, blank=True, verbose_name="CEP")

    # Dados profissionais
    crm = models.CharField(max_length=20, blank=True, verbose_name="CRM")
    especialidade = models.CharField(max_length=100, blank=True, verbose_name="Especialidade")

    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def nome_curto(self):
        """Retorna as duas primeiras palavras do nome"""
        palavras = self.name.split()
        return ' '.join(palavras[:2]) if len(palavras) >= 2 else self.name

#--------------------------------------------------------------
# EMPRESA (substitui Cliente/PJuridica)
class Empresa(models.Model):
    class Meta:
        db_table = 'empresa'
        verbose_name = "Empresa/Associação"
        verbose_name_plural = "Empresas/Associações"

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='empresas', null=False)

    # Dados da empresa
    name = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, blank=True, verbose_name="Nome Fantasia")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    inscricao_estadual = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Estadual")
    inscricao_municipal = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Municipal")

    # Contatos
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="Email")
    site = models.URLField(blank=True, verbose_name="Site")

    # Endereço
    endereco = models.CharField(max_length=255, blank=True, verbose_name="Endereço")
    numero = models.CharField(max_length=10, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    cep = models.CharField(max_length=9, blank=True, verbose_name="CEP")

    # Dados tributários
    regime_tributario = models.CharField(max_length=50, blank=True, verbose_name="Regime Tributário")
    aliquota_iss = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Alíquota ISS (%)"
    )

    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_fantasia or self.name

    def clean(self):
        # Validar CNPJ (implementação básica)
        if self.cnpj:
            # Remove caracteres não numéricos
            cnpj_numeros = ''.join(filter(str.isdigit, self.cnpj))
            if len(cnpj_numeros) != 14:
                raise ValidationError({'cnpj': 'CNPJ deve ter 14 dígitos'})

#--------------------------------------------------------------
class Socio(models.Model):
    class Meta:
        db_table = 'socio'
        verbose_name = "Sócio/Médico"
        verbose_name_plural = "Sócios/Médicos"
        unique_together = ('conta', 'pessoa')

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='socios', null=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE)

    # Status e controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_entrada = models.DateField(null=True, blank=True, verbose_name="Data de Entrada")
    data_saida = models.DateField(null=True, blank=True, verbose_name="Data de Saída")

    # Dados adicionais
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def __str__(self):
        return f"{self.pessoa.name} - {self.empresa.name}"

    def obter_percentual_item_mensal(self, item_despesa, mes_referencia):
        """Obtém o percentual de rateio para um item em um mês específico"""
        from .despesas import PercentualRateioMensal
        try:
            percentual = PercentualRateioMensal.objects.get(
                socio=self,
                item_despesa=item_despesa,
                mes_referencia=mes_referencia.replace(day=1),
                ativo=True
            )
            return percentual.percentual
        except PercentualRateioMensal.DoesNotExist:
            return 0

    def listar_percentuais_mes(self, mes_referencia):
        """Lista todos os percentuais de rateio para este sócio em um mês"""
        from .despesas import PercentualRateioMensal
        return PercentualRateioMensal.objects.filter(
            socio=self,
            mes_referencia=mes_referencia.replace(day=1),
            ativo=True
        ).select_related('item_despesa')
