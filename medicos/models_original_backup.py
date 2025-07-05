# -*- coding: utf-8 -*-
"""
Modularized models for the Medical Association Cash Flow System.

This file now imports all models from the modular structure in the 'models' package.
The original monolithic models.py has been refactored into:
- base.py: Core models and constants
- fiscal.py: Tax and invoice models  
- despesas.py: Expense and rateio models
- financeiro.py: Manual cash flow and balance models
- auditoria.py: Audit and configuration models
- relatorios.py: Consolidated report models

This maintains backward compatibility while improving maintainability and reducing memory usage.
"""

# Import all models and constants from the modular structure
from .models import *

# For backward compatibility, expose the app_name
app_name = 'medicos'

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
        unique_together = ('user', 'conta')

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

    def save(self, *args, **kwargs):
        # Validação SaaS: verificar se a licença permite mais usuários
        if not self.pk:  # Novo membership
            memberships_count = ContaMembership.objects.filter(conta=self.conta).count()
            if self.conta.licenca.limite_usuarios <= memberships_count:
                raise ValidationError(f"Limite de usuários excedido para a conta {self.conta.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()}) em {self.conta.name}"

#--------------------------------------------------------------
# MODELO BASE PARA TODOS OS MODELOS QUE PRECISAM DE TENANT ISOLATION
class SaaSBaseModel(models.Model):
    """
    Modelo base para todos os modelos que precisam de tenant isolation
    """
    class Meta:
        abstract = True
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ContaScopedManager()
    
    def save(self, *args, **kwargs):
        # Validação SaaS: verificar se a licença está ativa
        if hasattr(self, 'conta') and self.conta:
            if not self.conta.licenca.is_valida():
                raise ValidationError(f"Licença inválida ou expirada para a conta {self.conta.name}")
        super().save(*args, **kwargs)

#--------------------------------------------------------------
# PERFIL PESSOA (pode ser usado para usuários e não-usuários)
class Pessoa(SaaSBaseModel):
    
    class Meta:
        db_table = 'pessoa'
        unique_together = ('conta', 'CPF')  # CPF único por conta

    CPF = models.CharField(max_length=255, null=False)
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
        unique_together = ('conta', 'CNPJ')  # CNPJ único por conta

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='empresas', null=False)
    class Regime_t(models.IntegerChoices):
        COMPETENCIA = 1, "COMPETENCIA"
        CAIXA       = 2, "CAIXA"

    CNPJ = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)
    status = models.IntegerField(null=True)
    tipo_regime =  models.PositiveSmallIntegerField(
        choices=Regime_t.choices,
        default=Regime_t.COMPETENCIA
    )

    def __str__(self):
        return f"{self.name}"

#--------------------------------------------------------------
class Socio(models.Model):
    """Sócios/médicos associados às empresas"""
    
    class Meta:
        db_table = 'socio'
        unique_together = ('conta', 'empresa', 'pessoa')  # Evita duplicatas por conta

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
        return f"{self.pessoa.name} ({self.empresa.name})"
    
    def obter_percentual_item_mensal(self, item_despesa, mes_referencia):
        """
        Obtém o percentual de rateio para um item específico em um mês
        """
        from django.db import models as django_models
        return PercentualRateioMensal.objects.filter(
            socio=self,
            item_despesa=item_despesa,
            mes_referencia=mes_referencia,
            ativo=True
        ).first()
    
    def listar_percentuais_mes(self, mes_referencia):
        """
        Lista todos os percentuais do sócio para um mês específico
        """
        return PercentualRateioMensal.objects.filter(
            socio=self,
            mes_referencia=mes_referencia,
            ativo=True
        ).select_related('item_despesa__grupo')

