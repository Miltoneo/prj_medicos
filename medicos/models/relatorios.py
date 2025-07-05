"""
Modelos relacionados a relatórios consolidados

Este módulo contém todos os modelos relacionados à geração de relatórios
consolidados mensais e outras análises do sistema financeiro manual.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Conta


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
            from .financeiro import TIPO_MOVIMENTACAO_CONTA_CREDITO, TIPO_MOVIMENTACAO_CONTA_DEBITO
            creditos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_CREDITO)
            debitos = lancamentos.filter(tipo=TIPO_MOVIMENTACAO_CONTA_DEBITO)
            
            self.total_valor_creditos = creditos.aggregate(Sum('valor'))['valor__sum'] or 0
            self.total_valor_debitos = debitos.aggregate(Sum('valor'))['valor__sum'] or 0
            
            # Maiores lançamentos
            self.maior_lancamento_credito = creditos.aggregate(Max('valor'))['valor__max'] or 0
            self.maior_lancamento_debito = debitos.aggregate(Max('valor'))['valor__max'] or 0
            
            # Usuários diferentes
            self.usuarios_diferentes = lancamentos.values('lancado_por').distinct().count()
            
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
            from .auditoria import LogAuditoriaFinanceiro
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
        from .financeiro import TIPO_MOVIMENTACAO_CONTA_CREDITO, TIPO_MOVIMENTACAO_CONTA_DEBITO
        
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
            'financeiro': 'debitos_financeiro',
            'saldo': 'debitos_saldo',
            'outros': 'debitos_outros'
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
        
        # Validar lançamentos sem aprovação quando necessário
        sem_aprovacao = lancamentos.filter(
            valor__gt=config.limite_aprovacao_gerencial,
            status__in=['rascunho', 'pendente'],
            aprovado_por__isnull=True
        ).count()
        if sem_aprovacao > 0:
            inconsistencias.append({
                'tipo': 'aprovacao_pendente',
                'quantidade': sem_aprovacao,
                'descricao': f'{sem_aprovacao} lançamentos de valor alto pendentes de aprovação'
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
        
        # Registrar auditoria
        from .auditoria import LogAuditoriaFinanceiro
        LogAuditoriaFinanceiro.registrar_acao(
            conta=self.conta,
            usuario=usuario,
            acao='gerar_relatorio',
            descricao_acao=f"Aprovação de relatório consolidado mensal: {self.mes_ano_formatado}",
            objeto_id=self.id,
            objeto_tipo='RelatorioConsolidadoMensal'
        )
    
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
    
    def exportar_para_dict(self):
        """
        Exporta os dados do relatório para um dicionário
        """
        return {
            'conta': self.conta.name,
            'mes_referencia': self.mes_ano_formatado,
            'estatisticas_gerais': {
                'total_medicos_ativos': self.total_medicos_ativos,
                'total_lancamentos': self.total_lancamentos,
                'total_creditos': str(self.total_valor_creditos),
                'total_debitos': str(self.total_valor_debitos),
                'saldo_consolidado': str(self.saldo_geral_consolidado),
                'movimentacao_liquida': str(self.movimentacao_liquida),
            },
            'distribuicao_creditos': {
                'adiantamentos': str(self.creditos_adiantamentos),
                'pagamentos': str(self.creditos_pagamentos),
                'ajustes': str(self.creditos_ajustes),
                'transferencias': str(self.creditos_transferencias),
                'financeiro': str(self.creditos_financeiro),
                'saldo': str(self.creditos_saldo),
                'outros': str(self.creditos_outros),
            },
            'distribuicao_debitos': {
                'adiantamentos': str(self.debitos_adiantamentos),
                'despesas': str(self.debitos_despesas),
                'taxas': str(self.debitos_taxas),
                'transferencias': str(self.debitos_transferencias),
                'ajustes': str(self.debitos_ajustes),
                'financeiro': str(self.debitos_financeiro),
                'saldo': str(self.debitos_saldo),
                'outros': str(self.debitos_outros),
            },
            'auditoria': {
                'lancamentos_valores_altos': self.lancamentos_valores_altos,
                'lancamentos_sem_documento': self.lancamentos_sem_documento,
                'usuarios_diferentes': self.usuarios_diferentes,
                'maior_credito': str(self.maior_lancamento_credito),
                'maior_debito': str(self.maior_lancamento_debito),
                'inconsistencias': self.inconsistencias_encontradas,
                'detalhes_inconsistencias': self.detalhes_inconsistencias,
            },
            'controle': {
                'status': self.get_status_display(),
                'data_geracao': self.data_geracao.isoformat(),
                'tempo_processamento': str(self.tempo_processamento) if self.tempo_processamento else None,
                'gerado_por': self.gerado_por.username if self.gerado_por else None,
                'aprovado_por': self.aprovado_por.username if self.aprovado_por else None,
                'data_aprovacao': self.data_aprovacao.isoformat() if self.data_aprovacao else None,
            }
        }
