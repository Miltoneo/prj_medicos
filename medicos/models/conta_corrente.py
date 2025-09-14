from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Empresa, Socio
from .financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento

"""
Modelos relacionados ao controle de contas correntes bancárias

Este módulo contém os modelos para gerenciamento de contas correntes
e lançamentos bancários da aplicação de médicos, incluindo conciliação
bancária e controle de fluxo de caixa por conta.
"""


class ContaCorrente(models.Model):
    """
    Modelo para controle de contas correntes bancárias

    Este modelo permite controlar múltiplas contas correntes de uma empresa,
    com lançamentos individuais para cada conta que são consolidados
    dinamicamente conforme necessário para relatórios.
    """
    
    class Meta:
        db_table = 'conta_corrente'
        verbose_name = "Conta Corrente"
        verbose_name_plural = "Contas Correntes"
        unique_together = ('empresa', 'banco', 'agencia', 'numero_conta')
        indexes = [
            models.Index(fields=['empresa', 'ativa']),
            models.Index(fields=['banco', 'agencia']),
        ]
        ordering = ['banco', 'agencia', 'numero_conta']

    # Relacionamentos principais
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='contas_correntes',
        verbose_name="Empresa",
        help_text="Empresa proprietária desta conta corrente"
    )

    # Dados bancários
    banco = models.CharField(
        max_length=10,
        verbose_name="Código do Banco",
        help_text="Código do banco (ex: 001, 033, 104, 237)"
    )
    
    nome_banco = models.CharField(
        max_length=100,
        verbose_name="Nome do Banco",
        help_text="Nome do banco (ex: Banco do Brasil, Santander, Caixa)"
    )
    
    agencia = models.CharField(
        max_length=10,
        verbose_name="Agência",
        help_text="Número da agência (sem dígito verificador)"
    )
    
    digito_agencia = models.CharField(
        max_length=2,
        blank=True,
        verbose_name="Dígito da Agência",
        help_text="Dígito verificador da agência"
    )
    
    numero_conta = models.CharField(
        max_length=20,
        verbose_name="Número da Conta",
        help_text="Número da conta corrente (sem dígito verificador)"
    )
    
    digito_conta = models.CharField(
        max_length=2,
        verbose_name="Dígito da Conta",
        help_text="Dígito verificador da conta"
    )
    
    # Dados adicionais
    descricao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição ou apelido da conta (ex: Conta Principal, Conta Reserva)"
    )
    
    saldo_inicial = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Inicial",
        help_text="Saldo inicial da conta na data de cadastro"
    )
    
    data_abertura = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Abertura",
        help_text="Data de abertura da conta no banco"
    )
    
    # Status e controle
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Se esta conta está ativa para uso"
    )
    
    conta_principal = models.BooleanField(
        default=False,
        verbose_name="Conta Principal",
        help_text="Se esta é a conta principal da empresa"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_correntes_criadas',
        verbose_name="Criado Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre esta conta corrente"
    )

    def clean(self):
        """Validações personalizadas"""
        super().clean()
        
        # Validar que apenas uma conta pode ser principal por empresa
        if self.conta_principal:
            qs = ContaCorrente.objects.filter(
                empresa=self.empresa,
                conta_principal=True,
                ativa=True
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'conta_principal': 'Já existe uma conta principal ativa para esta empresa'
                })
        
        # Validar formato do código do banco (numérico)
        if self.banco and not self.banco.isdigit():
            raise ValidationError({
                'banco': 'Código do banco deve conter apenas números'
            })
        
        # Validar agência (numérico)
        if self.agencia and not self.agencia.isdigit():
            raise ValidationError({
                'agencia': 'Agência deve conter apenas números'
            })

    def save(self, *args, **kwargs):
        # Se esta conta está sendo marcada como principal, desmarcar outras
        if self.conta_principal and self.ativa:
            ContaCorrente.objects.filter(
                empresa=self.empresa,
                conta_principal=True,
                ativa=True
            ).exclude(pk=self.pk).update(conta_principal=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        conta_formatada = f"{self.banco} - Ag: {self.agencia}"
        if self.digito_agencia:
            conta_formatada += f"-{self.digito_agencia}"
        conta_formatada += f" - Cc: {self.numero_conta}"
        if self.digito_conta:
            conta_formatada += f"-{self.digito_conta}"
        
        if self.descricao:
            conta_formatada += f" ({self.descricao})"
        
        return conta_formatada
    
    @property
    def agencia_completa(self):
        """Retorna agência com dígito verificador"""
        if self.digito_agencia:
            return f"{self.agencia}-{self.digito_agencia}"
        return self.agencia
    
    @property
    def conta_completa(self):
        """Retorna número da conta com dígito verificador"""
        if self.digito_conta:
            return f"{self.numero_conta}-{self.digito_conta}"
        return self.numero_conta
    
    @property
    def identificacao_completa(self):
        """Retorna identificação completa da conta"""
        return f"{self.nome_banco} - Ag: {self.agencia_completa} - Cc: {self.conta_completa}"
    
    def calcular_saldo_atual(self, data_limite=None):
        """
        Calcula o saldo atual da conta considerando o saldo inicial
        
        Args:
            data_limite: Data limite para cálculo (default: hoje)
            
        Returns:
            decimal: Saldo atual da conta (apenas saldo inicial, sem movimentações)
        """
        if data_limite is None:
            data_limite = timezone.now().date()
        
        # Como não há mais relacionamento com movimentações, retorna apenas saldo inicial
        return self.saldo_inicial
    
    def obter_extrato_periodo(self, data_inicio, data_fim):
        """
        Obtém extrato da conta em um período específico
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            
        Returns:
            dict: Extrato simplificado (sem movimentações associadas)
        """
        # Saldo inicial do período
        saldo_inicial_periodo = self.calcular_saldo_atual(data_inicio - timezone.timedelta(days=1))
        
        return {
            'conta': self,
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            },
            'saldo_inicial': saldo_inicial_periodo,
            'lancamentos': [],
            'total_debitos_bancarios': 0,
            'total_creditos_bancarios': 0,
            'saldo_final': saldo_inicial_periodo,
            'quantidade_lancamentos': 0
        }
    
    @classmethod
    def obter_conta_principal(cls, empresa):
        """Obtém a conta principal de uma empresa"""
        try:
            return cls.objects.get(empresa=empresa, conta_principal=True, ativa=True)
        except cls.DoesNotExist:
            # Se não há conta principal, retorna a primeira conta ativa
            return cls.objects.filter(empresa=empresa, ativa=True).first()
    
    @classmethod
    def criar_conta_padrao(cls, empresa, usuario=None):
        """Cria uma conta padrão para uma nova empresa"""
        conta = cls.objects.create(
            empresa=empresa,
            banco='000',
            nome_banco='Banco não definido',
            agencia='0000',
            numero_conta='000000',
            descricao='Conta padrão (configurar dados bancários)',
            conta_principal=True,
            created_by=usuario,
            observacoes='Conta criada automaticamente. Configurar dados bancários reais.'
        )
        return conta