class Aliquotas(models.Model):
    """
    Alíquotas de impostos e regras para cálculo da tributação
    
    Este modelo define as alíquotas e parâmetros necessários para o cálculo automático
    dos impostos incidentes sobre as notas fiscais (ISS, PIS, COFINS, IRPJ, CSLL).
    
    Cada conta/cliente pode ter suas próprias alíquotas configuradas conforme
    sua situação tributária específica.
    """
    
    class Meta:
        db_table = 'aliquotas'
        verbose_name = "Alíquotas e Regras Tributárias"
        verbose_name_plural = "Alíquotas e Regras Tributárias"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='aliquotas', 
        null=False,
        verbose_name="Conta",
        help_text="Conta/cliente proprietária destas configurações tributárias"
    )
    
    # === IMPOSTOS MUNICIPAIS POR TIPO DE SERVIÇO ===
    # ISS para Consultas Médicas
    ISS_CONSULTAS = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="ISS - Consultas (%)",
        help_text="Alíquota do ISS para prestação de serviços de consulta médica"
    )
    
    # ISS para Plantão Médico
    ISS_PLANTAO = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="ISS - Plantão (%)",
        help_text="Alíquota do ISS para prestação de serviços de plantão médico"
    )
    
    # ISS para Outros Serviços (Vacinação, Exames, Procedimentos)
    ISS_OUTROS = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="ISS - Outros Serviços (%)",
        help_text="Alíquota do ISS para vacinação, exames, procedimentos e outros serviços"
    )
    
    # === CONTRIBUIÇÕES FEDERAIS (UNIFORMES PARA TODOS OS TIPOS) ===
    PIS = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="PIS (%)",
        help_text="Alíquota do PIS - Programa de Integração Social (geralmente 0,65%)"
    )
    COFINS = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="COFINS (%)",
        help_text="Alíquota da COFINS - Contribuição para Financiamento da Seguridade Social (geralmente 3%)"
    )
    
    # === IMPOSTO DE RENDA PESSOA JURÍDICA (IRPJ) ===
    IRPJ_BASE_CAL = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=32.00,
        verbose_name="IRPJ - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo do IRPJ (padrão 32%)"
    )
    IRPJ_ALIC_1 = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=15.00,
        verbose_name="IRPJ - Alíquota Normal (%)",
        help_text="Alíquota normal do IRPJ sobre a base de cálculo (padrão 15%)"
    )
    IRPJ_ALIC_2 = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=25.00,
        verbose_name="IRPJ - Alíquota Adicional (%)",
        help_text="Alíquota adicional do IRPJ sobre o excesso (padrão 25%)"
    )
    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=False, 
        default=60000.00,
        verbose_name="IRPJ - Limite para Adicional (R$)",
        help_text="Valor limite trimestral para início do cálculo do adicional (padrão R$ 60.000,00)"
    )
    IRPJ_ADICIONAL = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=10.00,
        verbose_name="IRPJ - Adicional (%)",
        help_text="Alíquota do adicional de IRPJ sobre o excesso do limite (padrão 10%)"
    )
    
    # === CONTRIBUIÇÃO SOCIAL SOBRE O LUCRO LÍQUIDO (CSLL) ===
    CSLL_BASE_CAL = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=32.00,
        verbose_name="CSLL - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo da CSLL (padrão 32%)"
    )
    CSLL_ALIC_1 = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=9.00,
        verbose_name="CSLL - Alíquota Normal (%)",
        help_text="Alíquota normal da CSLL sobre a base de cálculo (padrão 9%)"
    )
    CSLL_ALIC_2 = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=15.00,
        verbose_name="CSLL - Alíquota Adicional (%)",
        help_text="Alíquota adicional da CSLL para prestadores de serviços (padrão 15%)"
    )
    
    # === CONTROLE E AUDITORIA ===
    ativa = models.BooleanField(
        default=True,
        verbose_name="Configuração Ativa",
        help_text="Indica se esta configuração está ativa para uso nos cálculos"
    )
    data_vigencia_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name="Início da Vigência",
        help_text="Data de início da vigência desta configuração tributária"
    )
    data_vigencia_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fim da Vigência",
        help_text="Data de fim da vigência (deixe vazio se não há limite)"
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aliquotas_criadas',
        verbose_name="Criado por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre as particularidades desta configuração tributária"
    )

    def clean(self):
        """Validações personalizadas"""
        # Validar se as alíquotas estão em ranges válidos
        campos_percentuais = [
            ('ISS_CONSULTAS', self.ISS_CONSULTAS, 0, 20),
            ('ISS_PLANTAO', self.ISS_PLANTAO, 0, 20),
            ('ISS_OUTROS', self.ISS_OUTROS, 0, 20),
            ('PIS', self.PIS, 0, 10),
            ('COFINS', self.COFINS, 0, 10),
            ('IRPJ_BASE_CAL', self.IRPJ_BASE_CAL, 0, 100),
            ('IRPJ_ALIC_1', self.IRPJ_ALIC_1, 0, 50),
            ('IRPJ_ALIC_2', self.IRPJ_ALIC_2, 0, 50),
            ('IRPJ_ADICIONAL', self.IRPJ_ADICIONAL, 0, 50),
            ('CSLL_BASE_CAL', self.CSLL_BASE_CAL, 0, 100),
            ('CSLL_ALIC_1', self.CSLL_ALIC_1, 0, 50),
            ('CSLL_ALIC_2', self.CSLL_ALIC_2, 0, 50),
        ]
        
        for nome, valor, minimo, maximo in campos_percentuais:
            if valor < minimo or valor > maximo:
                raise ValidationError(f"{nome}: Valor deve estar entre {minimo}% e {maximo}%")
        
        # Validar datas de vigência
        if (self.data_vigencia_inicio and self.data_vigencia_fim and 
            self.data_vigencia_inicio > self.data_vigencia_fim):
            raise ValidationError("Data de início não pode ser posterior à data de fim da vigência")

    def __str__(self):
        return f"Alíquotas - {self.conta.name} (ISS Consultas: {self.ISS_CONSULTAS}%, Plantão: {self.ISS_PLANTAO}%, Outros: {self.ISS_OUTROS}%)"
    
    @property
    def eh_vigente(self):
        """Verifica se a configuração está vigente na data atual"""
        if not self.ativa:
            return False
        
        hoje = timezone.now().date()
        
        # Verifica início da vigência
        if self.data_vigencia_inicio and hoje < self.data_vigencia_inicio:
            return False
        
        # Verifica fim da vigência
        if self.data_vigencia_fim and hoje > self.data_vigencia_fim:
            return False
        
        return True
    
    def calcular_impostos_nf(self, valor_bruto, tipo_servico='consultas'):
        """
        Calcula os impostos para uma nota fiscal baseado no tipo de serviço prestado
        
        Args:
            valor_bruto (Decimal): Valor bruto da nota fiscal
            tipo_servico (str): Tipo do serviço médico prestado:
                - 'consultas': Prestação de serviço de consulta médica
                - 'plantao': Prestação de serviço de plantão médico  
                - 'outros': Prestação de serviço de vacinação, exames, procedimentos, outros
        
        Returns:
            dict: Dicionário com os valores calculados dos impostos por tipo de serviço
        """
        if not self.eh_vigente:
            raise ValidationError("Esta configuração de alíquotas não está vigente")
        
        # Determinar alíquota ISS baseada no tipo de serviço
        if tipo_servico == 'consultas':
            aliquota_iss = self.ISS_CONSULTAS
            descricao_servico = "Consultas Médicas"
        elif tipo_servico == 'plantao':
            aliquota_iss = self.ISS_PLANTAO
            descricao_servico = "Plantão Médico"
        elif tipo_servico == 'outros':
            aliquota_iss = self.ISS_OUTROS
            descricao_servico = "Vacinação/Exames/Procedimentos"
        else:
            # Fallback para consultas se tipo não reconhecido
            aliquota_iss = self.ISS_CONSULTAS
            descricao_servico = "Consultas Médicas (padrão)"
        
        # Cálculos básicos com ISS diferenciado por tipo de serviço
        valor_iss = valor_bruto * (aliquota_iss / 100)
        valor_pis = valor_bruto * (self.PIS / 100)
        valor_cofins = valor_bruto * (self.COFINS / 100)
        
        # Base de cálculo para IR e CSLL
        base_calculo_ir = valor_bruto * (self.IRPJ_BASE_CAL / 100)
        base_calculo_csll = valor_bruto * (self.CSLL_BASE_CAL / 100)
        
        # IRPJ
        valor_ir_normal = base_calculo_ir * (self.IRPJ_ALIC_1 / 100)
        valor_ir_adicional = 0
        if base_calculo_ir > self.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL:
            excesso = base_calculo_ir - self.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL
            valor_ir_adicional = excesso * (self.IRPJ_ADICIONAL / 100)
        
        valor_ir_total = valor_ir_normal + valor_ir_adicional
        
        # CSLL
        valor_csll = base_calculo_csll * (self.CSLL_ALIC_1 / 100)
        
        # Valor líquido
        total_impostos = valor_iss + valor_pis + valor_cofins + valor_ir_total + valor_csll
        valor_liquido = valor_bruto - total_impostos
        
        return {
            'valor_bruto': valor_bruto,
            'tipo_servico': tipo_servico,
            'descricao_servico': descricao_servico,
            'aliquota_iss_aplicada': aliquota_iss,
            'valor_iss': valor_iss,
            'valor_pis': valor_pis,
            'valor_cofins': valor_cofins,
            'valor_ir': valor_ir_total,
            'valor_ir_normal': valor_ir_normal,
            'valor_ir_adicional': valor_ir_adicional,
            'valor_csll': valor_csll,
            'total_impostos': total_impostos,
            'valor_liquido': valor_liquido,
            'base_calculo_ir': base_calculo_ir,
            'base_calculo_csll': base_calculo_csll,
        }
    
    @classmethod
    def obter_aliquota_vigente(cls, conta, data_referencia=None):
        """
        Obtém a configuração de alíquotas vigente para uma conta em uma data específica
        
        Args:
            conta: Instância da conta
            data_referencia: Data para verificar vigência (padrão: hoje)
        
        Returns:
            Aliquotas: Configuração vigente ou None se não encontrada
        """
        if not data_referencia:
            data_referencia = timezone.now().date()
        
        return cls.objects.filter(
            conta=conta,
            ativa=True,
            data_vigencia_inicio__lte=data_referencia
        ).filter(
            models.Q(data_vigencia_fim__isnull=True) | 
            models.Q(data_vigencia_fim__gte=data_referencia)
        ).first()

    def aplicar_impostos_nota_fiscal(self, nota_fiscal):
        """
        Aplica os cálculos de impostos em uma instância de NotaFiscal
        baseado no tipo de serviço prestado
        
        Args:
            nota_fiscal: Instância de NotaFiscal para aplicar os cálculos
        """
        if not nota_fiscal.val_bruto:
            return
        
        # Determinar tipo de serviço baseado no enum da nota fiscal
        tipo_servico_map = {
            1: 'consultas',    # NFISCAL_ALIQUOTA_CONSULTAS
            2: 'plantao',      # NFISCAL_ALIQUOTA_PLANTAO  
            3: 'outros'        # NFISCAL_ALIQUOTA_OUTROS
        }
        
        tipo_servico = tipo_servico_map.get(nota_fiscal.tipo_aliquota, 'consultas')
        
        # Calcular impostos baseado no tipo de serviço
        calculo = self.calcular_impostos_nf(
            nota_fiscal.val_bruto,
            tipo_servico
        )
        
        # Atualizar os campos da nota fiscal
        nota_fiscal.val_liquido = calculo['valor_liquido']
        nota_fiscal.val_ISS = calculo['valor_iss']
        nota_fiscal.val_PIS = calculo['valor_pis']
        nota_fiscal.val_COFINS = calculo['valor_cofins']
        nota_fiscal.val_IR = calculo['valor_ir']
        nota_fiscal.val_CSLL = calculo['valor_csll']
    
    def obter_aliquota_iss_por_tipo(self, tipo_servico):
        """
        Retorna a alíquota ISS específica para um tipo de serviço
        
        Args:
            tipo_servico (str): 'consultas', 'plantao' ou 'outros'
            
        Returns:
            Decimal: Alíquota ISS aplicável
        """
        if tipo_servico == 'consultas':
            return self.ISS_CONSULTAS
        elif tipo_servico == 'plantao':
            return self.ISS_PLANTAO
        elif tipo_servico == 'outros':
            return self.ISS_OUTROS
        else:
            return self.ISS_CONSULTAS  # Padrão

