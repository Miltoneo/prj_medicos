"""
Modelos relacionados à auditoria e configuração do sistema

Este módulo contém todos os modelos relacionados à auditoria, logging
e configurações do sistema manual de fluxo de caixa.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Conta


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
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracoes_sistema_manual_criadas',
        verbose_name="Criado Por"
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


class LogAuditoriaFinanceiro(models.Model):
    """
    Log de auditoria para todas as operações no sistema financeiro
    
    Este modelo registra todas as ações importantes realizadas no sistema
    financeiro manual, garantindo rastreabilidade completa de todas as
    operações para fins de auditoria e controle.
    """
    
    class Meta:
        db_table = 'log_auditoria_financeiro'
        indexes = [
            models.Index(fields=['conta', 'data_acao']),
            models.Index(fields=['usuario', 'acao']),
            models.Index(fields=['data_acao']),
            models.Index(fields=['ip_origem']),
        ]
        verbose_name = "Log de Auditoria Financeiro"
        verbose_name_plural = "Logs de Auditoria Financeiros"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='logs_auditoria', 
        null=False
    )
    
    # === DADOS DA AÇÃO ===
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário",
        help_text="Usuário que executou a ação"
    )
    
    data_acao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data/Hora da Ação"
    )
    
    # Tipos de ação para categorização
    ACOES_CHOICES = [
        # Lançamentos financeiros
        ('criar_lancamento', 'Criar Lançamento'),
        ('editar_lancamento', 'Editar Lançamento'),
        ('excluir_lancamento', 'Excluir Lançamento'),
        ('aprovar_lancamento', 'Aprovar Lançamento'),
        ('processar_lancamento', 'Processar Lançamento'),
        ('cancelar_lancamento', 'Cancelar Lançamento'),
        
        # Gestão de saldos
        ('calcular_saldo', 'Calcular Saldo'),
        ('fechar_mes', 'Fechar Mês'),
        ('reabrir_mes', 'Reabrir Mês'),
        
        # Configurações
        ('alterar_configuracao', 'Alterar Configuração'),
        ('criar_descricao', 'Criar Descrição de Movimentação'),
        ('editar_descricao', 'Editar Descrição de Movimentação'),
        
        # Relatórios
        ('gerar_relatorio', 'Gerar Relatório'),
        ('exportar_dados', 'Exportar Dados'),
        
        # Acesso e segurança
        ('login', 'Login no Sistema'),
        ('logout', 'Logout do Sistema'),
        ('acesso_negado', 'Acesso Negado'),
        ('tentativa_invalida', 'Tentativa de Operação Inválida'),
    ]
    
    acao = models.CharField(
        max_length=30,
        choices=ACOES_CHOICES,
        verbose_name="Ação Executada"
    )
    
    descricao_acao = models.TextField(
        verbose_name="Descrição da Ação",
        help_text="Descrição detalhada da ação executada"
    )
    
    # === DADOS RELACIONADOS ===
    objeto_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID do Objeto",
        help_text="ID do objeto principal relacionado à ação"
    )
    
    objeto_tipo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Tipo do Objeto",
        help_text="Tipo do objeto relacionado (ex: Financeiro, SaldoMensal, etc.)"
    )
    
    # === VALORES PARA AUDITORIA ===
    valores_anteriores = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Valores Anteriores",
        help_text="Valores antes da modificação (para edições)"
    )
    
    valores_novos = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Valores Novos",
        help_text="Valores após a modificação"
    )
    
    # === DADOS TÉCNICOS ===
    ip_origem = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP de Origem"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Informações do navegador/cliente"
    )
    
    # === RESULTADO DA AÇÃO ===
    RESULTADO_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
        ('cancelado', 'Cancelado'),
        ('negado', 'Negado'),
    ]
    
    resultado = models.CharField(
        max_length=20,
        choices=RESULTADO_CHOICES,
        default='sucesso',
        verbose_name="Resultado da Ação"
    )
    
    mensagem_erro = models.TextField(
        blank=True,
        verbose_name="Mensagem de Erro",
        help_text="Detalhes do erro (quando resultado = erro)"
    )
    
    # === METADADOS ===
    duracao_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duração (ms)",
        help_text="Tempo de execução da ação em milissegundos"
    )
    
    dados_extras = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados Extras",
        help_text="Dados adicionais específicos da ação"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_auditoria_criados',
        verbose_name="Criado Por"
    )

    def __str__(self):
        usuario_nome = self.usuario.username if self.usuario else "Sistema"
        return f"{self.data_acao.strftime('%d/%m/%Y %H:%M')} - {usuario_nome} - {self.get_acao_display()}"
    
    @property
    def data_formatada(self):
        """Retorna data formatada"""
        return self.data_acao.strftime('%d/%m/%Y %H:%M:%S')
    
    @property
    def duracao_formatada(self):
        """Retorna duração formatada"""
        if self.duracao_ms is None:
            return "N/A"
        if self.duracao_ms < 1000:
            return f"{self.duracao_ms}ms"
        else:
            return f"{self.duracao_ms/1000:.2f}s"
    
    @classmethod
    def registrar_acao(cls, conta, usuario, acao, descricao_acao, 
                       objeto_id=None, objeto_tipo=None, 
                       valores_anteriores=None, valores_novos=None,
                       ip_origem=None, user_agent=None, 
                       resultado='sucesso', mensagem_erro=None,
                       duracao_ms=None, dados_extras=None):
        """
        Método de classe para registrar uma ação de auditoria
        """
        log = cls(
            conta=conta,
            usuario=usuario,
            acao=acao,
            descricao_acao=descricao_acao,
            objeto_id=objeto_id,
            objeto_tipo=objeto_tipo,
            valores_anteriores=valores_anteriores,
            valores_novos=valores_novos,
            ip_origem=ip_origem,
            user_agent=user_agent,
            resultado=resultado,
            mensagem_erro=mensagem_erro,
            duracao_ms=duracao_ms,
            dados_extras=dados_extras
        )
        log.save()
        return log
    
    @classmethod
    def limpar_logs_antigos(cls, conta, dias_retencao=365):
        """
        Remove logs mais antigos que o período de retenção
        """
        from datetime import timedelta
        
        data_limite = timezone.now() - timedelta(days=dias_retencao)
        logs_removidos = cls.objects.filter(
            conta=conta,
            data_acao__lt=data_limite
        ).delete()
        
        return logs_removidos[0] if logs_removidos else 0
    
    @classmethod
    def obter_estatisticas_conta(cls, conta, data_inicio=None, data_fim=None):
        """
        Obtém estatísticas de auditoria para uma conta
        """
        queryset = cls.objects.filter(conta=conta)
        
        if data_inicio:
            queryset = queryset.filter(data_acao__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_acao__lte=data_fim)
        
        from django.db.models import Count
        
        estatisticas = {
            'total_acoes': queryset.count(),
            'acoes_por_tipo': dict(
                queryset.values('acao').annotate(count=Count('id')).values_list('acao', 'count')
            ),
            'acoes_por_usuario': dict(
                queryset.values('usuario__username').annotate(count=Count('id')).values_list('usuario__username', 'count')
            ),
            'acoes_por_resultado': dict(
                queryset.values('resultado').annotate(count=Count('id')).values_list('resultado', 'count')
            ),
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim
            }
        }
        
        return estatisticas


# Função de conveniência para auditoria
def registrar_auditoria(request, conta, acao, descricao, **kwargs):
    """
    Função de conveniência para registrar ações de auditoria
    
    Args:
        request: HttpRequest object
        conta: Instância da conta
        acao: Tipo da ação (deve estar em ACOES_CHOICES)
        descricao: Descrição detalhada da ação
        **kwargs: Argumentos adicionais para LogAuditoriaFinanceiro.registrar_acao
    """
    ip_origem = None
    user_agent = None
    
    if request:
        # Extrair IP do request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_origem = x_forwarded_for.split(',')[0].strip()
        else:
            ip_origem = request.META.get('REMOTE_ADDR')
        
        # Extrair user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return LogAuditoriaFinanceiro.registrar_acao(
        conta=conta,
        usuario=request.user if request and hasattr(request, 'user') else None,
        acao=acao,
        descricao_acao=descricao,
        ip_origem=ip_origem,
        user_agent=user_agent,
        **kwargs
    )
