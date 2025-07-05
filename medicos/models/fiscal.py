from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .base import (
    Conta, Empresa, NFISCAL_ALIQUOTA_CONSULTAS, NFISCAL_ALIQUOTA_PLANTAO, 
    NFISCAL_ALIQUOTA_OUTROS
)

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
        verbose_name = "Configuração de Alíquotas"
        verbose_name_plural = "Configurações de Alíquotas"
        unique_together = ('conta', 'ativa')

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='aliquotas', 
        null=False,
        verbose_name="Conta",
        help_text="Conta/cliente proprietária destas configurações tributárias"
    )
    
    # === IMPOSTOS MUNICIPAIS POR TIPO DE SERVIÇO ===
    ISS_CONSULTAS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Consultas (%)",
        help_text="Alíquota do ISS para prestação de serviços de consulta médica"
    )
    
    ISS_PLANTAO = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Plantão (%)",
        help_text="Alíquota do ISS para prestação de serviços de plantão médico"
    )
    
    ISS_OUTROS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Outros Serviços (%)",
        help_text="Alíquota do ISS para vacinação, exames, procedimentos e outros serviços"
    )
    
    # === CONTRIBUIÇÕES FEDERAIS ===
    PIS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="PIS (%)",
        help_text="Alíquota do PIS (geralmente 0,65%)"
    )
    
    COFINS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="COFINS (%)",
        help_text="Alíquota da COFINS (geralmente 3%)"
    )
    
    # === IMPOSTO DE RENDA PESSOA JURÍDICA ===
    IRPJ_BASE_CAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=32.00,
        verbose_name="IRPJ - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo do IRPJ (padrão 32%)"
    )
    
    IRPJ_ALIC_1 = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=15.00,
        verbose_name="IRPJ - Alíquota Normal (%)",
        help_text="Alíquota normal do IRPJ (padrão 15%)"
    )
    
    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = models.DecimalField(
        max_digits=12, decimal_places=2, null=False, default=60000.00,
        verbose_name="IRPJ - Limite para Adicional (R$)",
        help_text="Valor limite trimestral para adicional (padrão R$ 60.000,00)"
    )
    
    IRPJ_ADICIONAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=10.00,
        verbose_name="IRPJ - Adicional (%)",
        help_text="Alíquota do adicional de IRPJ (padrão 10%)"
    )
    
    # === CONTRIBUIÇÃO SOCIAL SOBRE O LUCRO LÍQUIDO ===
    CSLL_BASE_CAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=32.00,
        verbose_name="CSLL - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo da CSLL (padrão 32%)"
    )
    
    CSLL_ALIC_1 = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=9.00,
        verbose_name="CSLL - Alíquota Normal (%)",
        help_text="Alíquota normal da CSLL (padrão 9%)"
    )
    
    CSLL_ALIC_2 = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=15.00,
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
        null=True, blank=True,
        verbose_name="Início da Vigência",
        help_text="Data de início da vigência desta configuração tributária"
    )
    
    data_vigencia_fim = models.DateField(
        null=True, blank=True,
        verbose_name="Fim da Vigência",
        help_text="Data de fim da vigência (deixe vazio se não há limite)"
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='aliquotas_criadas',
        verbose_name="Criado por"
    )
    
    observacoes = models.TextField(
        blank=True, verbose_name="Observações",
        help_text="Observações sobre as particularidades desta configuração tributária"
    )

    def clean(self):
        campos_percentuais = [
            ('ISS_CONSULTAS', self.ISS_CONSULTAS, 0, 20),
            ('ISS_PLANTAO', self.ISS_PLANTAO, 0, 20),
            ('ISS_OUTROS', self.ISS_OUTROS, 0, 20),
            ('PIS', self.PIS, 0, 10),
            ('COFINS', self.COFINS, 0, 10),
            ('IRPJ_BASE_CAL', self.IRPJ_BASE_CAL, 0, 100),
            ('IRPJ_ALIC_1', self.IRPJ_ALIC_1, 0, 50),
            ('IRPJ_ADICIONAL', self.IRPJ_ADICIONAL, 0, 50),
            ('CSLL_BASE_CAL', self.CSLL_BASE_CAL, 0, 100),
            ('CSLL_ALIC_1', self.CSLL_ALIC_1, 0, 50),
            ('CSLL_ALIC_2', self.CSLL_ALIC_2, 0, 50),
        ]
        
        for nome, valor, minimo, maximo in campos_percentuais:
            if valor < minimo or valor > maximo:
                raise ValidationError({
                    nome.lower(): f'{nome} deve estar entre {minimo}% e {maximo}%'
                })
        
        # Validar datas de vigência
        if (self.data_vigencia_inicio and self.data_vigencia_fim and 
            self.data_vigencia_inicio > self.data_vigencia_fim):
            raise ValidationError({
                'data_vigencia_fim': 'Data fim deve ser posterior à data início'
            })

    def __str__(self):
        return f"Alíquotas - {self.conta.name} (ISS Consultas: {self.ISS_CONSULTAS}%, Plantão: {self.ISS_PLANTAO}%, Outros: {self.ISS_OUTROS}%)"
    
    @property
    def eh_vigente(self):
        hoje = timezone.now().date()
        if self.data_vigencia_inicio and hoje < self.data_vigencia_inicio:
            return False
        if self.data_vigencia_fim and hoje > self.data_vigencia_fim:
            return False
        return self.ativa
    
    def calcular_impostos_nf(self, valor_bruto, tipo_servico='consultas'):
        """Calcula os impostos para uma nota fiscal baseado no tipo de serviço prestado"""
        if not self.eh_vigente:
            raise ValidationError("Esta configuração de alíquotas não está vigente.")
        
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
            aliquota_iss = self.ISS_CONSULTAS
            descricao_servico = "Consultas Médicas"
        
        # Cálculos básicos
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
        """Obtém a configuração de alíquotas vigente para uma conta"""
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        return cls.objects.filter(
            conta=conta,
            ativa=True,
            data_vigencia_inicio__lte=data_referencia
        ).filter(
            models.Q(data_vigencia_fim__isnull=True) | 
            models.Q(data_vigencia_fim__gte=data_referencia)
        ).first()