#--------------------------------------------------------------
# PERCENTUAIS MENSAIS DE RATEIO POR ITEM DE DESPESA
class PercentualRateioMensal(models.Model):
    """Percentuais de rateio mensais para cada item de despesa dos grupos FOLHA e GERAL"""
    
    class Meta:
        db_table = 'percentual_rateio_mensal'
        unique_together = ('conta', 'item_despesa', 'socio', 'mes_referencia')
        verbose_name = "Percentual de Rateio Mensal"
        verbose_name_plural = "Percentuais de Rateio Mensais"
        indexes = [
            models.Index(fields=['mes_referencia', 'item_despesa']),
            models.Index(fields=['socio', 'mes_referencia']),
        ]

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='percentuais_rateio', null=False)
    
    # Relacionamentos
    item_despesa = models.ForeignKey(
        'Despesa_Item', 
        on_delete=models.CASCADE, 
        related_name='percentuais_mensais',
        verbose_name="Item de Despesa"
    )
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        related_name='percentuais_rateio',
        verbose_name="Sócio/Médico"
    )
    
    # Data de referência (mês/ano)
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Data no formato YYYY-MM-01 (primeiro dia do mês)"
    )
    
    # Percentual específico para este item/sócio/mês
    percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Percentual (%)",
        help_text="Percentual de rateio para este item específico no mês (0-100%)"
    )
    
    # Dados de controle
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    cadastrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Cadastrado Por"
    )
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def clean(self):
        """Validações personalizadas"""
        # Verificar se o percentual está no range válido
        if self.percentual < 0 or self.percentual > 100:
            raise ValidationError("Percentual deve estar entre 0 e 100%")
        
        # Verificar se o item permite rateio
        if self.item_despesa and not self.item_despesa.permite_rateio:
            raise ValidationError(
                f"O item '{self.item_despesa.nome}' não permite rateio. "
                f"Apenas itens dos grupos FOLHA e GERAL permitem rateio."
            )
        
        # Verificar se o item é dos grupos corretos (FOLHA ou GERAL)
        if self.item_despesa and self.item_despesa.grupo.codigo not in ['FOLHA', 'GERAL']:
            raise ValidationError(
                f"Percentuais de rateio só podem ser definidos para itens dos grupos FOLHA e GERAL. "
                f"O item selecionado é do grupo '{self.item_despesa.grupo.codigo}'."
            )
        
        # Verificar se sócio e item pertencem à mesma conta
        if self.socio and self.item_despesa:
            if self.socio.conta != self.item_despesa.conta:
                raise ValidationError("Sócio e item de despesa devem pertencer à mesma conta.")

    def save(self, *args, **kwargs):
        # Normalizar a data para o primeiro dia do mês
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        
        # Garantir que a conta seja consistente
        if self.item_despesa:
            self.conta = self.item_despesa.conta
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.item_despesa.codigo_completo} - "
            f"{self.socio.pessoa.name} - "
            f"{self.percentual}% "
            f"({self.mes_referencia.strftime('%m/%Y')})"
        )
    
    @property
    def mes_ano_formatado(self):
        """Retorna o mês/ano formatado"""
        return self.mes_referencia.strftime('%m/%Y')
    
    @property
    def percentual_formatado(self):
        """Retorna o percentual formatado"""
        return f"{self.percentual}%"

    @classmethod
    def obter_percentual_para_rateio(cls, item_despesa, socio, data_despesa):
        """
        Método de classe para obter o percentual de rateio para um item/sócio em uma data específica
        """
        # Normalizar para o primeiro dia do mês
        mes_referencia = data_despesa.replace(day=1)
        
        try:
            percentual_obj = cls.objects.get(
                item_despesa=item_despesa,
                socio=socio,
                mes_referencia=mes_referencia,
                ativo=True
            )
            return percentual_obj.percentual
        except cls.DoesNotExist:
            # Se não encontrar percentual específico, retornar 0
            return 0
    
    @classmethod
    def validar_percentuais_mes(cls, item_despesa, mes_referencia):
        """
        Valida se a soma dos percentuais para um item em um mês específico não excede 100%
        """
        percentuais = cls.objects.filter(
            item_despesa=item_despesa,
            mes_referencia=mes_referencia,
            ativo=True
        )
        
        total = sum(p.percentual for p in percentuais)
        
        return {
            'valido': total <= 100,
            'total': total,
            'percentuais': list(percentuais)
        }

