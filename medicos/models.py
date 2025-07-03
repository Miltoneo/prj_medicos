from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

app_name = 'medicos'

#--------------------------------------------------------------
# DEFINIÇÕES
#--------------------------------------------------------------
# Regime de tributação
REGIME_TRIBUTACAO_COMPETENCIA = 1   # considera o mes de recebimento da nota
REGIME_TRIBUTACAO_CAIXA       = 2   # considera o mes de emissão da nota

# tipo de alicota aplicar sobre a nota
NFISCAL_ALICOTA_CONSULTAS     = 1
NFISCAL_ALICOTA_OUTROS        = 2  # vacinação, exames, procedimentos, outros
NFISCAL_ALICOTA_PLANTAO       = 3  # vacinação, exames, procedimentos, outros

# tipo de movimentação da conta
TIPO_MOVIMENTACAO_CONTA_CREDITO    = 1    # entradas, creditos, depositos
TIPO_MOVIMENTACAO_CONTA_DEBITO     = 2    # retiradas, transferencia

# DESCRICAO PADRONIZADA DE MOVIMENTAÇÃO AUTOMÁTICA REALIZADA PELO SISTEMA
DESC_MOVIMENTACAO_CREDITO_SALDO_MES_SEGUINTE  = 'CREDITO SALDO MES ANTERIOR'
DESC_MOVIMENTACAO_DEBITO_IMPOSTO_PROVISIONADOS= 'DEBITO PAGAMENTO DE IMPOSTOS '

# GRUPOS DE DESPESAS
CODIGO_GRUPO_DESPESA_GERAL = 'GERAL'
CODIGO_GRUPO_DESPESA_FOLHA = 'FOLHA'
CODIGO_GRUPO_DESPESA_SOCIO = 'SOCIO'

# TIPO DE DESPESA
TIPO_DESPESA_COM_RATEIO = 1
TIPO_DESPESA_SEM_RATEIO = 2

# TIPO DE GRUPO
GRUPO_ITEM_COM_RATEIO = 1
GRUPO_ITEM_SEM_RATEIO = 2

#--------------------------------------------------------------
# MODELO DE USUÁRIO CUSTOMIZADO
class CustomUser(AbstractUser):

    class Meta:
        db_table = 'customUser'

    email = models.EmailField('e-mail address', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # o Django exige ao menos um campo além de USERNAME_FIELD

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

    def __str__(self):
        return f"{self.conta.name} - {self.plano}"

#--------------------------------------------------------------
# ASSOCIAÇÃO USUÁRIOS <-> CONTAS (com papéis)
class ContaMembership(models.Model):
    class Meta:
        db_table = 'conta_membership'

    ROLE_CHOICES = (
        ('admin', 'Administrador'),
        ('member', 'Membro'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conta_memberships')
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    date_joined = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='invited_users'
    )

    class Meta:
        unique_together = ('user', 'conta')

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()}) em {self.conta.name}"

#--------------------------------------------------------------
# PERFIL PESSOA (pode ser usado para usuários e não-usuários)
class Pessoa(models.Model):
    
    class Meta:
        db_table = 'pessoa'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='pessoas', null=True, blank=True)
    CPF = models.CharField(max_length=255, null=False, unique=True)
    type_of_person = models.IntegerField(null=True)
    name = models.CharField(max_length=255, null=False)
    profissão = models.CharField(null=True, max_length=255)
    dnascimento = models.DateField(null=True)
    address1 = models.CharField(max_length=255, null=True)
    zipcode = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    phone1 = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    status = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.name}"

#--------------------------------------------------------------
# EMPRESA (substitui Cliente/PJuridica)
class Empresa(models.Model):

    class Meta:
        db_table = 'empresa'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='empresas', null=True, blank=True)
    class Regime_t(models.IntegerChoices):
        COMPETENCIA = 1, "COMPETENCIA"
        CAIXA       = 2, "CAIXA"

    CNPJ = models.CharField(max_length=255, null=False, unique=False)
    name = models.CharField(max_length=255, null=False, unique=False)
    status = models.IntegerField(null=True)
    tipo_regime =  models.PositiveSmallIntegerField(
        choices=Regime_t.choices,
        default=Regime_t.COMPETENCIA
    )

    def __str__(self):
        return f"{self.name}"

#--------------------------------------------------------------
class Socio(models.Model):
    
    class Meta:
        db_table = 'socio'


    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='socios', null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    pessoa = models.ForeignKey(Pessoa, on_delete = models.CASCADE, unique=False)

    def __str__(self):
        return f" {self.pessoa}"