class MovimentacaoContaCorrente(models.Model):
    """
    Modelo para lançamentos bancários em contas correntes
    
    Este modelo registra todos os lançamentos bancários (débitos e créditos) 
    que ocorrem nas contas correntes da empresa, permitindo controle detalhado
    do fluxo de caixa bancário e conciliação com extratos bancários.
    
    JARGÃO BANCÁRIO CORRETO APLICADO:
    - Débito Bancário = Entrada de dinheiro na conta (valor positivo)
    - Crédito Bancário = Saída de dinheiro da conta (valor negativo)
    - Lançamento = Cada operação registrada no extrato bancário
    - Conciliação = Processo de conferência entre registros internos e extrato bancário
    - Histórico Complementar = Informações adicionais sobre o lançamento
    - Instrumento Bancário = Meio utilizado (DOC, TED, PIX, Cheque, etc.)
    
    Nota: A terminologia segue o padrão bancário onde "débito" na conta significa 
    entrada de recursos e "crédito" significa saída de recursos.
    """
    
    class Meta:
        db_table = 'movimentacao_conta_corrente'
        verbose_name = "Lançamento Bancário"
        verbose_name_plural = "Lançamentos Bancários"
        indexes = [
            models.Index(fields=['data_movimentacao']),
            models.Index(fields=['descricao_movimentacao']),
            models.Index(fields=['instrumento_bancario']),
        ]
        ordering = ['-data_movimentacao', '-created_at']

    # Relacionamentos principais
    
    descricao_movimentacao = models.ForeignKey(
        DescricaoMovimentacaoFinanceira,
        on_delete=models.PROTECT,
        related_name='lancamentos_bancarios',
        verbose_name="Descrição do Lançamento",
        help_text="Descrição padronizada deste lançamento bancário",
        default=1  # Valor padrão temporário para migração
    )
    
    instrumento_bancario = models.ForeignKey(
        MeioPagamento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lancamentos_bancarios',
        verbose_name="Instrumento Bancário",
        help_text="Instrumento utilizado no lançamento (DOC, TED, PIX, Cheque, etc.)"
    )
    
    # Relacionamentos opcionais
    nota_fiscal = models.ForeignKey(
        'medicos.NotaFiscal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_bancarios',
        verbose_name="Nota Fiscal",
        help_text="Nota fiscal relacionada a este lançamento, se houver"
    )
    
    socio = models.ForeignKey(
        Socio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_bancarios',
        verbose_name="Médico/Sócio",
        help_text="Médico ou sócio relacionado a este lançamento, se houver"
    )

    # Dados do lançamento bancário
    data_movimentacao = models.DateField(
        verbose_name="Data do Lançamento",
        help_text="Data em que o lançamento foi realizado no banco"
    )
    
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Valor",
        help_text="Valor do lançamento em reais. Positivo para débito bancário (entrada na conta), negativo para crédito bancário (saída da conta)"
    )
    
    numero_documento_bancario = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Número do Documento Bancário",
        help_text="Número do cheque, DOC, TED, PIX, comprovante de transferência, etc."
    )
    
    historico_complementar = models.TextField(
        blank=True,
        verbose_name="Histórico Complementar",
        help_text="Informações complementares sobre o lançamento bancário"
    )
    
    # Dados de conciliação bancária
    conciliado = models.BooleanField(
        default=False,
        verbose_name="Conciliado",
        help_text="Se esta movimentação foi conciliada com o extrato bancário"
    )
    
    data_conciliacao = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data da Conciliação",
        help_text="Data em que foi realizada a conciliação bancária"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_bancarios_criados',
        verbose_name="Criado Por"
    )

    def clean(self):
        """Validações personalizadas"""
        super().clean()
        
        # Validar que valor não pode ser zero
        if self.valor == 0:
            raise ValidationError({
                'valor': 'Valor do lançamento bancário não pode ser zero'
            })
        
        # Validar que data de lançamento não pode ser futura
        hoje = timezone.now().date()
        if self.data_movimentacao and self.data_movimentacao > hoje:
            raise ValidationError({
                'data_movimentacao': 'A data do lançamento não pode ser futura'
            })
        
        # Validar data de conciliação
        if self.data_conciliacao and not self.conciliado:
            raise ValidationError({
                'data_conciliacao': 'Data de conciliação só pode ser preenchida se lançamento estiver conciliado'
            })
        
        if self.conciliado and not self.data_conciliacao:
            self.data_conciliacao = timezone.now().date()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        tipo = "Débito Bancário" if self.valor > 0 else "Crédito Bancário"
        return f"{self.data_movimentacao.strftime('%d/%m/%Y')} - {tipo}: R$ {abs(self.valor):,.2f}"
    
    @property
    def eh_debito_bancario(self):
        """Verifica se é um débito bancário (entrada na conta)"""
        return self.valor > 0
    
    @property
    def eh_credito_bancario(self):
        """Verifica se é um crédito bancário (saída da conta)"""
        return self.valor < 0
    
    @property
    def valor_absoluto(self):
        """Retorna o valor absoluto da movimentação"""
        return abs(self.valor)
    
    @property
    def tipo_lancamento(self):
        """Retorna o tipo do lançamento como string"""
        return "Débito Bancário" if self.eh_debito_bancario else "Crédito Bancário"
    
    @property
    def mes_referencia(self):
        """Retorna o primeiro dia do mês do lançamento"""
        return self.data_movimentacao.replace(day=1)
    
    def pode_ser_editado(self):
        """Verifica se o lançamento pode ser editado"""
        # Não permite edição se já foi conciliado
        return not self.conciliado
    
    def pode_ser_cancelado(self):
        """Verifica se o lançamento pode ser cancelado"""
        # Não permite cancelamento se já foi conciliado
        return not self.conciliado
    
    def conciliar(self, data_conciliacao=None, usuario=None):
        """Marca o lançamento como conciliado"""
        if self.conciliado:
            raise ValidationError("Lançamento já está conciliado")
        
        self.conciliado = True
        self.data_conciliacao = data_conciliacao or timezone.now().date()
        self.save()
    
    def desconciliar(self, usuario=None):
        """Remove a conciliação do lançamento"""
        if not self.conciliado:
            raise ValidationError("Lançamento não está conciliado")
        
        self.conciliado = False
        self.data_conciliacao = None
        self.save()
    
    @classmethod
    def obter_lancamentos_periodo(cls, data_inicio, data_fim):
        """Obtém lançamentos bancários em um período específico"""
        return cls.objects.filter(
            data_movimentacao__range=[data_inicio, data_fim]
        ).select_related(
            'descricao_movimentacao',
            'instrumento_bancario',
            'socio__pessoa'
        )
    
    @classmethod
    def obter_saldo_periodo(cls, data_inicio, data_fim):
        """Calcula o saldo de um período específico"""
        lancamentos = cls.obter_lancamentos_periodo(data_inicio, data_fim)
        
        total_debitos_bancarios = lancamentos.filter(valor__gt=0).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        total_creditos_bancarios = lancamentos.filter(valor__lt=0).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        return {
            'total_debitos_bancarios': total_debitos_bancarios,  # Entradas
            'total_creditos_bancarios': abs(total_creditos_bancarios),  # Saídas
            'saldo_liquido': total_debitos_bancarios + total_creditos_bancarios,  # total_creditos_bancarios já é negativo
            'quantidade_lancamentos': lancamentos.count(),
            'conciliados': lancamentos.filter(conciliado=True).count(),
            'nao_conciliados': lancamentos.filter(conciliado=False).count()
        }
    
    @classmethod
    def obter_consolidado_periodo(cls, mes_referencia):
        """Obtém o consolidado de todos os lançamentos em um mês"""
        data_inicio = mes_referencia.replace(day=1)
        ultimo_dia = 31
        while ultimo_dia > 28:
            try:
                data_fim = data_inicio.replace(day=ultimo_dia)
                break
            except ValueError:
                ultimo_dia -= 1
        
        lancamentos = cls.objects.filter(
            data_movimentacao__range=[data_inicio, data_fim]
        )
        
        consolidado = {
            'total_lancamentos': lancamentos.count(),
            'total_debitos_bancarios': lancamentos.filter(valor__gt=0).aggregate(
                total=models.Sum('valor')
            )['total'] or 0,
            'total_creditos_bancarios': abs(lancamentos.filter(valor__lt=0).aggregate(
                total=models.Sum('valor')
            )['total'] or 0),
            'saldo_geral': lancamentos.aggregate(total=models.Sum('valor'))['total'] or 0,
            'conciliados': lancamentos.filter(conciliado=True).count(),
            'nao_conciliados': lancamentos.filter(conciliado=False).count(),
            'por_categoria': {},
        }
        
        # Consolidado por categoria (descrição)
        categorias = lancamentos.values(
            'descricao_movimentacao__descricao'
        ).annotate(
            total=models.Sum('valor'),
            quantidade=models.Count('id')
        )
        
        for categoria in categorias:
            nome_categoria = categoria['descricao_movimentacao__descricao'] or 'Sem categoria'
            consolidado['por_categoria'][nome_categoria] = {
                'total': categoria['total'],
                'quantidade': categoria['quantidade'],
                'tipo': 'Débito Bancário' if categoria['total'] > 0 else 'Crédito Bancário'
            }
        
        return consolidado