#--------------------------------------------------------------
# MODELO AUXILIAR PARA CONFIGURAÇÃO DE RATEIO POR MÊS
class ConfiguracaoRateioMensal(models.Model):
    """Configuração geral de rateio para um mês específico"""
    
    class Meta:
        db_table = 'configuracao_rateio_mensal'
        unique_together = ('conta', 'mes_referencia')
        verbose_name = "Configuração de Rateio Mensal"
        verbose_name_plural = "Configurações de Rateio Mensais"

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='configuracoes_rateio')
    
    # Mês de referência
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Data no formato YYYY-MM-01"
    )
    
    # Status da configuração
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('em_configuracao', 'Em Configuração'),
        ('finalizada', 'Finalizada'),
        ('aplicada', 'Aplicada às Despesas'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )
    
    # Controle
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_finalizacao = models.DateTimeField(null=True, blank=True)
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configuracoes_rateio_criadas',
        verbose_name="Criada Por"
    )
    finalizada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracoes_rateio_finalizadas',
        verbose_name="Finalizada Por"
    )
    
    # Observações
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def save(self, *args, **kwargs):
        # Normalizar a data para o primeiro dia do mês
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rateio {self.mes_referencia.strftime('%m/%Y')} - {self.get_status_display()}"
    
    def copiar_percentuais_mes_anterior(self):
        """
        Copia os percentuais do mês anterior para este mês como base
        """
        from dateutil.relativedelta import relativedelta
        
        mes_anterior = self.mes_referencia - relativedelta(months=1)
        
        percentuais_anteriores = PercentualRateioMensal.objects.filter(
            conta=self.conta,
            mes_referencia=mes_anterior,
            ativo=True
        )
        
        novos_percentuais = []
        for perc_anterior in percentuais_anteriores:
            # Verificar se já não existe para este mês
            existe = PercentualRateioMensal.objects.filter(
                conta=self.conta,
                item_despesa=perc_anterior.item_despesa,
                socio=perc_anterior.socio,
                mes_referencia=self.mes_referencia
            ).exists()
            
            if not existe:
                novo_percentual = PercentualRateioMensal(
                    conta=self.conta,
                    item_despesa=perc_anterior.item_despesa,
                    socio=perc_anterior.socio,
                    mes_referencia=self.mes_referencia,
                    percentual=perc_anterior.percentual,
                    cadastrado_por=perc_anterior.cadastrado_por,
                    observacoes=f"Copiado do mês {mes_anterior.strftime('%m/%Y')}"
                )
                novos_percentuais.append(novo_percentual)
        
        if novos_percentuais:
            PercentualRateioMensal.objects.bulk_create(novos_percentuais)
        
        return len(novos_percentuais)

class Despesa(models.Model):
    """Despesas unificadas com sistema de grupos e rateio"""
    
    class Meta:
        db_table = 'despesa'
        indexes = [
            models.Index(fields=['conta', 'data', 'item']),
            models.Index(fields=['empresa', 'socio']),
            models.Index(fields=['tipo_rateio', 'ja_rateada']),
        ]

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='despesas', null=False)
    
    class Tipo_t(models.IntegerChoices):
        COM_RATEIO = TIPO_DESPESA_COM_RATEIO, "DESPESA FOLHA/GERAL - COM RATEIO"
        SEM_RATEIO = TIPO_DESPESA_SEM_RATEIO, "DESPESA DE SOCIO - SEM RATEIO"

    # Classificação
    tipo_rateio = models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.COM_RATEIO,
        verbose_name="Tipo de Rateio"
    )
    item = models.ForeignKey('Despesa_Item', on_delete=models.PROTECT, verbose_name="Item de Despesa")
    
    # Relacionamentos
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa/Associação")
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Sócio Responsável",
        help_text="Obrigatório apenas para despesas de sócio (sem rateio)"
    )
    
    # Dados da despesa
    data = models.DateField(null=False, verbose_name="Data da Despesa")
    data_vencimento = models.DateField(null=True, blank=True, verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="Valor"
    )
    descricao = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        verbose_name="Descrição Adicional"
    )
    
    # Dados do documento
    numero_documento = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Número do Documento"
    )
    fornecedor = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Fornecedor"
    )
    
    # Controle de rateio
    ja_rateada = models.BooleanField(
        default=False,
        verbose_name="Já foi rateada",
        help_text="Indica se a despesa já teve seu rateio processado"
    )
    data_rateio = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Data do Rateio"
    )
    rateada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='despesas_rateadas',
        verbose_name="Rateada Por"
    )
    
    # Status
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name="Status"
    )
    
    # Dados contábeis
    centro_custo = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Centro de Custo"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lancada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='despesas_lancadas',
        verbose_name="Lançada Por"
    )

    def clean(self):
        """Validações personalizadas"""
        # Para despesas de sócio, sócio é obrigatório
        if self.tipo_rateio == self.Tipo_t.SEM_RATEIO:
            if not self.socio:
                raise ValidationError({
                    'socio': 'Sócio é obrigatório para despesas sem rateio.'
                })
        
        # Para despesas com rateio, sócio deve estar vazio
        elif self.tipo_rateio == self.Tipo_t.COM_RATEIO:
            if self.socio:
                raise ValidationError({
                    'socio': 'Sócio deve ser vazio para despesas com rateio.'
                })
        
        # Verificar se o item pertence ao tipo correto
        if self.item:
            if self.tipo_rateio == self.Tipo_t.SEM_RATEIO and self.item.grupo.codigo != 'SOCIO':
                raise ValidationError({
                    'item': 'Para despesas sem rateio, o item deve ser do grupo SOCIO.'
                })
            elif self.tipo_rateio == self.Tipo_t.COM_RATEIO and self.item.grupo.codigo not in ['FOLHA', 'GERAL']:
                raise ValidationError({
                    'item': 'Para despesas com rateio, o item deve ser do grupo FOLHA ou GERAL.'
                })

    def save(self, *args, **kwargs):
        # Definir tipo_rateio automaticamente baseado no grupo do item
        if self.item:
            if self.item.grupo.codigo == 'SOCIO':
                self.tipo_rateio = self.Tipo_t.SEM_RATEIO
            else:
                self.tipo_rateio = self.Tipo_t.COM_RATEIO
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.item.grupo.codigo}] {self.item.nome} - R$ {self.valor}"
    
    @property
    def grupo(self):
        """Acesso rápido ao grupo da despesa"""
        return self.item.grupo if self.item else None
    
    @property
    def pode_ser_rateada(self):
        """Verifica se a despesa pode ser rateada"""
        return (
            self.tipo_rateio == self.Tipo_t.COM_RATEIO and 
            not self.ja_rateada and
            self.status in ['pendente', 'aprovada']
        )
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado em real brasileiro"""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def eh_despesa_socio(self):
        """Verifica se é despesa de sócio"""
        return self.tipo_rateio == self.Tipo_t.SEM_RATEIO
    
    def criar_rateio_automatico(self, usuario=None):
        """
        Cria o rateio automático baseado nos percentuais mensais configurados
        
        IMPORTANTE: Este método é para rateio interno de despesas contábeis,
        que é diferente do fluxo de caixa individual dos médicos.
        
        O rateio de despesas é usado para:
        - Distribuição interna de custos operacionais
        - Controle contábil de gastos por médico
        - Base para cálculos de resultado
        
        Isso NÃO gera automaticamente lançamentos no fluxo de caixa individual.
        Para impactar o fluxo de caixa, deve ser criado lançamento manual
        usando descrições padronizadas pela contabilidade.
        """
        if not self.pode_ser_rateada:
            raise ValidationError("Esta despesa não pode ser rateada")
        
        # Obter o mês de referência da despesa
        mes_referencia = self.data.replace(day=1)
        
        # Buscar todos os percentuais para este item no mês
        percentuais = PercentualRateioMensal.objects.filter(
            item_despesa=self.item,
            mes_referencia=mes_referencia,
            ativo=True
        ).select_related('socio')
        
        if not percentuais.exists():
            raise ValidationError(
                f"Não há percentuais de rateio cadastrados para o item "
                f"'{self.item.nome}' no mês {mes_referencia.strftime('%m/%Y')}"
            )
        
        # Verificar se a soma dos percentuais é válida
        total_percentual = sum(p.percentual for p in percentuais)
        if total_percentual != 100:
            raise ValidationError(
                f"A soma dos percentuais para o item '{self.item.nome}' "
                f"no mês {mes_referencia.strftime('%m/%Y')} é {total_percentual}%. "
                f"Deve ser exatamente 100%."
            )
        
        # Criar os rateios
        rateios_criados = []
        for percentual_mensal in percentuais:
            rateio = Despesa_socio_rateio(
                conta=self.conta,
                despesa=self,
                socio=percentual_mensal.socio,
                percentual=percentual_mensal.percentual,
                rateado_por=usuario
            )
            rateio.save()  # O valor será calculado automaticamente no save()
            rateios_criados.append(rateio)
        
        # Marcar despesa como rateada
        self.ja_rateada = True
        self.data_rateio = timezone.now()
        self.rateada_por = usuario
        self.save()
        
        return rateios_criados
    
    def criar_lancamentos_financeiros(self, usuario=None):
        """
        MÉTODO DESABILITADO: Sistema agora opera exclusivamente de forma manual
        
        Este método criava lançamentos financeiros automáticos para rateio de despesas.
        No novo sistema manual, todos os lançamentos devem ser criados manualmente
        pela equipe de contabilidade usando as descrições padronizadas.
        
        Para registrar despesas individuais:
        1. Use a interface administrativa
        2. Selecione uma descrição padronizada da categoria 'despesa'
        3. Registre o lançamento manualmente com documentação adequada
        """
        raise NotImplementedError(
            "Sistema manual: Lançamentos financeiros devem ser criados manualmente "
            "pela contabilidade usando descrições padronizadas. "
            "Rateio automático foi desabilitado para garantir auditabilidade total."
        )

class Despesa_socio_rateio(models.Model):
    """Rateio de despesas entre sócios/médicos"""
    
    class Meta:
        db_table = 'despesa_socio_rateio'
        unique_together = ('despesa', 'socio')  # Evita rateio duplicado
        verbose_name = "Rateio de Despesa"
        verbose_name_plural = "Rateios de Despesas"

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='despesa_socios_rateio', null=False)
    despesa = models.ForeignKey('Despesa', on_delete=models.CASCADE, related_name='rateios')
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    
    # Dados do rateio
    percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="Percentual (%)",
        help_text="Percentual da despesa que cabe a este sócio"
    )
    vl_rateio = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="Valor do Rateio"
    )
    
    # Controle
    data_rateio = models.DateTimeField(auto_now_add=True, verbose_name="Data do Rateio")
    rateado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Rateado Por"
    )
    
    def clean(self):
        """Validações personalizadas"""
        if self.percentual <= 0 or self.percentual > 100:
            raise ValidationError("Percentual deve estar entre 0.01 e 100%")
        
        # Verificar se a despesa permite rateio
        if self.despesa and not self.despesa.pode_ser_rateada:
            raise ValidationError("Esta despesa não pode ser rateada")

    def save(self, *args, **kwargs):
        # Calcular valor do rateio automaticamente
        if self.despesa and self.percentual:
            self.vl_rateio = self.despesa.valor * (self.percentual / 100)
        
        # Garantir que a conta seja a mesma da despesa
        if self.despesa:
            self.conta = self.despesa.conta
            
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.despesa.item.nome} - {self.socio.pessoa.name} ({self.percentual}%)"
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado"""
        return f"R$ {self.vl_rateio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

