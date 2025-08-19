from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .base import Conta, SaaSBaseModel, Empresa, Socio

# Modelo restaurado: MeioPagamento

class MeioPagamento(models.Model):
    """
    Meios de pagamento cadastrados pelos usuários
    
    Agora o meio de pagamento é definido por empresa, não mais por conta.
    """
    class Meta:
        db_table = 'meio_pagamento'
        unique_together = ('empresa', 'codigo')
        verbose_name = "Meio de Pagamento"
        verbose_name_plural = "Meios de Pagamento"
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['codigo']),
        ]

    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='meios_pagamento',
        verbose_name="Empresa",
        help_text="Empresa à qual este meio de pagamento pertence"
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
        help_text="Nome descritivo do meio de pagamento",
        blank=True,
        null=True
    )

    # Status e controle
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se este meio de pagamento está disponível para uso"
    )

    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
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
        """Validação de unicidade do código por empresa."""
        if self.codigo:
            qs = MeioPagamento.objects.filter(
                empresa=self.empresa,
                codigo=self.codigo
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'codigo': 'Já existe um meio de pagamento com este código nesta empresa'
                })

    def __str__(self):
        return f"{self.nome} ({self.codigo})"
    



"""
Modelos relacionados ao sistema financeiro manual

Este módulo contém todos os modelos relacionados ao fluxo de caixa manual
da aplicação de médicos, incluindo descrições de movimentação, lançamentos
financeiros e saldos mensais consolidados.
"""

# Constantes específicas para financeiro
TIPO_MOVIMENTACAO_CONTA_CREDITO = 1    # entradas, creditos, depositos
TIPO_MOVIMENTACAO_CONTA_DEBITO = 2     # retiradas, transferencia


class DescricaoMovimentacaoFinanceira(models.Model):
    # Removido método pode_ser_usada_para pois tipo_movimentacao foi excluído
    """
    Descrições de movimentação financeira cadastradas pelos usuários
    
    Este modelo permite que os usuários criem e gerenciem suas próprias
    descrições padronizadas para categorizar movimentações financeiras,
    facilitando a organização e relatórios personalizados.
    """
    
    class Meta:
        db_table = 'descricao_movimentacao'
        unique_together = ()
        constraints = []
        verbose_name = "Descrição de Movimentação"
        verbose_name_plural = "Descrições de Movimentação"
        indexes = []

    # Removido campo conta: descrição agora é específica para empresa

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='descricoes_movimentacao',
        verbose_name="Empresa",
        help_text="Empresa à qual esta descrição pertence"
    )
    
    # Identificação da descrição
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição Detalhada",
        help_text="Descrição completa sobre quando usar esta movimentação"
    )
    
    # Removido bloco TIPOS_MOVIMENTACAO pois tipo_movimentacao foi excluído
    
    
    # Configurações contábeis/fiscais
    codigo_contabil = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Código Contábil",
        help_text="Código contábil para classificação (plano de contas)"
    )
    
    
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='descricoes_movimentacao_criadas',
        verbose_name="Criado Por"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o uso desta descrição"
    )

    # Removido clean pois campos de retenção foram excluídos

    def __str__(self):
        return self.descricao or f"DescriçãoMovimentacaoFinanceira #{self.pk}"
    
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
    
    # Removido calcular_retencao_ir pois campos de retenção foram excluídos
    
    @classmethod
    def obter_ativas(cls, empresa):
        """Obtém todas as descrições para uma empresa"""
        return cls.objects.filter(empresa=empresa).order_by('descricao')
    
    # Removido obter_creditos pois tipo_movimentacao foi excluído
    
    # Removido obter_debitos pois tipo_movimentacao foi excluído
    
    # Removido obter_frequentes pois uso_frequente foi excluído
    
    @classmethod
    def criar_descricoes_padrao(cls, empresa, usuario=None):
        """Cria descrições padrão para uma nova empresa"""
        descricoes_padrao = [
            {'descricao': 'Recebimento de honorários por serviços médicos prestados'},
            {'descricao': 'Recebimento por consultas médicas realizadas'},
            {'descricao': 'Recebimento por plantões médicos realizados'},
            {'descricao': 'Adiantamento de lucros da sociedade médica'},
            {'descricao': 'Adiantamento concedido para cobrir despesas'},
            {'descricao': 'Gastos com materiais médicos e insumos'},
            {'descricao': 'Gastos com cursos, congressos e capacitação'},
            {'descricao': 'Retirada de valores para uso pessoal'},
            {'descricao': 'Transferência bancária recebida de terceiros'},
            {'descricao': 'Transferência bancária enviada para terceiros'},
            {'descricao': 'Ajuste contábil positivo'},
            {'descricao': 'Ajuste contábil negativo'},
        ]
        descricoes_criadas = []
        for desc_data in descricoes_padrao:
            if not cls.objects.filter(
                empresa=empresa,
                descricao=desc_data['descricao']
            ).exists():
                descricao = cls.objects.create(
                    empresa=empresa,
                    criada_por=usuario,
                    observacoes='Descrição criada automaticamente',
                    descricao=desc_data['descricao']
                )
                descricoes_criadas.append(descricao)
        return descricoes_criadas