class SaldoMensalContaCorrente(models.Model):
    """
    Modelo para persistir saldos mensais da conta corrente por sócio.
    
    Este modelo implementa o conceito bancário de fechamento mensal,
    armazenando saldos de abertura, movimentações do período e saldo
    de fechamento, garantindo propagação correta entre competências.
    
    PADRÃO BANCÁRIO IMPLEMENTADO:
    - Saldo Anterior = Saldo de abertura do período
    - Créditos = Entradas no período (valores positivos)
    - Débitos = Saídas no período (valores negativos)
    - Saldo Final = Saldo Anterior + Créditos - Débitos
    
    Este modelo evita recálculo completo do histórico e garante
    integridade temporal dos saldos bancários.
    """
    
    class Meta:
        db_table = 'saldo_mensal_conta_corrente'
        verbose_name = "Saldo Mensal Conta Corrente"
        verbose_name_plural = "Saldos Mensais Conta Corrente"
        unique_together = ('empresa', 'socio', 'competencia')
        indexes = [
            models.Index(fields=['empresa', 'competencia']),
            models.Index(fields=['socio', 'competencia']),
            models.Index(fields=['competencia', 'fechado']),
        ]
        ordering = ['-competencia', 'socio__pessoa__name']

    # Relacionamentos principais
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='saldos_mensais_conta_corrente',
        verbose_name="Empresa",
        help_text="Empresa para isolamento multi-tenant"
    )
    
    socio = models.ForeignKey(
        Socio,
        on_delete=models.CASCADE,
        related_name='saldos_mensais_conta_corrente',
        verbose_name="Médico/Sócio",
        help_text="Sócio titular da conta corrente"
    )

    # Dados temporais
    competencia = models.DateField(
        verbose_name="Competência",
        help_text="Primeiro dia do mês de referência (ex: 2025-08-01)"
    )
    
    # Saldos bancários
    saldo_anterior = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Anterior",
        help_text="Saldo de abertura do período (final do mês anterior)"
    )
    
    total_creditos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Total de Créditos",
        help_text="Soma dos valores positivos (entradas) do período"
    )
    
    total_debitos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Total de Débitos",
        help_text="Soma dos valores negativos (saídas) do período"
    )
    
    saldo_final = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Final",
        help_text="Saldo de fechamento (Anterior + Créditos - Débitos)"
    )
    
    # Controles de processamento
    data_fechamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Fechamento",
        help_text="Timestamp do processamento do fechamento mensal"
    )
    
    fechado = models.BooleanField(
        default=False,
        verbose_name="Fechado",
        help_text="Indica se o período foi oficialmente fechado"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o fechamento mensal"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calcular_saldo_final(self):
        """
        Calcula o saldo final usando a fórmula bancária padrão.
        Saldo Final = Saldo Anterior + Créditos - Débitos
        """
        self.saldo_final = self.saldo_anterior + self.total_creditos - self.total_debitos
        return self.saldo_final
    
    def fechar_periodo(self, usuario=None):
        """
        Marca o período como fechado e registra timestamp.
        """
        from django.utils import timezone
        self.fechado = True
        self.data_fechamento = timezone.now()
        if usuario:
            self.observacoes += f"\nFechado por: {usuario} em {timezone.now()}"
        self.save()
    
    def __str__(self):
        return f"{self.socio.pessoa.name} - {self.competencia.strftime('%m/%Y')} - Saldo: R$ {self.saldo_final}"