#--------------------------------------------------------------
# SALDOS MENSAIS DOS MÉDICOS NO SISTEMA MANUAL
class SaldoMensalMedico(models.Model):
    """
    Controle de saldos mensais individuais por médico no sistema manual
    
    Este modelo consolida mensalmente todas as movimentações manuais
    registradas no fluxo de caixa individual de cada médico, fornecendo
    uma visão consolidada do saldo e das categorias de movimento.
    
    IMPORTANTE: Este modelo reflete APENAS movimentações manuais.
    As receitas de notas fiscais são tratadas separadamente no sistema contábil.
    """
    
    class Meta:
        db_table = 'saldo_mensal_medico'
        unique_together = ('conta', 'socio', 'mes_referencia')
        verbose_name = "Saldo Mensal do Médico"
        verbose_name_plural = "Saldos Mensais dos Médicos"
        indexes = [
            models.Index(fields=['conta', 'mes_referencia']),
            models.Index(fields=['socio', 'mes_referencia']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='saldos_mensais', 
        null=False
    )
    
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE,
        related_name='saldos_mensais',
        verbose_name="Médico/Sócio"
    )
    
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Data no formato YYYY-MM-01 (primeiro dia do mês)"
    )
    
    # === SALDOS CONSOLIDADOS ===
    saldo_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Inicial do Mês",
        help_text="Saldo transportado do mês anterior"
    )
    
    saldo_final = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Final do Mês",
        help_text="Saldo após todas as movimentações do mês"
    )
    
    # === TOTAIS DE MOVIMENTAÇÃO ===
    total_creditos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total de Créditos no Mês"
    )
    
    total_debitos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total de Débitos no Mês"
    )
    
    # === BREAKDOWN POR CATEGORIA (APENAS CATEGORIAS MANUAIS) ===
    # Créditos por categoria
    credito_adiantamentos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Adiantamentos de Lucro"
    )
    
    credito_pagamentos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Pagamentos Recebidos"
    )
    
    credito_ajustes = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Ajustes e Estornos"
    )
    
    credito_transferencias = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Transferências Recebidas"
    )
    
    credito_financeiro = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Operações Financeiras"
    )
    
    credito_saldo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Saldos e Transportes"
    )
    
    credito_outros = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Créditos - Outras Movimentações"
    )
    
    # Débitos por categoria
    debito_adiantamentos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Adiantamentos Concedidos"
    )
    
    debito_despesas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Despesas Individuais"
    )
    
    debito_taxas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Taxas e Encargos"
    )
    
    debito_transferencias = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Transferências Enviadas"
    )
    
    debito_ajustes = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Ajustes e Correções"
    )
    
    debito_financeiro = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Operações Financeiras"
    )
    
    debito_saldo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Saldos e Transportes"
    )
    
    debito_outros = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Débitos - Outras Movimentações"
    )
    
    # === ESTATÍSTICAS DO MÊS ===
    quantidade_movimentacoes = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade de Movimentações",
        help_text="Total de lançamentos no mês"
    )
    
    maior_credito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Maior Crédito do Mês"
    )
    
    maior_debito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Maior Débito do Mês"
    )
    
    # === CONTROLE DE FECHAMENTO ===
    fechado = models.BooleanField(
        default=False,
        verbose_name="Mês Fechado",
        help_text="Indica se o mês foi fechado para novas movimentações"
    )
    
    data_fechamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data do Fechamento"
    )
    
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fechamentos_realizados',
        verbose_name="Fechado Por"
    )
    
    # === AUDITORIA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    calculado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculos_saldo_realizados',
        verbose_name="Calculado Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o fechamento ou cálculo do mês"
    )

    def save(self, *args, **kwargs):
        # Normalizar a data para o primeiro dia do mês
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.socio.pessoa.name} - {self.mes_referencia.strftime('%m/%Y')} - Saldo: R$ {self.saldo_final}"
    
    @property
    def mes_ano_formatado(self):
        """Retorna o mês/ano formatado"""
        return self.mes_referencia.strftime('%m/%Y')
    
    @property
    def saldo_final_formatado(self):
        """Retorna o saldo final formatado"""
        sinal = "+" if self.saldo_final >= 0 else ""
        return f"{sinal}R$ {self.saldo_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def movimentacao_liquida(self):
        """Retorna a movimentação líquida do mês"""
        return self.total_creditos - self.total_debitos
    
    @property
    def categorias_credito(self):
        """Retorna um dicionário com todas as categorias de crédito"""
        return {
            'adiantamentos': self.credito_adiantamentos,
            'pagamentos': self.credito_pagamentos,
            'ajustes': self.credito_ajustes,
            'transferencias': self.credito_transferencias,
            'financeiro': self.credito_financeiro,
            'saldo': self.credito_saldo,
            'outros': self.credito_outros,
        }
    
    @property
    def categorias_debito(self):
        """Retorna um dicionário com todas as categorias de débito"""
        return {
            'adiantamentos': self.debito_adiantamentos,
            'despesas': self.debito_despesas,
            'taxas': self.debito_taxas,
            'transferencias': self.debito_transferencias,
            'ajustes': self.debito_ajustes,
            'financeiro': self.debito_financeiro,
            'saldo': self.debito_saldo,
            'outros': self.debito_outros,
        }
    
    def calcular_saldo_completo(self):
        """
        Recalcula todos os valores baseado nas movimentações financeiras do mês
        """
        from django.db.models import Sum, Max, Count
        from django.apps import apps
        
        # Obter o modelo Financeiro dinamicamente
        Financeiro = apps.get_model('medicos', 'Financeiro')
        
        # Buscar todas as movimentações do mês para este médico
        movimentacoes = Financeiro.objects.filter(
            socio=self.socio,
            data__year=self.mes_referencia.year,
            data__month=self.mes_referencia.month,
            status__in=['processado', 'conciliado', 'transferido']
        )
        
        # Resetar todos os valores
        self.total_creditos = 0
        self.total_debitos = 0
        self.quantidade_movimentacoes = 0
        self.maior_credito = 0
        self.maior_debito = 0
        
        # Resetar categorias
        for categoria in ['adiantamentos', 'pagamentos', 'ajustes', 'transferencias', 
                         'despesas', 'taxas', 'financeiro', 'saldo', 'outros']:
            setattr(self, f'credito_{categoria}', 0)
            setattr(self, f'debito_{categoria}', 0)
        
        # Processar cada movimentação
        for mov in movimentacoes:
            categoria = mov.descricao.categoria
            valor = mov.valor
            
            # Contadores gerais
            self.quantidade_movimentacoes += 1
            
            if mov.tipo == TIPO_MOVIMENTACAO_CONTA_CREDITO:
                self.total_creditos += valor
                self.maior_credito = max(self.maior_credito, valor)
                
                # Classificar por categoria
                campo_credito = f'credito_{categoria}'
                if hasattr(self, campo_credito):
                    setattr(self, campo_credito, getattr(self, campo_credito) + valor)
                else:
                    self.credito_outros += valor
                    
            else:  # DEBITO
                self.total_debitos += valor
                self.maior_debito = max(self.maior_debito, valor)
                
                # Classificar por categoria
                campo_debito = f'debito_{categoria}'
                if hasattr(self, campo_debito):
                    setattr(self, campo_debito, getattr(self, campo_debito) + valor)
                else:
                    self.debito_outros += valor
        
        # Calcular saldo final
        self.saldo_final = self.saldo_inicial + self.total_creditos - self.total_debitos
        
        # Salvar as alterações
        self.save(update_fields=[
            'total_creditos', 'total_debitos', 'saldo_final', 'quantidade_movimentacoes',
            'maior_credito', 'maior_debito', 'credito_adiantamentos', 'credito_pagamentos',
            'credito_ajustes', 'credito_transferencias', 'credito_financeiro', 'credito_saldo',
            'credito_outros', 'debito_adiantamentos', 'debito_despesas', 'debito_taxas',
            'debito_transferencias', 'debito_ajustes', 'debito_financeiro', 'debito_saldo',
            'debito_outros'
        ])