class AplicacaoFinanceira(models.Model):
    """
    Modelo simplificado para controle de aplicações financeiras.
    
    Mantém apenas os campos essenciais: data de referência, saldo, 
    IR cobrado e descrição da aplicação.
    """
    
    class Meta:
        db_table = 'aplicacao_financeira'
        unique_together = ('data_referencia', 'empresa')
        verbose_name = "Aplicação Financeira"
        verbose_name_plural = "Aplicações Financeiras"
        indexes = [
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
    
    rendimentos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Rendimentos auferidos no período"
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
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aplicacoes_financeiras_criadas',
        verbose_name="Criado Por"
    )
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        if self.saldo < 0:
            raise ValidationError({'saldo': 'Saldo não pode ser negativo'})
        
        if self.rendimentos < 0:
            raise ValidationError({'rendimentos': 'Rendimentos não podem ser negativos'})
        
        if self.ir_cobrado < 0:
            raise ValidationError({'ir_cobrado': 'IR cobrado não pode ser negativo'})
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.data_referencia.strftime('%m/%Y')} - Saldo: R$ {self.saldo:,.2f} - Rendimentos: R$ {self.rendimentos:,.2f}"


class Financeiro(models.Model):
    """
    Modelo principal para lançamentos financeiros manuais
    sdf
    Este modelo substitui e simplifica o antigo sistema de saldos mensais,
    permitindo lançamentos individuais que são consolidados dinamicamente
    conforme necessário para relatórios.
    """
    
    class Meta:
        db_table = 'financeiro'
        verbose_name = "Lançamento Financeiro"
        verbose_name_plural = "Lançamentos Financeiros"
        indexes = [
            models.Index(fields=['socio', 'data_movimentacao']),
            models.Index(fields=['descricao_movimentacao_financeira']),
        ]
        ordering = ['-data_movimentacao', '-created_at']

    # Relacionamentos principais
    # campo conta removido
    nota_fiscal = models.ForeignKey(
        'medicos.NotaFiscal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_financeiros',
        verbose_name="Nota Fiscal",
        help_text="Nota fiscal relacionada a este lançamento, se houver."
    )
    socio = models.ForeignKey(
        Socio,
        on_delete=models.PROTECT,
        related_name='lancamentos_financeiros',
        verbose_name="Médico/Sócio",
        help_text="Médico ou sócio responsável por esta movimentação"
    )
    descricao_movimentacao_financeira = models.ForeignKey(
        DescricaoMovimentacaoFinanceira,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name="Descrição da Movimentação",
        help_text="Descrição padronizada desta movimentação"
    )

    # Dados do lançamento
    data_movimentacao = models.DateField(
        verbose_name="Data da Movimentação",
        help_text="Data em que a movimentação foi realizada"
    )
    
    # Campo 'tipo' removido: agora o lançamento não diferencia crédito/débito por campo específico
    
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor",
        help_text="Valor da movimentação em reais. Use valor positivo para crédito (entrada) e negativo para débito (saída)."
    )
    

    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_financeiros_criados',
        verbose_name="Criado Por"
    )

    def clean(self):
        """Validações personalizadas"""
        super().clean()
        # Permitir valor positivo ou negativo. Valor zero pode ser tratado conforme regra de negócio.
        # Validação: data de movimentação não pode ser futura
        hoje = timezone.now().date()
        if self.data_movimentacao:
            if self.data_movimentacao > hoje:
                raise ValidationError({
                    'data_movimentacao': 'A data da movimentação não pode ser futura.'
                })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.socio.pessoa.name} - {self.data_movimentacao.strftime('%d/%m/%Y')} - R$ {self.valor:,.2f}"
    
    # Removido tipo_display_sinal pois campo tipo foi excluído
    
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
    def obter_saldo_periodo(cls, socio, data_inicio, data_fim):
        """Calcula o saldo de um período específico para um sócio"""
        lancamentos = cls.objects.filter(
            socio=socio,
            data_movimentacao__range=[data_inicio, data_fim]
        )
        total = lancamentos.aggregate(total=models.Sum('valor'))['total'] or 0
        return {
            'total_creditos': total,
            'total_debitos': 0,
            'saldo_liquido': total,
            'quantidade_lancamentos': lancamentos.count()
        }

    @classmethod
    def obter_saldo_mensal(cls, socio, mes_referencia):
        """Calcula o saldo de um mês específico para um sócio"""
        data_inicio = mes_referencia.replace(day=1)
        ultimo_dia = 31
        while ultimo_dia > 28:
            try:
                data_fim = data_inicio.replace(day=ultimo_dia)
                break
            except ValueError:
                ultimo_dia -= 1
        return cls.obter_saldo_periodo(socio, data_inicio, data_fim)

    @classmethod
    def obter_consolidado_empresa(cls, empresa, mes_referencia):
        """Obtém o consolidado de toda a empresa em um mês"""
        data_inicio = mes_referencia.replace(day=1)
        ultimo_dia = 31
        while ultimo_dia > 28:
            try:
                data_fim = data_inicio.replace(day=ultimo_dia)
                break
            except ValueError:
                ultimo_dia -= 1
        lancamentos = cls.objects.filter(
            socio__empresa=empresa,
            data_movimentacao__range=[data_inicio, data_fim]
        )
        consolidado = {
            'total_lancamentos': lancamentos.count(),
            'total_creditos': lancamentos.aggregate(total=models.Sum('valor'))['total'] or 0,
            'total_debitos': 0,
            'saldo_geral': lancamentos.aggregate(total=models.Sum('valor'))['total'] or 0,
            'medicos_ativos': lancamentos.values('socio').distinct().count(),
            'por_socio': {},
            'por_categoria': {},
        }
        for socio in Socio.objects.filter(
            empresa=empresa,
            id__in=lancamentos.values_list('socio', flat=True).distinct()
        ):
            saldo_socio = cls.obter_saldo_periodo(socio, data_inicio, data_fim)
            consolidado['por_socio'][socio.id] = {
                'socio': socio,
                'saldo': saldo_socio
            }
        categorias = lancamentos.values(
            'descricao_movimentacao_financeira__descricao'
        ).annotate(
            total=models.Sum('valor'),
            quantidade=models.Count('id')
        ).filter(total__gt=0)
        for categoria in categorias:
            nome_categoria = categoria['descricao_movimentacao_financeira__descricao'] or 'Sem categoria'
            consolidado['por_categoria'][nome_categoria] = {
                'total': categoria['total'],
                'quantidade': categoria['quantidade']
            }
        return consolidado



