"""
Modelos relacionados a gestão de despesas e rateio

Este módulo contém todos os modelos relacionados ao sistema de gestão de despesas
da aplicação de médicos, incluindo grupos, itens, despesas e sistema de rateio.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Conta, SaaSBaseModel, Empresa, Socio

# Constantes específicas para despesas
CODIGO_GRUPO_DESPESA_GERAL = 'GERAL'
CODIGO_GRUPO_DESPESA_FOLHA = 'FOLHA'
CODIGO_GRUPO_DESPESA_SOCIO = 'SOCIO'

TIPO_DESPESA_COM_RATEIO = 1
TIPO_DESPESA_SEM_RATEIO = 2

GRUPO_ITEM_COM_RATEIO = 1
GRUPO_ITEM_SEM_RATEIO = 2


class Despesa_Grupo(models.Model):
    """Grupos de despesas para organização contábil"""
    
    class Meta:
        db_table = 'despesa_grupo'
        unique_together = ('conta', 'codigo')
        verbose_name = "Grupo de Despesa"
        verbose_name_plural = "Grupos de Despesas"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='despesa_grupos', 
        null=False
    )
    
    class Tipo_t(models.IntegerChoices):
        COM_RATEIO = GRUPO_ITEM_COM_RATEIO, "COM RATEIO"
        SEM_RATEIO = GRUPO_ITEM_SEM_RATEIO, "SEM RATEIO"

    codigo = models.CharField(max_length=20, null=False)
    descricao = models.CharField(max_length=255, null=False, default="")
    tipo_rateio = models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.COM_RATEIO
    )

    def __str__(self):
        return f"{self.codigo}"


class Despesa_Item(models.Model):
    """Itens específicos de despesas dentro de cada grupo"""
    
    class Meta:
        db_table = 'despesa_item'
        unique_together = ('conta', 'codigo')
        verbose_name = "Item de Despesa"
        verbose_name_plural = "Itens de Despesas"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='despesa_itens', 
        null=False
    )
    grupo = models.ForeignKey(Despesa_Grupo, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, null=False)
    descricao = models.CharField(max_length=255, null=False, default="")

    @property
    def permite_rateio(self):
        """Verifica se o item permite rateio baseado no grupo"""
        return self.grupo.codigo in ['FOLHA', 'GERAL']
    
    @property
    def codigo_completo(self):
        """Retorna código completo no formato GRUPO.ITEM"""
        return f"{self.grupo.codigo}.{self.codigo}"

    def __str__(self):
        return f"{self.grupo.codigo} {self.descricao}"


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

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='percentuais_rateio', 
        null=False
    )
    
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


class ConfiguracaoRateioMensal(models.Model):
    """Configuração geral de rateio para um mês específico"""
    
    class Meta:
        db_table = 'configuracao_rateio_mensal'
        unique_together = ('conta', 'mes_referencia')
        verbose_name = "Configuração de Rateio Mensal"
        verbose_name_plural = "Configurações de Rateio Mensais"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='configuracoes_rateio'
    )
    
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

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='despesas', 
        null=False
    )
    
    class Tipo_t(models.IntegerChoices):
        COM_RATEIO = TIPO_DESPESA_COM_RATEIO, "DESPESA FOLHA/GERAL - COM RATEIO"
        SEM_RATEIO = TIPO_DESPESA_SEM_RATEIO, "DESPESA DE SOCIO - SEM RATEIO"

    # Classificação
    tipo_rateio = models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.COM_RATEIO,
        verbose_name="Tipo de Rateio"
    )
    item = models.ForeignKey(
        'Despesa_Item', 
        on_delete=models.PROTECT, 
        verbose_name="Item de Despesa"
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

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='despesa_socios_rateio', 
        null=False
    )
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