#--------------------------------------------------------------
# MODELO UTILITÁRIO PARA CONFIGURAÇÕES GERAIS DO SISTEMA MANUAL
class ConfiguracaoSistemaManual(models.Model):
    """
    Configurações gerais para o funcionamento do sistema manual
    
    Este modelo centraliza configurações importantes do sistema de fluxo de caixa
    manual, como limites de valores, políticas de auditoria e outras configurações
    operacionais específicas de cada conta (tenant).
    """
    
    class Meta:
        db_table = 'configuracao_sistema_manual'
        verbose_name = "Configuração do Sistema Manual"
        verbose_name_plural = "Configurações do Sistema Manual"

    conta = models.OneToOneField(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='configuracao_manual', 
        null=False
    )
    
    # === LIMITES FINANCEIROS ===
    limite_valor_alto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1000.00,
        verbose_name="Limite para Valor Alto",
        help_text="Valores acima deste limite requerem documentação obrigatória"
    )
    
    limite_aprovacao_gerencial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=5000.00,
        verbose_name="Limite para Aprovação Gerencial",
        help_text="Valores acima deste limite requerem aprovação gerencial"
    )
    
    # === POLÍTICAS DE AUDITORIA ===
    exigir_documento_para_valores_altos = models.BooleanField(
        default=True,
        verbose_name="Exigir Documento para Valores Altos",
        help_text="Se deve exigir número de documento para valores acima do limite"
    )
    
    registrar_ip_usuario = models.BooleanField(
        default=True,
        verbose_name="Registrar IP do Usuário",
        help_text="Se deve registrar o IP do usuário nos logs de auditoria"
    )
    
    dias_edicao_lancamento = models.PositiveIntegerField(
        default=7,
        verbose_name="Dias para Edição de Lançamento",
        help_text="Número de dias após criação que um lançamento pode ser editado"
    )
    
    # === CONFIGURAÇÕES DE FECHAMENTO ===
    permitir_lancamento_mes_fechado = models.BooleanField(
        default=False,
        verbose_name="Permitir Lançamento em Mês Fechado",
        help_text="Se permite lançamentos em meses já fechados (requer aprovação especial)"
    )
    
    fechamento_automatico = models.BooleanField(
        default=False,
        verbose_name="Fechamento Automático",
        help_text="Se deve fechar automaticamente o mês anterior ao iniciar um novo"
    )
    
    # === NOTIFICAÇÕES ===
    notificar_valores_altos = models.BooleanField(
        default=True,
        verbose_name="Notificar Valores Altos",
        help_text="Se deve notificar supervisores sobre lançamentos de valores altos"
    )
    
    email_notificacao = models.EmailField(
        blank=True,
        verbose_name="Email para Notificações",
        help_text="Email que receberá notificações importantes do sistema"
    )
    
    # === BACKUP E SEGURANÇA ===
    backup_automatico = models.BooleanField(
        default=True,
        verbose_name="Backup Automático",
        help_text="Se deve fazer backup automático dos dados financeiros"
    )
    
    retencao_logs_dias = models.PositiveIntegerField(
        default=365,
        verbose_name="Retenção de Logs (dias)",
        help_text="Por quantos dias manter os logs de auditoria"
    )
    
    # === CONTROLE ===
    ativa = models.BooleanField(
        default=True,
        verbose_name="Configuração Ativa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracoes_criadas',
        verbose_name="Criada Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre as configurações específicas desta conta"
    )

    def __str__(self):
        return f"Configuração Manual - {self.conta.name}"
    
    def clean(self):
        """Validações personalizadas"""
        if self.limite_aprovacao_gerencial <= self.limite_valor_alto:
            raise ValidationError(
                "O limite para aprovação gerencial deve ser maior que o limite para valor alto."
            )
        
        if self.dias_edicao_lancamento < 1:
            raise ValidationError(
                "O período de edição deve ser de pelo menos 1 dia."
            )
        
        if self.retencao_logs_dias < 30:
            raise ValidationError(
                "A retenção de logs deve ser de pelo menos 30 dias."
            )
    
    @classmethod
    def obter_configuracao(cls, conta):
        """
        Obtém ou cria a configuração para uma conta
        """
        config, created = cls.objects.get_or_create(
            conta=conta,
            defaults={
                'ativa': True
            }
        )
        return config
    
    def valor_requer_documento(self, valor):
        """Verifica se um valor requer documentação obrigatória"""
        return self.exigir_documento_para_valores_altos and valor > self.limite_valor_alto
    
    def valor_requer_aprovacao_gerencial(self, valor):
        """Verifica se um valor requer aprovação gerencial"""
        return valor > self.limite_aprovacao_gerencial
    
    def lancamento_pode_ser_editado(self, lancamento):
        """Verifica se um lançamento ainda pode ser editado"""
        from datetime import timedelta
        limite = timezone.now() - timedelta(days=self.dias_edicao_lancamento)
        return lancamento.created_at > limite
    
    @classmethod
    def criar_configuracao_padrao(cls, conta, usuario=None):
        """
        Cria uma configuração padrão para uma nova conta
        """
        config, created = cls.objects.get_or_create(
            conta=conta,
            defaults={
                'limite_valor_alto': 1000.00,
                'limite_aprovacao_gerencial': 5000.00,
                'exigir_documento_para_valores_altos': True,
                'registrar_ip_usuario': True,
                'dias_edicao_lancamento': 7,
                'permitir_lancamento_mes_fechado': False,
                'fechamento_automatico': False,
                'notificar_valores_altos': True,
                'backup_automatico': True,
                'retencao_logs_dias': 365,
                'ativa': True,
                'criada_por': usuario,
                'observacoes': 'Configuração padrão criada automaticamente para sistema manual'
            }
        )
        return config, created

