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


class Desc_movimentacao_financeiro(models.Model):
    """
    Descrições padronizadas para movimentações financeiras manuais
    
    Este modelo armazena as descrições pré-definidas que devem ser usadas
    nos lançamentos manuais do fluxo de caixa, garantindo padronização
    e facilitando relatórios e auditoria.
    """
    
    class Meta:
        db_table = 'desc_movimentacao_financeiro'
        unique_together = ('conta', 'descricao')
        verbose_name = "Descrição de Movimentação Financeira"
        verbose_name_plural = "Descrições de Movimentações Financeiras"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='desc_movimentacao_financeiro', 
        null=False
    )
    
    # Categorias para organização das descrições
    CATEGORIAS_CHOICES = [
        # Créditos
        ('adiantamento', 'Adiantamento'),
        ('pagamento', 'Pagamento'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferência'),
        ('financeiro', 'Operação Financeira'),
        ('saldo', 'Saldo/Transporte'),
        ('outros', 'Outros'),
        
        # Débitos específicos
        ('despesa', 'Despesa'),
        ('taxa', 'Taxa/Encargo'),
    ]
    
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS_CHOICES,
        default='outros',
        verbose_name="Categoria",
        help_text="Categoria da movimentação para organização e relatórios"
    )
    
    descricao = models.CharField(
        max_length=255, 
        null=False, 
        verbose_name="Descrição",
        help_text="Descrição padronizada para o tipo de movimentação"
    )
    
    # Controle de tipo padrão (crédito/débito)
    tipo_padrao = models.PositiveSmallIntegerField(
        choices=[
            (TIPO_MOVIMENTACAO_CONTA_CREDITO, 'Crédito'),
            (TIPO_MOVIMENTACAO_CONTA_DEBITO, 'Débito'),
        ],
        null=True,
        blank=True,
        verbose_name="Tipo Padrão",
        help_text="Tipo padrão de movimentação (pode ser alterado no lançamento)"
    )
    
    # Status e controle
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Se esta descrição está disponível para uso"
    )
    
    exige_documento = models.BooleanField(
        default=False,
        verbose_name="Exige Documento",
        help_text="Se lançamentos com esta descrição exigem número de documento"
    )
    
    exige_aprovacao = models.BooleanField(
        default=False,
        verbose_name="Exige Aprovação",
        help_text="Se lançamentos com esta descrição exigem aprovação adicional"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criada Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o uso desta descrição"
    )

    def __str__(self):
        return f"{self.descricao}"
    
    @property
    def categoria_formatada(self):
        """Retorna a categoria formatada"""
        return self.get_categoria_display()