class Alicotas(models.Model):
    
    class Meta:
        db_table = 'alicotas'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='alicotas', null=True, blank=True)
    ISS = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    PIS = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    COFINS = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    IRPJ_BASE_CAL = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    IRPJ_ALIC_1 = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    IRPJ_ALIC_2 = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    IRPJ_ADICIONAL = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    CSLL_BASE_CAL = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    CSLL_ALIC_1 = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)
    CSLL_ALIC_2 = models.DecimalField(max_digits=9, decimal_places=2, null=False,  default=0)

    def __str__(self):
        return f"{self.ISS} {self.PIS} {self.COFINS}"

class Despesa_Grupo(models.Model):
    
    class Meta:
        db_table = 'despesa_grupo'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='despesa_grupos', null=True, blank=True)
    class Tipo_t(models.IntegerChoices):
        COM_RATEIO = GRUPO_ITEM_COM_RATEIO, "COM RATEIO"
        SEM_RATEIO = GRUPO_ITEM_SEM_RATEIO, "SEM RATEIO"

    codigo =  models.CharField(max_length=20, null=False, unique=True)
    descricao = models.CharField(max_length=255, null=False, default="")
    tipo_rateio =  models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.COM_RATEIO
    )

    def __str__(self):
        return f" {self.codigo }"

class Despesa_Item(models.Model):
    
    class Meta:
        db_table = 'despesa_item'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='despesa_itens', null=True, blank=True)
    grupo = models.ForeignKey(Despesa_Grupo, on_delete = models.CASCADE)
    codigo =  models.CharField(max_length=20, null=False, unique=True)
    descricao = models.CharField(max_length=255, null=False, default="")

    def __str__(self):
        return f" {self.grupo.codigo } {self.descricao }"

class Despesa(models.Model):
    
    class Meta:
        db_table = 'despesa'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='despesas', null=True, blank=True)
    class Tipo_t(models.IntegerChoices):
        COM_RATEIO = TIPO_DESPESA_COM_RATEIO, "DESPESA FOLHA/GERAL - COM RATEIO"
        SEM_RATEIO = TIPO_DESPESA_SEM_RATEIO, "DESPESA DE SOCIO    - SEM RATEIO"

    tipo_rateio =  models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.COM_RATEIO
    )
    item = models.ForeignKey(Despesa_Item, on_delete = models.CASCADE, unique=False)
    empresa = models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    socio = models.ForeignKey(Socio,  on_delete = models.CASCADE, null=True, unique=False)
    data = models.DateField(null=False, unique=False)
    valor  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    descricao = models.CharField(max_length=255,null=True,unique=False)
    def __str__(self):
        return f" [{self.item.grupo.codigo}] {self.item.descricao}"

class Despesa_socio_rateio(models.Model):
    
    class Meta:
        db_table = 'despesa_socio_rateio'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='despesa_socios_rateio', null=True, blank=True)
    fornecedor = models.ForeignKey(Empresa, on_delete = models.CASCADE)
    socio = models.ForeignKey(Socio, on_delete = models.CASCADE)
    despesa = models.ForeignKey(Despesa, on_delete = models.CASCADE)
    percentual = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    vl_rateio = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)

    def __str__(self):
        return f" {self.despesa.item} {self.socio.pessoa.name}"

class NotaFiscal(models.Model):
    
    class Meta:
        db_table = 'nota_fiscal'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='notas_fiscais', null=True, blank=True)
    class Alicota_t(models.IntegerChoices):
        CONSULTAS = NFISCAL_ALICOTA_CONSULTAS, "CONSULTAS"
        PLANTAO   = NFISCAL_ALICOTA_PLANTAO, "PLANTAO"
        OUTROS    = NFISCAL_ALICOTA_OUTROS, "OUTROS"

    numero = models.CharField(max_length=255,null=True,unique=False,default=0)
    tomador = models.CharField(max_length=255,null=True,unique=False,default=0)
    fornecedor  = models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    socio = models.ForeignKey(Socio, on_delete = models.CASCADE, unique=False, null=True)
    dtEmissao = models.DateField(null=False)
    dtRecebimento = models.DateField(null=True,  blank=True)
    val_bruto = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    val_liquido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    val_ISS  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    val_PIS  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    val_COFINS  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    val_IR = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    val_CSLL  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    tipo_aliquota =  models.PositiveSmallIntegerField(
        choices=Alicota_t.choices,
        default=Alicota_t.CONSULTAS
    )

    def __str__(self):
        return f"{self.tomador} {self.val_bruto}"