#--------------------------------------------------------------
# MODELO PARA RELATÓRIOS CONSOLIDADOS DO SISTEMA MANUAL
class RelatorioConsolidadoMensal(models.Model):
    """
    Relatórios consolidados mensais do sistema de fluxo de caixa manual
    
    Este modelo gera e armazena relatórios consolidados mensais com
    estatísticas, validações e resumos operacionais do sistema manual,
    facilitando auditorias e análises gerenciais.
    """
    
    class Meta:
        db_table = 'relatorio_consolidado_mensal'
        unique_together = ('conta', 'mes_referencia')
        verbose_name = "Relatório Consolidado Mensal"
        verbose_name_plural = "Relatórios Consolidados Mensais"
        indexes = [
            models.Index(fields=['conta', 'mes_referencia']),
            models.Index(fields=['data_geracao']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='relatorios_consolidados', 
        null=False
    )
    
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Data no formato YYYY-MM-01"
    )
    
    # === ESTATÍSTICAS GERAIS ===
    total_medicos_ativos = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Médicos Ativos"
    )
    
    total_lancamentos = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Lançamentos no Mês"
    )
    
    total_valor_creditos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Total de Créditos"
    )
    
    total_valor_debitos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Total de Débitos"
    )
    
    saldo_geral_consolidado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Geral Consolidado"
    )
    
    # === DISTRIBUIÇÃO POR CATEGORIA ===
    # Créditos por categoria
    creditos_adiantamentos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    creditos_pagamentos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    creditos_ajustes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    creditos_transferencias = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    creditos_financeiro = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    creditos_saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    creditos_outros = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Débitos por categoria
    debitos_adiantamentos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_despesas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_taxas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_transferencias = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_ajustes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_financeiro = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debitos_outros = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # === ESTATÍSTICAS DE AUDITORIA ===
    lancamentos_valores_altos = models.PositiveIntegerField(
        default=0,
        verbose_name="Lançamentos com Valores Altos",
        help_text="Lançamentos acima do limite configurado"
    )
    
    lancamentos_sem_documento = models.PositiveIntegerField(
        default=0,
        verbose_name="Lançamentos sem Documento",
        help_text="Lançamentos de valor alto sem número de documento"
    )
    
    usuarios_diferentes = models.PositiveIntegerField(
        default=0,
        verbose_name="Usuários que Fizeram Lançamentos",
        help_text="Quantidade de usuários diferentes que fizeram lançamentos no mês"
    )
    
    maior_lancamento_credito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Maior Lançamento de Crédito"
    )
    
    maior_lancamento_debito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Maior Lançamento de Débito"
    )
    
    # === VALIDAÇÕES ===
    inconsistencias_encontradas = models.PositiveIntegerField(
        default=0,
        verbose_name="Inconsistências Encontradas"
    )
    
    detalhes_inconsistencias = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Detalhes das Inconsistências",
        help_text="JSON com detalhes das inconsistências encontradas"
    )
    
    # === STATUS DO RELATÓRIO ===
    STATUS_CHOICES = [
        ('gerando', 'Gerando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro na Geração'),
        ('revisao', 'Em Revisão'),
        ('aprovado', 'Aprovado'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='gerando',
        verbose_name="Status do Relatório"
    )
    
    # === CONTROLE ===
    data_geracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Geração"
    )
    
    tempo_processamento = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Tempo de Processamento",
        help_text="Tempo necessário para gerar o relatório"
    )
    
    gerado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatorios_gerados',
        verbose_name="Gerado Por"
    )
    
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatorios_aprovados',
        verbose_name="Aprovado Por"
    )
    
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Aprovação"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o relatório ou processo de geração"
    )

    def save(self, *args, **kwargs):
        # Normalizar a data para o primeiro dia do mês
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Relatório Consolidado - {self.conta.name} - {self.mes_referencia.strftime('%m/%Y')}"
    
    @property
    def mes_ano_formatado(self):
        """Retorna o mês/ano formatado"""
        return self.mes_referencia.strftime('%m/%Y')
    
    @property
    def movimentacao_liquida(self):
        """Retorna a movimentação líquida do mês"""
        return self.total_valor_creditos - self.total_valor_debitos
    
    @property
    def percentual_lancamentos_valores_altos(self):
        """Retorna o percentual de lançamentos com valores altos"""
        if self.total_lancamentos == 0:
            return 0
        return (self.lancamentos_valores_altos / self.total_lancamentos) * 100
    
    @property
    def media_valor_lancamento(self):
        """Retorna a média de valor por lançamento"""
        if self.total_lancamentos == 0:
            return 0
        return (self.total_valor_creditos + self.total_valor_debitos) / self.total_lancamentos
    
    def gerar_relatorio_completo(self):
        """
        Gera o relatório consolidado completo para o mês
        """
        from django.apps import apps
        from django.db.models import Sum, Max, Count, Q
        from datetime import datetime
        
        inicio_processamento = timezone.now()
        
        try:
            # Obter modelos dinamicamente
            Financeiro = apps.get_model('medicos', 'Financeiro')
            SaldoMensalMedico = apps.get_model('medicos', 'SaldoMensalMedico')
            ConfiguracaoSistemaManual = apps.get_model('medicos', 'ConfiguracaoSistemaManual')
            
            # Resetar valores
            self.status = 'gerando'
            self.save()
            
            # Obter configuração da conta
            config = ConfiguracaoSistemaManual.obter_configuracao(self.conta)
            
            # Buscar todos os lançamentos do mês
            lancamentos = Financeiro.objects.filter(
                conta=self.conta,
                data__year=self.mes_referencia.year,
                data__month=self.mes_referencia.month,
                status__in=['processado', 'conciliado', 'transferido']
            )
            
            # Estatísticas gerais
            self.total_lancamentos = lancamentos.count()
            
            # Buscar médicos ativos no mês
            medicos_ativos = lancamentos.values('socio').distinct().count()
            self.total_medicos_ativos = medicos_ativos
            
            # Totais por tipo
            creditos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_CREDITO)
            debitos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_DEBITO)
            
            self.total_valor_creditos = creditos.aggregate(Sum('valor'))['valor__sum'] or 0
            self.total_valor_debitos = debitos.aggregate(Sum('valor'))['valor__sum'] or 0
            
            # Maiores lançamentos
            self.maior_lancamento_credito = creditos.aggregate(Max('valor'))['valor__max'] or 0
            self.maior_lancamento_debito = debitos.aggregate(Max('valor'))['valor__max'] or 0
            
            # Usuários diferentes
            self.usuarios_diferentes = lancamentos.values('processado_por').distinct().count()
            
            # Distribuição por categoria
            self._calcular_distribuicao_categorias(lancamentos)
            
            # Validações de auditoria
            self._executar_validacoes_auditoria(lancamentos, config)
            
            # Buscar saldos mensais para consolidação
            saldos_mensais = SaldoMensalMedico.objects.filter(
                conta=self.conta,
                mes_referencia=self.mes_referencia
            )
            
            self.saldo_geral_consolidado = saldos_mensais.aggregate(
                Sum('saldo_final')
            )['saldo_final__sum'] or 0
            
            # Finalizar
            self.status = 'concluido'
            self.tempo_processamento = timezone.now() - inicio_processamento
            self.save()
            
            # Registrar no log de auditoria
            from django.apps import apps
            LogAuditoriaFinanceiro = apps.get_model('medicos', 'LogAuditoriaFinanceiro')
            LogAuditoriaFinanceiro.registrar_acao(
                conta=self.conta,
                usuario=self.gerado_por,
                acao='gerar_relatorio',
                descricao_acao=f"Geração de relatório consolidado mensal: {self.mes_ano_formatado}",
                valores_novos={
                    'total_lancamentos': self.total_lancamentos,
                    'total_creditos': str(self.total_valor_creditos),
                    'total_debitos': str(self.total_valor_debitos),
                    'saldo_consolidado': str(self.saldo_geral_consolidado),
                    'inconsistencias': self.inconsistencias_encontradas,
                    'tempo_processamento': str(self.tempo_processamento)
                }
            )
            
        except Exception as e:
            self.status = 'erro'
            self.observacoes = f"Erro na geração: {str(e)}"
            self.save()
            raise
    
    def _calcular_distribuicao_categorias(self, lancamentos):
        """Calcula a distribuição por categorias"""
        from django.apps import apps
        
        # Obter modelo dinamicamente
        Desc_movimentacao_financeiro = apps.get_model('medicos', 'Desc_movimentacao_financeiro')
        
        # Mapeamento de categorias para campos
        categorias_credito = {
            'adiantamento': 'creditos_adiantamentos',
            'pagamento': 'creditos_pagamentos', 
            'ajuste': 'creditos_ajustes',
            'transferencia': 'creditos_transferencias',
            'financeiro': 'creditos_financeiro',
            'saldo': 'creditos_saldo',
            'outros': 'creditos_outros'
        }
        
        categorias_debito = {
            'adiantamento': 'debitos_adiantamentos',
            'despesa': 'debitos_despesas',
            'taxa': 'debitos_taxas', 
            'transferencia': 'debitos_transferencias',
            'ajuste': 'debitos_ajustes',
            'financeiro': 'debito_financeiro',
            'saldo': 'debito_saldo',
            'outros': 'debito_outros'
        }
        
        # Processar créditos
        for categoria, campo in categorias_credito.items():
            valor = lancamentos.filter(
                tipo=TIPO_MOVIMENTACAO_CONTA_CREDITO,
                descricao__categoria=categoria
            ).aggregate(models.Sum('valor'))['valor__sum'] or 0
            setattr(self, campo, valor)
        
        # Processar débitos
        for categoria, campo in categorias_debito.items():
            valor = lancamentos.filter(
                tipo=TIPO_MOVIMENTACAO_CONTA_DEBITO,
                descricao__categoria=categoria
            ).aggregate(models.Sum('valor'))['valor__sum'] or 0
            setattr(self, campo, valor)
    
    def _executar_validacoes_auditoria(self, lancamentos, config):
        """Executa validações de auditoria"""
        inconsistencias = []
        
        # Validar lançamentos com valores altos
        valores_altos = lancamentos.filter(valor__gt=config.limite_valor_alto)
        self.lancamentos_valores_altos = valores_altos.count()
        
        # Validar lançamentos sem documento
        sem_documento = valores_altos.filter(
            models.Q(numero_documento__isnull=True) | models.Q(numero_documento='')
        )
        self.lancamentos_sem_documento = sem_documento.count()
        
        if self.lancamentos_sem_documento > 0:
            inconsistencias.append({
                'tipo': 'documento_faltante',
                'quantidade': self.lancamentos_sem_documento,
                'descricao': f'{self.lancamentos_sem_documento} lançamentos de valor alto sem documento'
            })
        
        # Validar consistência de datas
        data_futura = lancamentos.filter(data__gt=timezone.now().date()).count()
        if data_futura > 0:
            inconsistencias.append({
                'tipo': 'data_futura',
                'quantidade': data_futura,
                'descricao': f'{data_futura} lançamentos com data futura'
            })
        
        # Salvar inconsistências
        self.inconsistencias_encontradas = len(inconsistencias)
        if inconsistencias:
            self.detalhes_inconsistencias = inconsistencias
    
    def aprovar_relatorio(self, usuario):
        """Aprova o relatório após revisão"""
        if self.status != 'concluido':
            raise ValidationError("Apenas relatórios concluídos podem ser aprovados.")
        
        self.status = 'aprovado'
        self.aprovado_por = usuario
        self.data_aprovacao = timezone.now()
        self.save()
    
    @classmethod
    def gerar_relatorio_mensal(cls, conta, mes_referencia, usuario=None):
        """
        Gera um novo relatório consolidado mensal
        """
        # Normalizar data
        mes_referencia = mes_referencia.replace(day=1)
        
        # Verificar se já existe
        relatorio, created = cls.objects.get_or_create(
            conta=conta,
            mes_referencia=mes_referencia,
            defaults={
                'gerado_por': usuario,
                'status': 'gerando'
            }
        )
        
        if not created:
            # Se já existe, regerar
            relatorio.gerado_por = usuario
            relatorio.status = 'gerando'
            relatorio.save()
        
        # Gerar o relatório
        relatorio.gerar_relatorio_completo()
        
        return relatorio

