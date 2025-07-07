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
            models.Index(fields=['categoria_movimentacao']),
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
    
    # Categorização dinâmica
    categoria_movimentacao = models.ForeignKey(
        'CategoriaMovimentacao',
        on_delete=models.PROTECT,
        related_name='descricoes',
        verbose_name="Categoria",
        help_text="Categoria de movimentação associada a esta descrição"
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
    def nome_completo(self):
        """Retorna nome completo com categoria"""
        categoria_display = self.categoria_movimentacao.nome if self.categoria_movimentacao else "Sem categoria"
        return f"[{categoria_display}] {self.nome}"
    
    @property
    def categoria_display(self):
        """Retorna a categoria formatada"""
        return self.categoria_movimentacao.nome if self.categoria_movimentacao else "Sem categoria"
    
    @property
    def categoria(self):
        """Propriedade de compatibilidade para código legacy que referencia o campo 'categoria'"""
        return self.categoria_movimentacao.codigo if self.categoria_movimentacao else 'outros'
    
    def pode_ser_usada_para(self, tipo_movimentacao):
        """Verifica se pode ser usada para um tipo específico de movimentação"""
        if self.tipo_movimentacao == 'ambos':
            return True
        
        if tipo_movimentacao == TIPO_MOVIMENTACAO_CONTA_CREDITO:
            return self.tipo_movimentacao == 'credito'
        elif tipo_movimentacao == TIPO_MOVIMENTACAO_CONTA_DEBITO:
            return self.tipo_movimentacao == 'debito'
        
        return False
    
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
        ).select_related('categoria_movimentacao').order_by(
            'categoria_movimentacao__natureza', 
            'categoria_movimentacao__ordem', 
            'nome'
        )
    
    @classmethod
    def obter_por_categoria(cls, conta, categoria_movimentacao):
        """Obtém descrições por categoria"""
        return cls.objects.filter(
            conta=conta,
            categoria_movimentacao=categoria_movimentacao
        ).order_by('nome')
    
    @classmethod
    def obter_creditos(cls, conta):
        """Obtém apenas descrições para crédito"""
        return cls.objects.filter(
            conta=conta,
            tipo_movimentacao__in=['credito', 'ambos']
        ).select_related('categoria_movimentacao').order_by(
            'categoria_movimentacao__natureza', 
            'categoria_movimentacao__ordem', 
            'nome'
        )
    
    @classmethod
    def obter_debitos(cls, conta):
        """Obtém apenas descrições para débito"""
        return cls.objects.filter(
            conta=conta,
            tipo_movimentacao__in=['debito', 'ambos']
        ).select_related('categoria_movimentacao').order_by(
            'categoria_movimentacao__natureza', 
            'categoria_movimentacao__ordem', 
            'nome'
        )
    
    @classmethod
    def obter_frequentes(cls, conta):
        """Obtém descrições marcadas como uso frequente"""
        return cls.objects.filter(
            conta=conta,
            ativa=True,
            uso_frequente=True
        ).select_related('categoria_movimentacao').order_by(
            'categoria_movimentacao__natureza', 
            'categoria_movimentacao__ordem', 
            'nome'
        )
    
    @classmethod
    def criar_descricoes_padrao(cls, conta, usuario=None):
        """Cria descrições padrão para uma nova conta"""
        # Primeiro, garantir que as categorias padrão existam
        categorias = CategoriaMovimentacao.criar_categorias_padrao(conta, usuario)
        
        # Mapeamento de códigos de categoria para objetos
        categorias_map = {}
        for categoria in CategoriaMovimentacao.objects.filter(conta=conta):
            categorias_map[categoria.codigo] = categoria
        
        descricoes_padrao = [
            # Receitas
            {
                'nome': 'Recebimento de Honorários Médicos',
                'categoria_codigo': 'receita_servicos',
                'tipo_movimentacao': 'credito',
                'descricao': 'Recebimento de honorários por serviços médicos prestados',
                'uso_frequente': True,
                'exige_documento': True,
            },
            {
                'nome': 'Recebimento de Consultas',
                'categoria_codigo': 'receita_servicos',
                'tipo_movimentacao': 'credito',
                'descricao': 'Recebimento por consultas médicas realizadas',
                'uso_frequente': True,
            },
            {
                'nome': 'Recebimento de Plantão',
                'categoria_codigo': 'receita_servicos',
                'tipo_movimentacao': 'credito',
                'descricao': 'Recebimento por plantões médicos realizados',
                'uso_frequente': True,
            },
            
            # Adiantamentos
            {
                'nome': 'Adiantamento de Lucros',
                'categoria_codigo': 'adiantamento_recebido',
                'tipo_movimentacao': 'credito',
                'descricao': 'Adiantamento de lucros da sociedade médica',
                'uso_frequente': True,
            },
            {
                'nome': 'Adiantamento para Despesas',
                'categoria_codigo': 'adiantamento_concedido',
                'tipo_movimentacao': 'debito',
                'descricao': 'Adiantamento concedido para cobrir despesas',
            },
            
            # Despesas
            {
                'nome': 'Despesas com Material Médico',
                'categoria_codigo': 'despesa_operacional',
                'tipo_movimentacao': 'debito',
                'descricao': 'Gastos com materiais médicos e insumos',
                'exige_documento': True,
            },
            {
                'nome': 'Despesas com Educação Médica',
                'categoria_codigo': 'despesa_operacional',
                'tipo_movimentacao': 'debito',
                'descricao': 'Gastos com cursos, congressos e capacitação',
                'exige_documento': True,
            },
            {
                'nome': 'Retirada para Uso Pessoal',
                'categoria_codigo': 'despesa_pessoal',
                'tipo_movimentacao': 'debito',
                'descricao': 'Retirada de valores para uso pessoal',
                'uso_frequente': True,
            },
            
            # Transferências
            {
                'nome': 'Transferência Bancária Recebida',
                'categoria_codigo': 'transferencia_recebida',
                'tipo_movimentacao': 'credito',
                'descricao': 'Transferência bancária recebida de terceiros',
                'exige_documento': True,
            },
            {
                'nome': 'Transferência Bancária Enviada',
                'categoria_codigo': 'transferencia_enviada',
                'tipo_movimentacao': 'debito',
                'descricao': 'Transferência bancária enviada para terceiros',
                'exige_documento': True,
            },
            
            # Ajustes
            {
                'nome': 'Ajuste Contábil a Crédito',
                'categoria_codigo': 'ajuste_credito',
                'tipo_movimentacao': 'credito',
                'descricao': 'Ajuste contábil positivo',
                'exige_aprovacao': True,
            },
            {
                'nome': 'Ajuste Contábil a Débito',
                'categoria_codigo': 'ajuste_debito',
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
                # Obter a categoria correspondente
                categoria_codigo = desc_data.pop('categoria_codigo')
                categoria_obj = categorias_map.get(categoria_codigo)
                
                if categoria_obj:
                    descricao = cls.objects.create(
                        conta=conta,
                        criada_por=usuario,
                        categoria_movimentacao=categoria_obj,
                        observacoes='Descrição criada automaticamente',
                        **desc_data
                    )
                    descricoes_criadas.append(descricao)
        
        return descricoes_criadas


class CategoriaMovimentacao(models.Model):
    """
    Categorias de movimentação financeira configuráveis por conta
    
    Este modelo permite que cada conta/cliente configure suas próprias
    categorias de movimentação conforme suas necessidades específicas,
    proporcionando flexibilidade total na organização financeira.
    """
    
    class Meta:
        db_table = 'categoria_movimentacao'
        unique_together = ('conta', 'codigo')
        verbose_name = "Categoria de Movimentação"
        verbose_name_plural = "Categorias de Movimentação"
        indexes = [
            models.Index(fields=['conta', 'ativa']),
            models.Index(fields=['tipo_movimentacao']),
            models.Index(fields=['codigo']),
        ]
        ordering = ['tipo_movimentacao', 'ordem', 'nome']

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='categorias_movimentacao', 
        null=False
    )
    
    # Identificação da categoria
    codigo = models.CharField(
        max_length=50,
        verbose_name="Código",
        help_text="Código único para identificar a categoria (ex: receita_servicos, despesa_operacional)"
    )
    
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome",
        help_text="Nome descritivo da categoria"
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição detalhada sobre quando usar esta categoria"
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
        help_text="Tipos de movimentação permitidos com esta categoria"
    )
    
    # Configurações visuais e organizacionais
    cor = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name="Cor",
        help_text="Cor em hexadecimal para representar esta categoria (#RRGGBB)"
    )
    
    icone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ícone",
        help_text="Nome do ícone para representar esta categoria (ex: fas fa-money-bill)"
    )
    
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem de Exibição",
        help_text="Ordem para exibição nas listas (menor número aparece primeiro)"
    )
    
    # Configurações contábeis/fiscais
    NATUREZAS_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
        ('transferencia', 'Transferência'),
        ('ajuste', 'Ajuste'),
        ('aplicacao', 'Aplicação Financeira'),
        ('emprestimo', 'Empréstimo'),
        ('outros', 'Outros'),
    ]
    
    natureza = models.CharField(
        max_length=20,
        choices=NATUREZAS_CHOICES,
        default='outros',
        verbose_name="Natureza Contábil",
        help_text="Natureza contábil da categoria para classificação"
    )
    
    codigo_contabil = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Código Contábil",
        help_text="Código contábil padrão para esta categoria (plano de contas)"
    )
    
    # Configurações tributárias
    possui_retencao_ir = models.BooleanField(
        default=False,
        verbose_name="Possui Retenção IR",
        help_text="Se movimentações desta categoria podem ter retenção de IR"
    )
    
    percentual_retencao_ir_padrao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="% Retenção IR Padrão",
        help_text="Percentual padrão de retenção de IR para esta categoria"
    )
    
    # Configurações de controle
    exige_documento = models.BooleanField(
        default=False,
        verbose_name="Exige Documento",
        help_text="Se movimentações desta categoria exigem número de documento"
    )
    
    exige_aprovacao = models.BooleanField(
        default=False,
        verbose_name="Exige Aprovação",
        help_text="Se movimentações desta categoria exigem aprovação adicional"
    )
    
    limite_valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Limite de Valor",
        help_text="Valor limite para movimentações desta categoria (opcional)"
    )
    
    # Status e controle
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Se esta categoria está disponível para uso"
    )
    
    categoria_sistema = models.BooleanField(
        default=False,
        verbose_name="Categoria do Sistema",
        help_text="Indica se é uma categoria criada automaticamente pelo sistema"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categorias_movimentacao_criadas',
        verbose_name="Criada Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o uso desta categoria"
    )

    def clean(self):
        """Validações personalizadas"""
        # Validar código único por conta
        if self.codigo:
            qs = CategoriaMovimentacao.objects.filter(
                conta=self.conta,
                codigo=self.codigo
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                raise ValidationError({
                    'codigo': 'Já existe uma categoria com este código nesta conta'
                })
        
        # Validar cor hexadecimal
        if self.cor and not self.cor.startswith('#'):
            raise ValidationError({
                'cor': 'Cor deve estar no formato hexadecimal (#RRGGBB)'
            })
        
        # Validar percentual de retenção
        if self.percentual_retencao_ir_padrao < 0 or self.percentual_retencao_ir_padrao > 100:
            raise ValidationError({
                'percentual_retencao_ir_padrao': 'Percentual deve estar entre 0% e 100%'
            })
        
        # Se não possui retenção, o percentual deve ser zero
        if not self.possui_retencao_ir and self.percentual_retencao_ir_padrao > 0:
            raise ValidationError({
                'percentual_retencao_ir_padrao': 'Percentual deve ser zero se não possui retenção'
            })
        
        # Validar limite de valor
        if self.limite_valor is not None and self.limite_valor <= 0:
            raise ValidationError({
                'limite_valor': 'Limite de valor deve ser positivo'
            })

    def save(self, *args, **kwargs):
        # Gerar código automaticamente se não foi fornecido
        if not self.codigo:
            import re
            # Converter nome para código (remover acentos, espaços, etc.)
            codigo_base = re.sub(r'[^a-zA-Z0-9]', '_', self.nome.lower())
            codigo_base = re.sub(r'_+', '_', codigo_base).strip('_')
            
            # Garantir unicidade
            contador = 1
            codigo_candidato = codigo_base
            while CategoriaMovimentacao.objects.filter(
                conta=self.conta,
                codigo=codigo_candidato
            ).exclude(pk=self.pk).exists():
                codigo_candidato = f"{codigo_base}_{contador}"
                contador += 1
            
            self.codigo = codigo_candidato
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome}"
    
    @property
    def nome_completo(self):
        """Retorna nome completo com natureza"""
        natureza_display = self.get_natureza_display()
        return f"[{natureza_display}] {self.nome}"
    
    @property
    def cor_css(self):
        """Retorna a cor formatada para CSS"""
        return self.cor if self.cor.startswith('#') else f"#{self.cor}"
    
    def pode_ser_usada_para(self, tipo_movimentacao):
        """Verifica se pode ser usada para um tipo específico de movimentação"""
        if self.tipo_movimentacao == 'ambos':
            return True
        
        if tipo_movimentacao == TIPO_MOVIMENTACAO_CONTA_CREDITO:
            return self.tipo_movimentacao == 'credito'
        elif tipo_movimentacao == TIPO_MOVIMENTACAO_CONTA_DEBITO:
            return self.tipo_movimentacao == 'debito'
        
        return False
    
    def validar_valor(self, valor):
        """Valida se um valor é aceito por esta categoria"""
        if not self.ativa:
            raise ValidationError("Esta categoria não está ativa")
        
        if self.limite_valor and valor > self.limite_valor:
            raise ValidationError(f"Valor excede o limite de R$ {self.limite_valor} para a categoria '{self.nome}'")
    
    def calcular_retencao_ir(self, valor_base):
        """Calcula o valor da retenção de IR"""
        if not self.possui_retencao_ir or self.percentual_retencao_ir_padrao <= 0:
            return 0
        
        return valor_base * (self.percentual_retencao_ir_padrao / 100)
    
    @classmethod
    def obter_ativas(cls, conta):
        """Obtém todas as categorias ativas para uma conta"""
        return cls.objects.filter(
            conta=conta,
            ativa=True
        ).order_by('tipo_movimentacao', 'ordem', 'nome')
    
    @classmethod
    def obter_por_natureza(cls, conta, natureza):
        """Obtém categorias por natureza"""
        return cls.objects.filter(
            conta=conta,
            natureza=natureza,
            ativa=True
        ).order_by('ordem', 'nome')
    
    @classmethod
    def obter_creditos(cls, conta):
        """Obtém apenas categorias para crédito"""
        return cls.objects.filter(
            conta=conta,
            tipo_movimentacao__in=['credito', 'ambos'],
            ativa=True
        ).order_by('ordem', 'nome')
    
    @classmethod
    def obter_debitos(cls, conta):
        """Obtém apenas categorias para débito"""
        return cls.objects.filter(
            conta=conta,
            tipo_movimentacao__in=['debito', 'ambos'],
            ativa=True
        ).order_by('ordem', 'nome')
    
    @classmethod
    def criar_categorias_padrao(cls, conta, usuario=None):
        """Cria categorias padrão para uma nova conta"""
        categorias_padrao = [
            # === RECEITAS ===
            {
                'codigo': 'receita_servicos',
                'nome': 'Receita de Serviços',
                'natureza': 'receita',
                'tipo_movimentacao': 'credito',
                'cor': '#28a745',
                'icone': 'fas fa-user-md',
                'ordem': 10,
                'descricao': 'Receitas provenientes de serviços médicos prestados',
                'categoria_sistema': True,
            },
            {
                'codigo': 'receita_outros',
                'nome': 'Outras Receitas',
                'natureza': 'receita',
                'tipo_movimentacao': 'credito',
                'cor': '#20c997',
                'icone': 'fas fa-plus-circle',
                'ordem': 20,
                'descricao': 'Outras receitas não relacionadas aos serviços principais',
                'categoria_sistema': True,
            },
            
            # === ADIANTAMENTOS RECEBIDOS ===
            {
                'codigo': 'adiantamento_recebido',
                'nome': 'Adiantamento Recebido',
                'natureza': 'receita',
                'tipo_movimentacao': 'credito',
                'cor': '#17a2b8',
                'icone': 'fas fa-hand-holding-usd',
                'ordem': 30,
                'descricao': 'Adiantamentos de lucros ou pagamentos recebidos',
                'categoria_sistema': True,
            },
            
            # === EMPRÉSTIMOS ===
            {
                'codigo': 'emprestimo_recebido',
                'nome': 'Empréstimo Recebido',
                'natureza': 'emprestimo',
                'tipo_movimentacao': 'credito',
                'cor': '#6f42c1',
                'icone': 'fas fa-handshake',
                'ordem': 40,
                'descricao': 'Empréstimos recebidos de terceiros',
                'exige_documento': True,
                'categoria_sistema': True,
            },
            {
                'codigo': 'emprestimo_concedido',
                'nome': 'Empréstimo Concedido',
                'natureza': 'emprestimo',
                'tipo_movimentacao': 'debito',
                'cor': '#6f42c1',
                'icone': 'fas fa-hand-holding-heart',
                'ordem': 110,
                'descricao': 'Empréstimos concedidos a terceiros',
                'exige_documento': True,
                'categoria_sistema': True,
            },
            
            # === DESPESAS ===
            {
                'codigo': 'despesa_operacional',
                'nome': 'Despesa Operacional',
                'natureza': 'despesa',
                'tipo_movimentacao': 'debito',
                'cor': '#dc3545',
                'icone': 'fas fa-file-invoice-dollar',
                'ordem': 50,
                'descricao': 'Despesas relacionadas à operação médica',
                'exige_documento': True,
                'categoria_sistema': True,
            },
            {
                'codigo': 'despesa_pessoal',
                'nome': 'Despesa Pessoal',
                'natureza': 'despesa',
                'tipo_movimentacao': 'debito',
                'cor': '#fd7e14',
                'icone': 'fas fa-user',
                'ordem': 60,
                'descricao': 'Retiradas e despesas pessoais do médico',
                'categoria_sistema': True,
            },
            
            # === ADIANTAMENTOS CONCEDIDOS ===
            {
                'codigo': 'adiantamento_concedido',
                'nome': 'Adiantamento Concedido',
                'natureza': 'despesa',
                'tipo_movimentacao': 'debito',
                'cor': '#fd7e14',
                'icone': 'fas fa-donate',
                'ordem': 70,
                'descricao': 'Adiantamentos concedidos a funcionários ou parceiros',
                'categoria_sistema': True,
            },
            
            # === TRANSFERÊNCIAS ===
            {
                'codigo': 'transferencia_recebida',
                'nome': 'Transferência Recebida',
                'natureza': 'transferencia',
                'tipo_movimentacao': 'credito',
                'cor': '#007bff',
                'icone': 'fas fa-arrow-circle-down',
                'ordem': 80,
                'descricao': 'Transferências bancárias recebidas',
                'exige_documento': True,
                'categoria_sistema': True,
            },
            {
                'codigo': 'transferencia_enviada',
                'nome': 'Transferência Enviada',
                'natureza': 'transferencia',
                'tipo_movimentacao': 'debito',
                'cor': '#007bff',
                'icone': 'fas fa-arrow-circle-up',
                'ordem': 90,
                'descricao': 'Transferências bancárias enviadas',
                'exige_documento': True,
                'categoria_sistema': True,
            },
            
            # === AJUSTES ===
            {
                'codigo': 'ajuste_credito',
                'nome': 'Ajuste a Crédito',
                'natureza': 'ajuste',
                'tipo_movimentacao': 'credito',
                'cor': '#28a745',
                'icone': 'fas fa-plus',
                'ordem': 100,
                'descricao': 'Ajustes contábiles positivos',
                'exige_aprovacao': True,
                'categoria_sistema': True,
            },
            {
                'codigo': 'ajuste_debito',
                'nome': 'Ajuste a Débito',
                'natureza': 'ajuste',
                'tipo_movimentacao': 'debito',
                'cor': '#dc3545',
                'icone': 'fas fa-minus',
                'ordem': 120,
                'descricao': 'Ajustes contábiles negativos',
                'exige_aprovacao': True,
                'categoria_sistema': True,
            },
            
            # === APLICAÇÕES FINANCEIRAS ===
            {
                'codigo': 'aplicacao_financeira',
                'nome': 'Aplicação Financeira',
                'natureza': 'aplicacao',
                'tipo_movimentacao': 'debito',
                'cor': '#6610f2',
                'icone': 'fas fa-chart-line',
                'ordem': 130,
                'descricao': 'Aplicações financeiras realizadas',
                'exige_documento': True,
                'categoria_sistema': True,
            },
            {
                'codigo': 'resgate_aplicacao',
                'nome': 'Resgate de Aplicação',
                'natureza': 'aplicacao',
                'tipo_movimentacao': 'credito',
                'cor': '#6610f2',
                'icone': 'fas fa-piggy-bank',
                'ordem': 35,
                'descricao': 'Resgates de aplicações financeiras',
                'exige_documento': True,
                'categoria_sistema': True,
            },
        ]
        
        # Criar as categorias
        categorias_criadas = []
        for categoria_data in categorias_padrao:
            categoria_data['conta'] = conta
            categoria_data['criada_por'] = usuario
            
            # Verificar se já existe
            if not cls.objects.filter(conta=conta, codigo=categoria_data['codigo']).exists():
                categoria = cls.objects.create(**categoria_data)
                categorias_criadas.append(categoria)
        
        return categorias_criadas


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
    def categoria(self):
        """Retorna a categoria da movimentação"""
        return self.desc_movimentacao.categoria_movimentacao if self.desc_movimentacao else None
    
    @property
    def natureza(self):
        """Retorna a natureza contábil da movimentação"""
        return self.categoria.natureza if self.categoria else 'outros'
    
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
        
        # Por categoria
        from django.db.models import Q
        categorias = lancamentos.values(
            'desc_movimentacao__categoria_movimentacao__nome'
        ).annotate(
            total=models.Sum('valor'),
            quantidade=models.Count('id')
        ).filter(total__gt=0)
        
        for categoria in categorias:
            nome_categoria = categoria['desc_movimentacao__categoria_movimentacao__nome'] or 'Sem categoria'
            consolidado['por_categoria'][nome_categoria] = {
                'total': categoria['total'],
                'quantidade': categoria['quantidade']
            }
        
        return consolidado