class Balanco(models.Model):
    
    class Meta:
        db_table = 'balanco'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='balancos', null=True, blank=True)
    data = models.DateField(null=False)
    empresa = models.ForeignKey(Empresa, on_delete = models.CASCADE)
    socio = models.ForeignKey(Socio, on_delete = models.CASCADE)
    receita_bruta_notas_emitidas = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    recebido_consultas = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    recebido_plantao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    recebido_outros = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    recebido_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_bruta_trimestre = models.DecimalField(max_digits=9, decimal_places=2, null=True, default=0)
    faturamento_servicos_consultas = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    faturamento_servicos_plantao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    faturamento_servicos_outros = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_bruta_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_liquida_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_csll_base_calculo = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_csll_imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_csll_imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_csll_imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_irpj_base_calculo  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_irpj_imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_irpj_imposto_adicional = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_irpj_imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_irpj_imposto_pagar  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_iss_base_calculo  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_iss_imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_iss_imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_imposto_iss_imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_PIS_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_COFINS_devido  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    despesa_com_rateio = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    despesa_sem_rateio = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    despesa_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    despesa_socio_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    despesa_folha_rateio = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    despesa_geral_rateio = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_movimentacao_financeira= models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_apurado= models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_a_transferir = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)

    def __str__(self):
        return f"{self.data}"

class Apuracao_pis(models.Model):
    
    class Meta:
        db_table = 'apuracao_pis'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_pis', null=True, blank=True)
    data = models.DateField(null=False)
    fornecedor =   models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    base_calculo = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_mes_anterior = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_mes_seguinte = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)

    def __str__(self):
        return f"{self.data} {self.imposto_devido}"

class Apuracao_cofins(models.Model):

    class Meta:
        db_table = 'apuracao_cofins'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_cofins', null=True, blank=True)
    data = models.DateField(null=False)
    fornecedor =  models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    base_calculo = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_mes_anterior = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_mes_seguinte = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)

    def __str__(self):
        return f"{self.data} {self.imposto_devido}"

class Apuracao_csll(models.Model):
    
    class Meta:
        db_table = 'apuracao_csll'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_csll', null=True, blank=True)
    data = models.DateField(null=False)
    trimestre = models.IntegerField(null=False)
    fornecedor =   models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    receita_consultas = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_plantao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_outros = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_bruta  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    base_calculo = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    rend_aplicacao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    irrf_aplicacao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    base_calculo_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_adicional = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    def __str__(self):
        return f"{self.data} {self.trimestre}"

class Apuracao_irpj(models.Model):
    
    class Meta:
        db_table = 'apuracao_irpj'


    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_irpj', null=True, blank=True)
    data = models.DateField(null=False)
    trimestre = models.IntegerField(null=False)
    fornecedor =   models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    receita_consultas = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_plantao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_outros = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    receita_bruta  = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    base_calculo = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    rend_aplicacao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    irrf_aplicacao = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    base_calculo_total = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_adicional = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    def __str__(self):
        return f"{self.data} {self.trimestre}"

class Apuracao_iss(models.Model):
    
    class Meta:
        db_table = 'apuracao_iss'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_iss', null=True, blank=True)
    data = models.DateField(null=False)
    fornecedor =   models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    base_calculo = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_devido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_retido = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    imposto_pagar = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    saldo_mes_anterior = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)

    def __str__(self):
        return f"{self.data} {self.imposto_devido}"

class Aplic_financeiras(models.Model):

    class Meta:
        db_table = 'aplic_financeiras'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='aplic_financeiras', null=True, blank=True)
    data = models.DateField(null=False)
    fornecedor =   models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    rendimentos = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    irrf = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    descricao = models.CharField(max_length=255,null=True)

    def __str__(self):
        return f"{self.data} "

class Desc_movimentacao_financeiro(models.Model):
    
    class Meta:
        db_table = 'desc_movimentacao_financeiro'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='desc_movimentacao_financeiro', null=True, blank=True)
    descricao = models.CharField(max_length=255, null=False, default="")

    def __str__(self):
        return f" {self.descricao }"

class Financeiro(models.Model):
    
    class Meta:
        db_table = 'financeiro'
        
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='financeiros', null=True, blank=True)
    class tipo_t(models.IntegerChoices):
        CREDITO    = TIPO_MOVIMENTACAO_CONTA_CREDITO, "CREDITO"
        DEBITO     = TIPO_MOVIMENTACAO_CONTA_DEBITO,  "DEBITO"

    data = models.DateField(null=False)
    fornecedor  = models.ForeignKey(Empresa, on_delete = models.CASCADE, unique=False)
    socio =   models.ForeignKey(Socio, on_delete = models.CASCADE, unique=False)
    notafiscal = models.ForeignKey(NotaFiscal, on_delete = models.CASCADE, null=True, unique=False)
    tipo =  models.PositiveSmallIntegerField(
        choices=tipo_t.choices,
        default=tipo_t.CREDITO
    )
    descricao  = models.ForeignKey(Desc_movimentacao_financeiro, on_delete = models.CASCADE, unique=False)
    nota = models.CharField(max_length=50,null=True,unique=False,default='')
    valor = models.DecimalField(max_digits=9, decimal_places=2, null=False, default=0)
    operacao_auto = models.BooleanField(null=True, default= False)

    def __str__(self):
        return f"{self.data} "

