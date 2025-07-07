"""
Modelos relacionados ao sistema financeiro manual

Este módulo contém todos os modelos relacionados ao fluxo de caixa manual
da aplicação de médicos, incluindo descrições de movimentação, lançamentos
financeiros e saldos mensais consolidados.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Conta, SaaSBaseModel, Empresa, Socio

# Constantes específicas para financeiro
TIPO_MOVIMENTACAO_CONTA_CREDITO = 1    # entradas, creditos, depositos
TIPO_MOVIMENTACAO_CONTA_DEBITO = 2     # retiradas, transferencia

# DESCRICAO PADRONIZADA DE MOVIMENTAÇÃO AUTOMÁTICA REALIZADA PELO SISTEMA
DESC_MOVIMENTACAO_CREDITO_SALDO_MES_SEGUINTE = 'CREDITO SALDO MES ANTERIOR'
DESC_MOVIMENTACAO_DEBITO_IMPOSTO_PROVISIONADOS = 'DEBITO PAGAMENTO DE IMPOSTOS'


class MeioPagamento(models.Model):
    """
    Meios de pagamento cadastrados pelos usuários
    
    Este modelo armazena os meios de pagamento específicos que podem ser
    utilizados nas movimentações financeiras, com suas respectivas taxas,
    prazos de compensação e outras características.
    """
    
    class Meta:
        db_table = 'meio_pagamento'
        unique_together = ('conta', 'codigo')
        verbose_name = "Meio de Pagamento"
        verbose_name_plural = "Meios de Pagamento"
        indexes = [
            models.Index(fields=['conta', 'ativo']),
            models.Index(fields=['codigo']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='meios_pagamento', 
        null=False
    )
    
    # Identificação do meio
    codigo = models.CharField(
        max_length=20,
        verbose_name="Código",
        help_text="Código único para identificar o meio de pagamento (ex: DINHEIRO, PIX, CARTAO_CREDITO)"
    )
    
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome",
        help_text="Nome descritivo do meio de pagamento"
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição detalhada do meio de pagamento"
    )
    
    # Configurações financeiras
    taxa_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Taxa (%)",
        help_text="Taxa percentual cobrada por este meio de pagamento"
    )
    
    taxa_fixa = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name="Taxa Fixa (R$)",
        help_text="Valor fixo cobrado por transação (além da taxa percentual)"
    )
    
    valor_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Mínimo",
        help_text="Valor mínimo aceito para este meio de pagamento"
    )
    
    valor_maximo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Máximo",
        help_text="Valor máximo aceito para este meio de pagamento"
    )
    
    # Prazos e disponibilidade
    prazo_compensacao_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Prazo de Compensação (dias)",
        help_text="Quantos dias demora para o valor estar disponível"
    )
    
    horario_limite = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Horário Limite",
        help_text="Horário limite para transações no mesmo dia (opcional)"
    )
    
    # Configurações de uso
    TIPOS_MOVIMENTACAO = [
        ('credito', 'Apenas Créditos'),
        ('debito', 'Apenas Débitos'),
        ('ambos', 'Créditos e Débitos'),
    ]
    
    tipo_movimentacao = models.CharField(
        max_length=10,
        choices=TIPOS_MOVIMENTACAO,
        default='ambos',
        verbose_name="Tipo de Movimentação",
        help_text="Tipos de movimentação permitidos com este meio"
    )
    
    exige_documento = models.BooleanField(
        default=False,
        verbose_name="Exige Documento",
        help_text="Se transações com este meio exigem número de documento"
    )
    
    exige_aprovacao = models.BooleanField(
        default=False,
        verbose_name="Exige Aprovação",
        help_text="Se transações com este meio exigem aprovação adicional"
    )
    
    # Status e controle
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se este meio de pagamento está disponível para uso"
    )
    
    data_inicio_vigencia = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Início de Vigência",
        help_text="A partir de quando este meio pode ser usado"
    )
    
    data_fim_vigencia = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Fim de Vigência",
        help_text="Até quando este meio pode ser usado"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meios_pagamento_criados',
        verbose_name="Criado Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre este meio de pagamento"
    )

    def clean(self):
        """Validações personalizadas"""
        # Validar taxas
        if self.taxa_percentual < 0 or self.taxa_percentual > 100:
            raise ValidationError({
                'taxa_percentual': 'Taxa percentual deve estar entre 0% e 100%'
            })
        
        if self.taxa_fixa < 0:
            raise ValidationError({
                'taxa_fixa': 'Taxa fixa não pode ser negativa'
            })
        
        # Validar valores mínimo e máximo
        if self.valor_minimo is not None and self.valor_minimo < 0:
            raise ValidationError({
                'valor_minimo': 'Valor mínimo não pode ser negativo'
            })
        
        if self.valor_maximo is not None and self.valor_maximo < 0:
            raise ValidationError({
                'valor_maximo': 'Valor máximo não pode ser negativo'
            })
        
        if (self.valor_minimo is not None and self.valor_maximo is not None 
            and self.valor_minimo > self.valor_maximo):
            raise ValidationError({
                'valor_maximo': 'Valor máximo deve ser maior que o valor mínimo'
            })
        
        # Validar datas de vigência
        if (self.data_inicio_vigencia and self.data_fim_vigencia 
            and self.data_inicio_vigencia > self.data_fim_vigencia):
            raise ValidationError({
                'data_fim_vigencia': 'Data de fim deve ser posterior à data de início'
            })
        
        # Validar unicidade do código por conta
        if self.codigo:
            qs = MeioPagamento.objects.filter(
                conta=self.conta,
                codigo=self.codigo
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                raise ValidationError({
                    'codigo': 'Já existe um meio de pagamento com este código nesta conta'
                })

    def __str__(self):
        return f"{self.nome} ({self.codigo})"
    
    @property
    def nome_completo(self):
        """Retorna nome com código para identificação"""
        taxa_info = ""
        if self.taxa_percentual > 0 or self.taxa_fixa > 0:
            partes_taxa = []
            if self.taxa_percentual > 0:
                partes_taxa.append(f"{self.taxa_percentual}%")
            if self.taxa_fixa > 0:
                partes_taxa.append(f"R${self.taxa_fixa}")
            taxa_info = f" (taxa: {' + '.join(partes_taxa)})"
        
        return f"{self.nome}{taxa_info}"
    
    @property
    def esta_vigente(self):
        """Verifica se o meio está vigente na data atual"""
        hoje = timezone.now().date()
        
        if self.data_inicio_vigencia and hoje < self.data_inicio_vigencia:
            return False
        
        if self.data_fim_vigencia and hoje > self.data_fim_vigencia:
            return False
        
        return True
    
    @property
    def disponivel_para_uso(self):
        """Verifica se o meio está disponível para uso"""
        return self.ativo and self.esta_vigente
    
    def calcular_valor_liquido(self, valor_bruto):
        """Calcula o valor líquido após aplicar as taxas"""
        if valor_bruto <= 0:
            return 0
        
        # Aplicar taxa percentual
        valor_taxa_percentual = valor_bruto * (self.taxa_percentual / 100)
        
        # Aplicar taxa fixa
        valor_taxa_total = valor_taxa_percentual + self.taxa_fixa
        
        # Calcular valor líquido
        valor_liquido = valor_bruto - valor_taxa_total
        
        # Garantir que não seja negativo
        return max(0, valor_liquido)
    
    def calcular_taxas(self, valor_bruto):
        """Calcula os valores das taxas aplicadas"""
        if valor_bruto <= 0:
            return {
                'taxa_percentual_valor': 0,
                'taxa_fixa_valor': 0,
                'taxa_total': 0,
                'valor_liquido': 0
            }
        
        taxa_percentual_valor = valor_bruto * (self.taxa_percentual / 100)
        taxa_fixa_valor = self.taxa_fixa
        taxa_total = taxa_percentual_valor + taxa_fixa_valor
        valor_liquido = max(0, valor_bruto - taxa_total)
        
        return {
            'taxa_percentual_valor': taxa_percentual_valor,
            'taxa_fixa_valor': taxa_fixa_valor,
            'taxa_total': taxa_total,
            'valor_liquido': valor_liquido
        }
    
    def validar_valor(self, valor):
        """Valida se um valor é aceito por este meio de pagamento"""
        if not self.disponivel_para_uso:
            raise ValidationError("Este meio de pagamento não está disponível")
        
        if self.valor_minimo and valor < self.valor_minimo:
            raise ValidationError(f"Valor mínimo para {self.nome}: R$ {self.valor_minimo}")
        
        if self.valor_maximo and valor > self.valor_maximo:
            raise ValidationError(f"Valor máximo para {self.nome}: R$ {self.valor_maximo}")
    
    def pode_ser_usado_para(self, tipo_movimentacao):
        """Verifica se pode ser usado para um tipo específico de movimentação"""
        if self.tipo_movimentacao == 'ambos':
            return True
        
        if tipo_movimentacao == TIPO_MOVIMENTACAO_CONTA_CREDITO:
            return self.tipo_movimentacao == 'credito'
        elif tipo_movimentacao == TIPO_MOVIMENTACAO_CONTA_DEBITO:
            return self.tipo_movimentacao == 'debito'
        
        return False
    
    @classmethod
    def obter_ativos(cls, conta):
        """Obtém todos os meios de pagamento ativos para uma conta"""
        return cls.objects.filter(
            conta=conta,
            ativo=True
        ).order_by('nome')
    
    @classmethod
    def obter_disponiveis(cls, conta):
        """Obtém todos os meios de pagamento disponíveis para uso"""
        hoje = timezone.now().date()
        
        return cls.objects.filter(
            conta=conta,
            ativo=True
        ).filter(
            models.Q(data_inicio_vigencia__isnull=True) | 
            models.Q(data_inicio_vigencia__lte=hoje)
        ).filter(
            models.Q(data_fim_vigencia__isnull=True) | 
            models.Q(data_fim_vigencia__gte=hoje)
        ).order_by('nome')
    
    @classmethod
    def obter_por_codigo(cls, conta, codigo):
        """Obtém um meio de pagamento específico pelo código"""
        try:
            return cls.objects.get(
                conta=conta,
                codigo=codigo,
                ativo=True
            )
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def criar_meios_padrao(cls, conta, usuario=None):
        """Cria meios de pagamento padrão para uma nova conta"""
        meios_padrao = [
            {
                'codigo': 'DINHEIRO',
                'nome': 'Dinheiro',
                'descricao': 'Pagamento em dinheiro/espécie',
                'taxa_percentual': 0.00,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 0,
                'tipo_movimentacao': 'ambos',
            },
            {
                'codigo': 'PIX',
                'nome': 'PIX',
                'descricao': 'Transferência instantânea via PIX',
                'taxa_percentual': 0.00,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 0,
                'tipo_movimentacao': 'ambos',
            },
            {
                'codigo': 'CARTAO_CREDITO',
                'nome': 'Cartão de Crédito',
                'descricao': 'Pagamento via cartão de crédito',
                'taxa_percentual': 3.50,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 30,
                'tipo_movimentacao': 'credito',
                'exige_documento': True,
            },
            {
                'codigo': 'CARTAO_DEBITO',
                'nome': 'Cartão de Débito',
                'descricao': 'Pagamento via cartão de débito',
                'taxa_percentual': 1.50,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 1,
                'tipo_movimentacao': 'credito',
                'exige_documento': True,
            },
            {
                'codigo': 'TRANSFERENCIA',
                'nome': 'Transferência Bancária',
                'descricao': 'Transferência entre contas bancárias',
                'taxa_percentual': 0.00,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 1,
                'tipo_movimentacao': 'ambos',
                'exige_documento': True,
            },
            {
                'codigo': 'DEPOSITO',
                'nome': 'Depósito em Conta',
                'descricao': 'Depósito direto em conta bancária',
                'taxa_percentual': 0.00,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 1,
                'tipo_movimentacao': 'credito',
                'exige_documento': True,
            },
            {
                'codigo': 'CHEQUE',
                'nome': 'Cheque',
                'descricao': 'Pagamento via cheque',
                'taxa_percentual': 0.00,
                'taxa_fixa': 0.00,
                'prazo_compensacao_dias': 3,
                'tipo_movimentacao': 'credito',
                'exige_documento': True,
            },
        ]
        
        meios_criados = []
        for meio_data in meios_padrao:
            # Verificar se já existe
            if not cls.objects.filter(
                conta=conta,
                codigo=meio_data['codigo']
            ).exists():
                meio = cls.objects.create(
                    conta=conta,
                    criado_por=usuario,
                    observacoes='Meio de pagamento criado automaticamente',
                    **meio_data
                )
                meios_criados.append(meio)
        
        return meios_criados


class DescricaoMovimentacaoFinanceira(models.Model):
    """
    Descrições de movimentação financeira cadastradas pelos usuários
    
    Este modelo permite que os usuários criem e gerenciem suas próprias
    descrições padronizadas para categorizar movimentações financeiras,
    facilitando a organização e relatórios personalizados.
    """
    
    class Meta:
        db_table = 'descricao_movimentacao'
        unique_together = ('conta', 'nome')
        verbose_name = "Descrição de Movimentação"
        verbose_name_plural = "Descrições de Movimentação"
        indexes = [
            models.Index(fields=['conta']),
            models.Index(fields=['desc_movimentacao']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='descricoes_movimentacao', 
        null=False
    )
    
    # Identificação da descrição
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome",
        help_text="Nome da descrição de movimentação"
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição Detalhada",
        help_text="Descrição completa sobre quando usar esta movimentação"
    )
    
    # Configurações de comportamento
    TIPOS_MOVIMENTACAO = [
        ('credito', 'Apenas Créditos'),
        ('debito', 'Apenas Débitos'),
        ('ambos', 'Créditos e Débitos'),
    ]
    
    tipo_movimentacao = models.CharField(
        max_length=10,
        choices=TIPOS_MOVIMENTACAO,
        default='ambos',
        verbose_name="Tipo de Movimentação",
        help_text="Tipos de movimentação permitidos com esta descrição"
    )
    
    exige_documento = models.BooleanField(
        default=False,
        verbose_name="Exige Documento",
        help_text="Se movimentações com esta descrição exigem número de documento"
    )
    
    exige_aprovacao = models.BooleanField(
        default=False,
        verbose_name="Exige Aprovação",
        help_text="Se movimentações com esta descrição exigem aprovação adicional"
    )
    
    # Configurações contábeis/fiscais
    codigo_contabil = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Código Contábil",
        help_text="Código contábil para classificação (plano de contas)"
    )
    
    possui_retencao_ir = models.BooleanField(
        default=False,
        verbose_name="Possui Retenção IR",
        help_text="Se esta movimentação possui retenção de Imposto de Renda"
    )
    
    percentual_retencao_ir = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="% Retenção IR",
        help_text="Percentual de retenção de IR aplicado"
    )
    
    # Controle de uso
    uso_frequente = models.BooleanField(
        default=False,
        verbose_name="Uso Frequente",
        help_text="Marcar para mostrar em destaque nas seleções"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='descricoes_movimentacao_criadas',
        verbose_name="Criada Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o uso desta descrição"
    )

    def clean(self):
        """Validações personalizadas"""
        # Validar percentual de retenção
        if self.percentual_retencao_ir < 0 or self.percentual_retencao_ir > 100:
            raise ValidationError({
                'percentual_retencao_ir': 'Percentual de retenção deve estar entre 0% e 100%'
            })
        
        # Se não possui retenção, o percentual deve ser zero
        if not self.possui_retencao_ir and self.percentual_retencao_ir > 0:
            raise ValidationError({
                'percentual_retencao_ir': 'Percentual deve ser zero se não possui retenção'
            })
        
        # Validar unicidade do nome por conta
        if self.nome:
            qs = DescricaoMovimentacaoFinanceira.objects.filter(
                conta=self.conta,
                nome=self.nome
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                raise ValidationError({
                    'nome': 'Já existe uma descrição com este nome nesta conta'
                })

    def __str__(self):
        return f"{self.nome}"
    
    @property
    def esta_vigente(self):
        """Verifica se a descrição está vigente na data atual"""
        hoje = timezone.now().date()
        
        if self.data_inicio_vigencia and hoje < self.data_inicio_vigencia:
            return False
        
        if self.data_fim_vigencia and hoje > self.data_fim_vigencia:
            return False
        
        return True
    
    @property
    def disponivel_para_uso(self):
        """Verifica se a descrição está disponível para uso"""
        return self.ativa and self.esta_vigente
    
    def calcular_retencao_ir(self, valor_base):
        """Calcula o valor da retenção de IR"""
        if not self.possui_retencao_ir or self.percentual_retencao_ir <= 0:
            return 0
        
        return valor_base * (self.percentual_retencao_ir / 100)
    
    @classmethod
    def obter_ativas(cls, conta):
        """Obtém todas as descrições para uma conta"""
        return cls.objects.filter(
            conta=conta
        ).order_by(
            'nome'
        )
    
    @classmethod
    def obter_creditos(cls, conta):
        """Obtém apenas descrições para crédito"""
        return cls.objects.filter(
            conta=conta,
            tipo_movimentacao__in=['credito', 'ambos']
        ).order_by(
            'nome'
        )
    
    @classmethod
    def obter_debitos(cls, conta):
        """Obtém apenas descrições para débito"""
        return cls.objects.filter(
            conta=conta,
            tipo_movimentacao__in=['debito', 'ambos']
        ).order_by(
            'nome'
        )
    
    @classmethod
    def obter_frequentes(cls, conta):
        """Obtém descrições marcadas como uso frequente"""
        return cls.objects.filter(
            conta=conta,
            ativa=True,
            uso_frequente=True
        ).order_by(
            'nome'
        )
    
    @classmethod
    def criar_descricoes_padrao(cls, conta, usuario=None):
        """Cria descrições padrão para uma nova conta"""
        descricoes_padrao = [
            # Receitas
            {
                'nome': 'Recebimento de Honorários Médicos',
                'tipo_movimentacao': 'credito',
                'descricao': 'Recebimento de honorários por serviços médicos prestados',
                'uso_frequente': True,
                'exige_documento': True,
            },
            {
                'nome': 'Recebimento de Consultas',
                'tipo_movimentacao': 'credito',
                'descricao': 'Recebimento por consultas médicas realizadas',
                'uso_frequente': True,
            },
            {
                'nome': 'Recebimento de Plantão',
                'tipo_movimentacao': 'credito',
                'descricao': 'Recebimento por plantões médicos realizados',
                'uso_frequente': True,
            },
            
            # Adiantamentos
            {
                'nome': 'Adiantamento de Lucros',
                'tipo_movimentacao': 'credito',
                'descricao': 'Adiantamento de lucros da sociedade médica',
                'uso_frequente': True,
            },
            {
                'nome': 'Adiantamento para Despesas',
                'tipo_movimentacao': 'debito',
                'descricao': 'Adiantamento concedido para cobrir despesas',
            },
            
            # Despesas
            {
                'nome': 'Despesas com Material Médico',
                'tipo_movimentacao': 'debito',
                'descricao': 'Gastos com materiais médicos e insumos',
                'exige_documento': True,
            },
            {
                'nome': 'Despesas com Educação Médica',
                'tipo_movimentacao': 'debito',
                'descricao': 'Gastos com cursos, congressos e capacitação',
                'exige_documento': True,
            },
            {
                'nome': 'Retirada para Uso Pessoal',
                'tipo_movimentacao': 'debito',
                'descricao': 'Retirada de valores para uso pessoal',
                'uso_frequente': True,
            },
            
            # Transferências
            {
                'nome': 'Transferência Bancária Recebida',
                'tipo_movimentacao': 'credito',
                'descricao': 'Transferência bancária recebida de terceiros',
                'exige_documento': True,
            },
            {
                'nome': 'Transferência Bancária Enviada',
                'tipo_movimentacao': 'debito',
                'descricao': 'Transferência bancária enviada para terceiros',
                'exige_documento': True,
            },
            
            # Ajustes
            {
                'nome': 'Ajuste Contábil a Crédito',
                'tipo_movimentacao': 'credito',
                'descricao': 'Ajuste contábil positivo',
                'exige_aprovacao': True,
            },
            {
                'nome': 'Ajuste Contábil a Débito',
                'tipo_movimentacao': 'debito',
                'descricao': 'Ajuste contábil negativo',
                'exige_aprovacao': True,
            },
        ]
        
        descricoes_criadas = []
        for desc_data in descricoes_padrao:
            # Verificar se já existe
            if not cls.objects.filter(
                conta=conta,
                nome=desc_data['nome']
            ).exists():
                descricao = cls.objects.create(
                    conta=conta,
                    criada_por=usuario,
                    observacoes='Descrição criada automaticamente',
                    **desc_data
                )
                descricoes_criadas.append(descricao)
        
        return descricoes_criadas


class AplicacaoFinanceira(SaaSBaseModel):
    """
    Modelo simplificado para controle de aplicações financeiras.
    
    Mantém apenas os campos essenciais: data de referência, saldo, 
    IR cobrado e descrição da aplicação.
    """
    
    class Meta:
        db_table = 'aplicacao_financeira'
        unique_together = ('conta', 'data_referencia', 'empresa')
        verbose_name = "Aplicação Financeira"
        verbose_name_plural = "Aplicações Financeiras"
        indexes = [
            models.Index(fields=['conta', 'data_referencia']),
            models.Index(fields=['empresa', 'data_referencia']),
            models.Index(fields=['data_referencia']),
        ]
    
    # Relacionamentos
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='aplicacoes_financeiras',
        help_text="Empresa/instituição financeira onde a aplicação está alocada"
    )
    
    # Campos essenciais
    data_referencia = models.DateField(
        help_text="Data de referência da aplicação (mês/ano)"
    )
    
    saldo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Saldo da aplicação financeira"
    )
    
    ir_cobrado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valor do Imposto de Renda cobrado sobre a aplicação"
    )
    
    descricao = models.CharField(
        max_length=500,
        blank=True,
        help_text="Descrição da aplicação financeira"
    )
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        if self.saldo < 0:
            raise ValidationError({'saldo': 'Saldo não pode ser negativo'})
        
        if self.ir_cobrado < 0:
            raise ValidationError({'ir_cobrado': 'IR cobrado não pode ser negativo'})
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.data_referencia.strftime('%m/%Y')} - R$ {self.saldo:,.2f}"


class Financeiro(SaaSBaseModel):
    """
    Modelo principal para lançamentos financeiros manuais
    
    Este modelo substitui e simplifica o antigo sistema de saldos mensais,
    permitindo lançamentos individuais que são consolidados dinamicamente
    conforme necessário para relatórios.
    """
    
    class Meta:
        db_table = 'financeiro'
        verbose_name = "Lançamento Financeiro"
        verbose_name_plural = "Lançamentos Financeiros"
        indexes = [
            models.Index(fields=['conta', 'data_movimentacao']),
            models.Index(fields=['socio', 'data_movimentacao']),
            models.Index(fields=['desc_movimentacao']),
            models.Index(fields=['data_movimentacao', 'tipo']),
        ]
        ordering = ['-data_movimentacao', '-created_at']

    # Relacionamentos principais
    socio = models.ForeignKey(
        Socio,
        on_delete=models.PROTECT,
        related_name='lancamentos_financeiros',
        verbose_name="Médico/Sócio",
        help_text="Médico ou sócio responsável por esta movimentação"
    )
    
    desc_movimentacao = models.ForeignKey(
        DescricaoMovimentacaoFinanceira,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name="Descrição da Movimentação",
        help_text="Descrição padronizada desta movimentação"
    )
    
    aplicacao_financeira = models.ForeignKey(
        AplicacaoFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name="Aplicação Financeira",
        help_text="Aplicação financeira relacionada (opcional)"
    )
    
    # Dados do lançamento
    data_movimentacao = models.DateField(
        verbose_name="Data da Movimentação",
        help_text="Data em que a movimentação foi realizada"
    )
    
    TIPOS_MOVIMENTACAO = [
        (TIPO_MOVIMENTACAO_CONTA_CREDITO, 'Crédito'),
        (TIPO_MOVIMENTACAO_CONTA_DEBITO, 'Débito'),
    ]
    
    tipo = models.PositiveSmallIntegerField(
        choices=TIPOS_MOVIMENTACAO,
        verbose_name="Tipo de Movimentação",
        help_text="Se é um crédito (entrada) ou débito (saída)"
    )
    
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor",
        help_text="Valor da movimentação em reais"
    )
    

    
    def clean(self):
        """Validações personalizadas"""
        super().clean()
        
        # Validar valor
        if self.valor <= 0:
            raise ValidationError({
                'valor': 'Valor deve ser positivo'
            })
        

        
        # Validar compatibilidade entre tipo e descrição
        if self.desc_movimentacao:
            if not self.desc_movimentacao.pode_ser_usada_para(self.tipo):
                tipo_display = self.get_tipo_display()
                raise ValidationError({
                    'desc_movimentacao': f'A descrição selecionada não permite movimentações do tipo {tipo_display}'
                })
        
        # Validar data de movimentação (não pode ser futura)
        if self.data_movimentacao and self.data_movimentacao > timezone.now().date():
            raise ValidationError({
                'data_movimentacao': 'Data de movimentação não pode ser futura'
            })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        sinal = "+" if self.tipo == TIPO_MOVIMENTACAO_CONTA_CREDITO else "-"
        return f"{self.socio.pessoa.name} - {self.data_movimentacao.strftime('%d/%m/%Y')} - {sinal}R$ {self.valor:,.2f}"
    
    @property
    def tipo_display_sinal(self):
        """Retorna o tipo com sinal visual"""
        if self.tipo == TIPO_MOVIMENTACAO_CONTA_CREDITO:
            return f"+ {self.get_tipo_display()}"
        else:
            return f"- {self.get_tipo_display()}"
    
    @property
    def mes_referencia(self):
        """Retorna o primeiro dia do mês da movimentação"""
        return self.data_movimentacao.replace(day=1)
    
    def pode_ser_editado(self):
        """Verifica se o lançamento pode ser editado"""
        return True  # Sempre pode ser editado na versão simplificada
    
    def pode_ser_cancelado(self):
        """Verifica se o lançamento pode ser cancelado"""
        return True  # Sempre pode ser cancelado na versão simplificada
    
    def processar(self, usuario=None):
        """Processa o lançamento - simplificado"""
        pass  # Método mantido para compatibilidade
    
    def cancelar(self, motivo=None):
        """Cancela o lançamento - simplificado"""
        pass  # Método mantido para compatibilidade
    
    @classmethod
    def obter_saldo_periodo(cls, conta, socio, data_inicio, data_fim):
        """Calcula o saldo de um período específico"""
        lancamentos = cls.objects.filter(
            conta=conta,
            socio=socio,
            data_movimentacao__range=[data_inicio, data_fim]
        )
        
        creditos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_CREDITO).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        debitos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_DEBITO).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        return {
            'total_creditos': creditos,
            'total_debitos': debitos,
            'saldo_liquido': creditos - debitos,
            'quantidade_lancamentos': lancamentos.count()
        }
    
    @classmethod
    def obter_saldo_mensal(cls, conta, socio, mes_referencia):
        """Calcula o saldo de um mês específico"""
        # Primeiro e último dia do mês
        data_inicio = mes_referencia.replace(day=1)
        ultimo_dia = 31
        while ultimo_dia > 28:
            try:
                data_fim = data_inicio.replace(day=ultimo_dia)
                break
            except ValueError:
                ultimo_dia -= 1
        
        return cls.obter_saldo_periodo(conta, socio, data_inicio, data_fim)
    
    @classmethod
    def obter_consolidado_conta(cls, conta, mes_referencia):
        """Obtém o consolidado de toda a conta em um mês"""
        data_inicio = mes_referencia.replace(day=1)
        ultimo_dia = 31
        while ultimo_dia > 28:
            try:
                data_fim = data_inicio.replace(day=ultimo_dia)
                break
            except ValueError:
                ultimo_dia -= 1
        
        lancamentos = cls.objects.filter(
            conta=conta,
            data_movimentacao__range=[data_inicio, data_fim]
        )
        
        consolidado = {
            'total_lancamentos': lancamentos.count(),
            'total_creditos': 0,
            'total_debitos': 0,
            'saldo_geral': 0,
            'medicos_ativos': 0,
            'por_socio': {},
            'por_categoria': {},
        }
        
        # Totais gerais
        creditos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_CREDITO).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        debitos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_DEBITO).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        consolidado['total_creditos'] = creditos
        consolidado['total_debitos'] = debitos
        consolidado['saldo_geral'] = creditos - debitos
        
        # Médicos ativos
        consolidado['medicos_ativos'] = lancamentos.values('socio').distinct().count()
        
        # Por sócio
        for socio in Socio.objects.filter(
            id__in=lancamentos.values_list('socio', flat=True).distinct()
        ):
            saldo_socio = cls.obter_saldo_periodo(conta, socio, data_inicio, data_fim)
            consolidado['por_socio'][socio.id] = {
                'socio': socio,
                'saldo': saldo_socio
            }
        
        # Por categoria (agora por descrição de movimentação)
        from django.db.models import Q
        categorias = lancamentos.values(
            'desc_movimentacao__nome'
        ).annotate(
            total=models.Sum('valor'),
            quantidade=models.Count('id')
        ).filter(total__gt=0)
        
        for categoria in categorias:
            nome_categoria = categoria['desc_movimentacao__nome'] or 'Sem categoria'
            consolidado['por_categoria'][nome_categoria] = {
                'total': categoria['total'],
                'quantidade': categoria['quantidade']
            }
        
        return consolidado