class NotaFiscal(models.Model):
    """Notas fiscais emitidas para as empresas/associações médicas"""
    
    class Meta:
        db_table = 'nota_fiscal'
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='notas_fiscais', null=False)
    
    class Aliquota_t(models.IntegerChoices):
        CONSULTAS = NFISCAL_ALIQUOTA_CONSULTAS, "CONSULTAS MÉDICAS"
        PLANTAO   = NFISCAL_ALIQUOTA_PLANTAO, "PLANTÃO MÉDICO"  
        OUTROS    = NFISCAL_ALIQUOTA_OUTROS, "VACINAÇÃO/EXAMES/PROCEDIMENTOS"

    # Dados da nota fiscal
    numero = models.CharField(max_length=255, null=True, verbose_name="Número da NF")
    serie = models.CharField(max_length=10, blank=True, verbose_name="Série")
    
    # Relacionamentos
    empresa_destinataria = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, 
        related_name='notas_fiscais_recebidas',
        verbose_name="Empresa Destinatária"
    )
    tomador = models.CharField(max_length=255, null=True, verbose_name="Tomador dos Serviços")
    
    # Datas
    dtEmissao = models.DateField(null=False, verbose_name="Data de Emissão")
    dtRecebimento = models.DateField(null=True, blank=True, verbose_name="Data de Recebimento")
    dtVencimento = models.DateField(null=True, blank=True, verbose_name="Data de Vencimento")
    
    # Valores
    val_bruto = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor Bruto")
    val_liquido = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor Líquido")
    
    # Impostos retidos
    val_ISS = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor ISS")
    val_PIS = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor PIS")
    val_COFINS = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor COFINS")
    val_IR = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor IR")
    val_CSLL = models.DecimalField(max_digits=12, decimal_places=2, null=False, default=0, verbose_name="Valor CSLL")
    
    # Tipo de serviço prestado
    tipo_aliquota = models.PositiveSmallIntegerField(
        choices=Aliquota_t.choices, default=Aliquota_t.CONSULTAS,
        verbose_name="Tipo de Serviço Médico"
    )
    
    # Descrição dos serviços
    descricao_servicos = models.TextField(blank=True, verbose_name="Descrição dos Serviços")
    
    # Status de processamento
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Lançamento'),
        ('lancada', 'Lançada no Financeiro'),
        ('rateada', 'Rateada entre Médicos'),
        ('paga', 'Paga'),
        ('cancelada', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    
    # Controle
    ja_rateada = models.BooleanField(default=False, verbose_name="Já foi rateada")
    data_lancamento = models.DateTimeField(null=True, blank=True, verbose_name="Data de Lançamento")
    lancada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notas_fiscais_lancadas',
        verbose_name="Lançada Por"
    )
    
    # Dados adicionais
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"NF {self.numero} - {self.empresa_destinataria.name} - R$ {self.val_bruto}"
    
    @property
    def pode_ser_rateada(self):
        """Verifica se a NF pode ser rateada"""
        return self.status in ['pendente', 'lancada'] and not self.ja_rateada

# Modelos de apuração (simplificados para reduzir tamanho)
class Balanco(models.Model):
    class Meta:
        db_table = 'balanco'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='balancos', null=False)
    data = models.DateField(null=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    # ... outros campos conforme necessário

class Apuracao_pis(models.Model):
    class Meta:
        db_table = 'apuracao_pis'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_pis', null=False)
    data = models.DateField(null=False)
    fornecedor = models.ForeignKey(Empresa, on_delete=models.CASCADE, unique=False)
    # ... outros campos

class Apuracao_cofins(models.Model):
    class Meta:
        db_table = 'apuracao_cofins'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_cofins', null=False)
    data = models.DateField(null=False)
    fornecedor = models.ForeignKey(Empresa, on_delete=models.CASCADE, unique=False)
    # ... outros campos

class Apuracao_csll(models.Model):
    class Meta:
        db_table = 'apuracao_csll'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_csll', null=False)
    data = models.DateField(null=False)
    trimestre = models.IntegerField(null=False)
    fornecedor = models.ForeignKey(Empresa, on_delete=models.CASCADE, unique=False)
    # ... outros campos

class Apuracao_irpj(models.Model):
    class Meta:
        db_table = 'apuracao_irpj'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_irpj', null=False)
    data = models.DateField(null=False)
    trimestre = models.IntegerField(null=False)
    fornecedor = models.ForeignKey(Empresa, on_delete=models.CASCADE, unique=False)
    # ... outros campos

class Apuracao_iss(models.Model):
    class Meta:
        db_table = 'apuracao_iss'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='apuracao_iss', null=False)
    data = models.DateField(null=False)
    fornecedor = models.ForeignKey(Empresa, on_delete=models.CASCADE, unique=False)
    # ... outros campos

class Aplic_financeiras(models.Model):
    class Meta:
        db_table = 'aplic_financeiras'
    
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='aplic_financeiras', null=False)
    data = models.DateField(null=False)
    fornecedor = models.ForeignKey(Empresa, on_delete=models.CASCADE, unique=False)
    # ... outros campos