class Financeiro(models.Model):
    """
    Movimentações financeiras manuais do fluxo de caixa individual
    
    Este modelo registra todas as movimentações manuais do fluxo de caixa
    individual de cada médico/sócio, garantindo total auditabilidade
    e controle manual sobre todos os lançamentos.
    """
    
    class Meta:
        db_table = 'financeiro'
        indexes = [
            models.Index(fields=['conta', 'data', 'socio']),
            models.Index(fields=['tipo', 'status']),
            models.Index(fields=['data_processamento']),
        ]
        verbose_name = "Movimentação Financeira"
        verbose_name_plural = "Movimentações Financeiras"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='financeiros', 
        null=False
    )
    
    class Tipo_t(models.IntegerChoices):
        CREDITO = TIPO_MOVIMENTACAO_CONTA_CREDITO, "CREDITO"
        DEBITO = TIPO_MOVIMENTACAO_CONTA_DEBITO, "DEBITO"
    
    # Dados principais da movimentação
    data = models.DateField(
        null=False, 
        verbose_name="Data da Movimentação"
    )
    
    # Relacionamentos
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        verbose_name="Empresa/Associação"
    )
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        verbose_name="Médico/Sócio"
    )
    notafiscal = models.ForeignKey(
        'fiscal.NotaFiscal', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Nota Fiscal Relacionada",
        help_text="Nota fiscal relacionada (quando aplicável)"
    )
    
    # Tipo e descrição
    tipo = models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.CREDITO,
        verbose_name="Tipo de Movimentação"
    )
    descricao = models.ForeignKey(
        Desc_movimentacao_financeiro, 
        on_delete=models.PROTECT,
        verbose_name="Descrição Padronizada"
    )
    
    # Valores e documentos
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="Valor"
    )
    numero_documento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Número do Documento",
        help_text="Número do documento comprobatório"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações adicionais sobre a movimentação"
    )
    
    # Controle de processamento
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('pendente', 'Pendente de Aprovação'),
        ('aprovado', 'Aprovado'),
        ('processado', 'Processado'),
        ('conciliado', 'Conciliado'),
        ('transferido', 'Transferido'),
        ('cancelado', 'Cancelado'),
        ('erro', 'Erro no Processamento'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )
    
    # Controle automático vs manual
    operacao_auto = models.BooleanField(
        default=False,
        verbose_name="Operação Automática",
        help_text="Indica se foi criada automaticamente pelo sistema"
    )
    
    # Auditoria detalhada
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    lancado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lancamentos_financeiros',
        verbose_name="Lançado Por"
    )
    
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aprovacoes_financeiras',
        verbose_name="Aprovado Por"
    )
    
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Aprovação"
    )
    
    processado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processamentos_financeiros',
        verbose_name="Processado Por"
    )
    
    data_processamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Processamento"
    )
    
    # Dados de auditoria adicional
    ip_origem = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP de Origem",
        help_text="IP do usuário que criou o lançamento"
    )
    
    dados_auditoria = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados de Auditoria",
        help_text="Dados adicionais para auditoria em formato JSON"
    )

    def clean(self):
        """Validações personalizadas"""
        # Validar valor positivo
        if self.valor <= 0:
            raise ValidationError("O valor deve ser positivo")
        
        # Validar se empresa e sócio pertencem à mesma conta
        if self.empresa and self.socio:
            if self.empresa.conta != self.socio.conta:
                raise ValidationError("Empresa e sócio devem pertencer à mesma conta")
        
        # Validar se descrição exige documento
        if self.descricao and self.descricao.exige_documento:
            if not self.numero_documento:
                raise ValidationError(
                    f"A descrição '{self.descricao.descricao}' exige número de documento"
                )
        
        # Validar se descrição exige aprovação para valores altos
        if self.descricao and self.descricao.exige_aprovacao:
            # Obter configuração da conta para verificar limite
            from .auditoria import ConfiguracaoSistemaManual
            config = ConfiguracaoSistemaManual.obter_configuracao(self.conta)
            if config.valor_requer_aprovacao_gerencial(self.valor):
                if self.status not in ['pendente', 'aprovado'] and not self.aprovado_por:
                    raise ValidationError(
                        "Lançamentos de valor alto com esta descrição exigem aprovação"
                    )

    def save(self, *args, **kwargs):
        # Garantir consistência da conta
        if self.empresa:
            self.conta = self.empresa.conta
        
        # Definir tipo padrão baseado na descrição se ainda não foi definido
        if self.descricao and self.descricao.tipo_padrao and not self.pk:
            self.tipo = self.descricao.tipo_padrao
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        sinal = "+" if self.tipo == self.Tipo_t.CREDITO else "-"
        return f"{self.data} {sinal}R$ {self.valor} - {self.socio.pessoa.name}"
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado com sinal"""
        sinal = "+" if self.tipo == self.Tipo_t.CREDITO else "-"
        return f"{sinal}R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def categoria_descricao(self):
        """Retorna a categoria da descrição"""
        return self.descricao.categoria if self.descricao else 'outros'
    
    @property
    def pode_ser_editado(self):
        """Verifica se o lançamento ainda pode ser editado"""
        return self.status in ['rascunho', 'pendente'] and not self.operacao_auto
    
    @property
    def pode_ser_cancelado(self):
        """Verifica se o lançamento pode ser cancelado"""
        return self.status not in ['cancelado', 'transferido'] and not self.operacao_auto
    
    def aprovar(self, usuario):
        """Aprova o lançamento"""
        if self.status != 'pendente':
            raise ValidationError("Apenas lançamentos pendentes podem ser aprovados")
        
        self.status = 'aprovado'
        self.aprovado_por = usuario
        self.data_aprovacao = timezone.now()
        self.save()
    
    def processar(self, usuario):
        """Processa o lançamento"""
        if self.status not in ['aprovado', 'rascunho']:
            raise ValidationError("Lançamento deve estar aprovado ou em rascunho para ser processado")
        
        self.status = 'processado'
        self.processado_por = usuario
        self.data_processamento = timezone.now()
        self.save()
    
    def cancelar(self, usuario, motivo=""):
        """Cancela o lançamento"""
        if not self.pode_ser_cancelado:
            raise ValidationError("Este lançamento não pode ser cancelado")
        
        self.status = 'cancelado'
        self.processado_por = usuario
        self.data_processamento = timezone.now()
        if motivo:
            self.observacoes = f"{self.observacoes}\n\nCANCELADO: {motivo}" if self.observacoes else f"CANCELADO: {motivo}"
        self.save()


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
            categoria = mov.categoria_descricao
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
    
    def fechar_mes(self, usuario):
        """Fecha o mês para novas movimentações"""
        if self.fechado:
            raise ValidationError("Este mês já está fechado")
        
        # Recalcular antes de fechar
        self.calcular_saldo_completo()
        
        self.fechado = True
        self.data_fechamento = timezone.now()
        self.fechado_por = usuario
        self.save()
    
    def reabrir_mes(self, usuario):
        """Reabre o mês para novas movimentações"""
        if not self.fechado:
            raise ValidationError("Este mês não está fechado")
        
        self.fechado = False
        self.data_fechamento = None
        self.fechado_por = None
        self.observacoes = f"{self.observacoes}\n\nMês reaberto por {usuario.username} em {timezone.now()}" if self.observacoes else f"Mês reaberto por {usuario.username} em {timezone.now()}"
        self.save()
