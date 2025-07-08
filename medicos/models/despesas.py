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


class GrupoDespesa(models.Model):
    """Grupos de despesas para organização contábil"""
    
    class Meta:
        db_table = 'despesa_grupo'
        unique_together = ('conta', 'codigo')
        verbose_name = "Grupo de Despesa"
        verbose_name_plural = "Grupos de Despesas"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='grupos_despesa', 
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

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grupos_despesa_criados',
        verbose_name="Criado Por"
    )

    def __str__(self):
        return f"{self.codigo}"


class ItemDespesa(models.Model):
    """Itens específicos de despesas dentro de cada grupo"""
    
    class Meta:
        db_table = 'despesa_item'
        unique_together = ('conta', 'codigo')
        verbose_name = "Item de Despesa"
        verbose_name_plural = "Itens de Despesas"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='itens_despesa', 
        null=False
    )
    grupo = models.ForeignKey(GrupoDespesa, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, null=False)
    descricao = models.CharField(max_length=255, null=False, default="")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_despesa_criados',
        verbose_name="Criado Por"
    )

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


class ItemDespesaRateioMensal(models.Model):
    """
    Configuração de rateio mensal percentual para itens de despesa entre médicos/sócios
    
    Este modelo é fundamental para o sistema de gestão financeira, definindo como
    os custos operacionais da clínica/associação médica devem ser distribuídos
    entre os médicos sócios através de percentuais fixos por mês.
    
    RATEIO PERCENTUAL:
    
    - Cada médico tem um percentual fixo do custo total da despesa
    - A soma de todos os percentuais deve ser exatamente 100%
    - Sistema simples, claro e auditável
    - Ideal para todos os tipos de despesas (fixas e variáveis)
    
    FLUXO DE FUNCIONAMENTO:
    
    1. Configuração mensal: Define-se o percentual de cada médico por item
    2. Lançamento de despesas: Despesas são classificadas por item/grupo
    3. Processamento de rateio: Sistema distribui valores proporcionalmente
    4. Relatórios gerenciais: Acompanhamento dos custos por médico
    
    INTEGRAÇÃO COM O SISTEMA:
    
    - Conecta-se ao módulo de Despesas para aplicação automática dos rateios
    - Gera dados para relatórios de custos por médico
    - Base para cálculo de resultado individual dos sócios
    - Auditoria completa de todas as configurações e alterações
    
    EXEMPLOS DE USO:
    
    Aluguel da clínica:
    - Dr. João: 45% (sala maior)
    - Dr. Maria: 35% (sala média)  
    - Dr. Pedro: 20% (sala menor)
    
    Energia elétrica:
    - Dr. João: 40% 
    - Dr. Maria: 35%
    - Dr. Pedro: 25%
    
    Material de consumo:
    - Dr. João: 50% (maior volume de atendimentos)
    - Dr. Maria: 30%
    - Dr. Pedro: 20%
    """
    
    class Meta:
        db_table = 'item_despesa_rateio_mensal'
        unique_together = ('conta', 'item_despesa', 'socio', 'mes_referencia')
        verbose_name = "Rateio Mensal de Item de Despesa"
        verbose_name_plural = "Rateios Mensais de Itens de Despesa"
        indexes = [
            models.Index(fields=['mes_referencia', 'item_despesa']),
            models.Index(fields=['socio', 'mes_referencia']),
            models.Index(fields=['item_despesa', 'ativo']),
        ]

    # Tenant isolation
    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='rateios_itens_despesa', 
        null=False,
        verbose_name="Conta"
    )
    
    # Relacionamentos principais
    item_despesa = models.ForeignKey(
        'ItemDespesa', 
        on_delete=models.CASCADE, 
        related_name='rateios_mensais',
        verbose_name="Item de Despesa",
        help_text="Item de despesa que será rateado"
    )
    
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        related_name='rateios_despesas',
        verbose_name="Médico/Sócio",
        help_text="Médico que participará do rateio"
    )
    
    # Data de referência (mês/ano)
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Data no formato YYYY-MM-01 (primeiro dia do mês). Define o período em que esta configuração de rateio será aplicada."
    )
    
    # Valor de rateio percentual
    percentual_rateio = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Percentual de Rateio (%)",
        help_text="Percentual que este médico deve pagar deste item (0-100%). A soma de todos os médicos deve ser 100%."
    )
    
    # Controle e auditoria
    ativo = models.BooleanField(
        default=True, 
        verbose_name="Ativo",
        help_text="Se este rateio está ativo para o período"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rateios_despesa_criados',
        verbose_name="Criado Por"
    )
    
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações",
        help_text="Observações sobre este rateio específico. Ex: 'Sala maior', 'Meio período', 'Acordo especial', etc. Importante para justificar percentuais diferenciados."
    )

    def clean(self):
        """
        Validações personalizadas para garantir consistência do rateio percentual
        
        Validações implementadas:
        1. Obrigatoriedade do percentual de rateio
        2. Limites válidos para percentuais (0-100%)
        3. Verificação se o item permite rateio (apenas grupos FOLHA e GERAL)
        4. Consistência entre sócio e item (mesma conta/empresa)
        """
        # Verificar se o percentual de rateio foi informado
        if not self.percentual_rateio:
            raise ValidationError({
                'percentual_rateio': 'Percentual de rateio é obrigatório'
            })
        
        # Verificar se o percentual está no range válido (0-100%)
        if self.percentual_rateio < 0 or self.percentual_rateio > 100:
            raise ValidationError({
                'percentual_rateio': 'Percentual deve estar entre 0 e 100%'
            })
        
        # Verificar se o item permite rateio (apenas grupos FOLHA e GERAL)
        if self.item_despesa and not self.item_despesa.permite_rateio:
            raise ValidationError({
                'item_despesa': (
                    f'O item "{self.item_despesa.descricao}" não permite rateio. '
                    f'Apenas itens dos grupos FOLHA e GERAL permitem rateio.'
                )
            })
        
        # Verificar se o item é dos grupos corretos (FOLHA ou GERAL)
        if self.item_despesa and self.item_despesa.grupo.codigo not in ['FOLHA', 'GERAL']:
            raise ValidationError({
                'item_despesa': (
                    f'Rateios só podem ser definidos para itens dos grupos FOLHA e GERAL. '
                    f'O item selecionado é do grupo "{self.item_despesa.grupo.codigo}".'
                )
            })
        
        # Verificar se sócio e item pertencem à mesma conta (tenant isolation)
        if self.socio and self.item_despesa:
            if self.socio.empresa.conta != self.item_despesa.conta:
                raise ValidationError({
                    'socio': 'Sócio e item de despesa devem pertencer à mesma conta/empresa.'
                })

    def save(self, *args, **kwargs):
        """
        Método save customizado com validações e normalizações automáticas
        
        Operações realizadas:
        1. Normaliza a data para o primeiro dia do mês (formato padrão)
        2. Garante consistência da conta entre item e rateio (tenant isolation)
        3. Executa todas as validações antes de salvar
        """
        # Normalizar a data para o primeiro dia do mês (formato padrão do sistema)
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        
        # Garantir que a conta seja consistente (tenant isolation)
        if self.item_despesa:
            self.conta = self.item_despesa.conta
        
        # Executar todas as validações antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.item_despesa.codigo_completo} - "
            f"{self.socio.pessoa.name} - "
            f"{self.percentual_rateio}% "
            f"({self.mes_referencia.strftime('%m/%Y')})"
        )
    
    @property
    def mes_ano_formatado(self):
        """Retorna o mês/ano formatado"""
        return self.mes_referencia.strftime('%m/%Y')
    
    @property
    def valor_rateio_display(self):
        """Retorna o percentual formatado"""
        return f"{self.percentual_rateio:.2f}%"
    
    @classmethod
    def obter_rateio_para_despesa(cls, item_despesa, socio, data_despesa):
        """
        Método de classe para obter o rateio para um item/sócio em uma data específica
        """
        # Normalizar para o primeiro dia do mês
        mes_referencia = data_despesa.replace(day=1)
        
        try:
            rateio_obj = cls.objects.get(
                item_despesa=item_despesa,
                socio=socio,
                mes_referencia=mes_referencia,
                ativo=True
            )
            return rateio_obj
        except cls.DoesNotExist:
            # Se não encontrar rateio específico, retornar None
            return None
    
    @classmethod
    def validar_rateios_mes(cls, item_despesa, mes_referencia):
        """
        Valida se a configuração de rateios percentuais para um item em um mês específico está correta
        """
        rateios = cls.objects.filter(
            item_despesa=item_despesa,
            mes_referencia=mes_referencia,
            ativo=True
        )
        
        # Verificar se os percentuais somam 100%
        total_percentual = sum(r.percentual_rateio or 0 for r in rateios)
        
        return {
            'valido': abs(total_percentual - 100) < 0.01,
            'total_percentual': total_percentual,
            'total_rateios': rateios.count(),
            'rateios': list(rateios)
        }
    
    @classmethod
    def criar_rateio_igualitario(cls, item_despesa, medicos_lista, mes_referencia, usuario=None):
        """
        Cria rateio igualitário entre uma lista de médicos para um item de despesa
        
        Args:
            item_despesa: Instância do ItemDespesa
            medicos_lista: Lista de instâncias de Socio
            mes_referencia: Data do mês de referência
            usuario: Usuário que está criando o rateio
        
        Returns:
            list: Lista dos rateios criados
        """
        if not medicos_lista:
            raise ValidationError("Lista de médicos não pode estar vazia")
        
        # Calcular percentual igual para todos
        percentual_por_medico = 100 / len(medicos_lista)
        
        # Limpar rateios existentes para este item/mês
        cls.objects.filter(
            item_despesa=item_despesa,
            mes_referencia=mes_referencia.replace(day=1)
        ).delete()
        
        rateios_criados = []
        for medico in medicos_lista:
            rateio = cls.objects.create(
                conta=item_despesa.conta,
                item_despesa=item_despesa,
                socio=medico,
                mes_referencia=mes_referencia.replace(day=1),
                percentual_rateio=percentual_por_medico,
                created_by=usuario,
                observacoes=f'Rateio igualitário entre {len(medicos_lista)} médicos'
            )
            rateios_criados.append(rateio)
        
        return rateios_criados
    
    @classmethod
    def criar_rateio_por_percentuais(cls, item_despesa, rateios_config, mes_referencia, usuario=None):
        """
        Cria rateio baseado em percentuais específicos
        
        Args:
            item_despesa: Instância do ItemDespesa
            rateios_config: Lista de dicts com 'medico' e 'percentual'
            mes_referencia: Data do mês de referência
            usuario: Usuário que está criando o rateio
        
        Returns:
            list: Lista dos rateios criados
        """
        # Validar que o total dos percentuais não excede 100%
        total_percentual = sum(config['percentual'] for config in rateios_config)
        if total_percentual > 100:
            raise ValidationError(f'Total dos percentuais ({total_percentual}%) excede 100%')
        
        # Limpar rateios existentes
        cls.objects.filter(
            item_despesa=item_despesa,
            mes_referencia=mes_referencia.replace(day=1)
        ).delete()
        
        rateios_criados = []
        for config in rateios_config:
            medico = config['medico']
            percentual = config['percentual']
            
            rateio = cls.objects.create(
                conta=item_despesa.conta,
                item_despesa=item_despesa,
                socio=medico,
                mes_referencia=mes_referencia.replace(day=1),
                percentual_rateio=percentual,
                created_by=usuario,
                observacoes=config.get('observacoes', '')
            )
            rateios_criados.append(rateio)
        
        return rateios_criados


class Despesa(models.Model):
    """Despesas unificadas com sistema de grupos e rateio"""
    
    class Meta:
        db_table = 'despesa'
        indexes = [
            # Consultas principais otimizadas
            models.Index(fields=['conta', 'data', 'status']),
            models.Index(fields=['item', 'data']),
            models.Index(fields=['empresa', 'socio', 'data']),
            models.Index(fields=['created_at']),
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

    # Classificação - CAMPO ELIMINADO: tipo_rateio (redundante, derivado do grupo)
    # Usar property tipo_rateio para acesso transparente
    item = models.ForeignKey(
        'ItemDespesa', 
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
        help_text="OBRIGATÓRIO para despesas SEM rateio (grupo SOCIO). "
                 "DEVE SER NULL para despesas COM rateio (grupos FOLHA/GERAL)."
    )
    
    # Dados da despesa
    data = models.DateField(null=False, verbose_name="Data da Despesa")
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=False, 
        default=0,
        verbose_name="Valor da Despesa (R$)",
        help_text="Valor total da despesa em reais"
    )
    
    # Status da despesa (NOVO CAMPO)
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Aprovação'),
        ('aprovada', 'Aprovada'),
        ('paga', 'Paga'),
        ('cancelada', 'Cancelada'),
        ('vencida', 'Vencida'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status da Despesa"
    )
    
    # Controle e auditoria (NOMENCLATURA PADRONIZADA)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='despesas_criadas',
        verbose_name="Criada Por"
    )
    possui_rateio = models.BooleanField(
        default=False,
        verbose_name="Possui Rateio",
        help_text="Indica se a despesa é rateada entre sócios/participantes"
    )

    def clean(self):
        """Validações personalizadas aprimoradas"""
        # Para despesas de sócio, sócio é obrigatório
        if self.tipo_rateio == self.Tipo_t.SEM_RATEIO:
            if not self.socio:
                raise ValidationError({
                    'socio': 'Sócio é obrigatório para despesas sem rateio (grupo SOCIO).'
                })
        
        # Para despesas com rateio, sócio deve estar vazio
        elif self.tipo_rateio == self.Tipo_t.COM_RATEIO:
            if self.socio:
                raise ValidationError({
                    'socio': 'Sócio deve ser vazio para despesas com rateio (grupos FOLHA/GERAL).'
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
        # Validações antes de salvar (tipo_rateio agora é property derivada)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.item.grupo.codigo}] {self.item.descricao} - {self.data}"
    
    # ===============================
    # PROPERTIES DERIVADAS (substituem campo eliminado)
    # ===============================
    
    @property
    def tipo_rateio(self):
        """Tipo de rateio derivado do grupo do item (substitui campo eliminado)"""
        if not self.item or not self.item.grupo:
            return None
        return self.item.grupo.tipo_rateio
    
    @property
    def grupo(self):
        """Acesso rápido ao grupo da despesa"""
        return self.item.grupo if self.item else None
    
    @property
    def pode_ser_rateada(self):
        """Verifica se a despesa pode ser rateada"""
        return self.tipo_rateio == self.Tipo_t.COM_RATEIO
    
    @property
    def eh_despesa_socio(self):
        """Verifica se é despesa de sócio"""
        return self.tipo_rateio == self.Tipo_t.SEM_RATEIO
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado em real brasileiro"""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def calcular_rateio_automatico(self):
        """
        Calcula rateio automático usando o valor da própria despesa
        
        Returns:
            list: Lista de dicts com rateio por médico
        """
        return self.calcular_rateio_dinamico()
    
    def obter_total_rateado(self):
        """
        Calcula o total que seria rateado baseado na configuração atual
        
        Returns:
            Decimal: Total dos rateios calculados
        """
        rateios = self.calcular_rateio_dinamico()
        return sum(rateio['valor_rateio'] for rateio in rateios)
    
    def criar_rateio_automatico(self, usuario=None):
        """
        MÉTODO DESABILITADO: Sistema simplificado - rateios são apenas consultados
        
        No sistema simplificado:
        1. Configuração: ItemDespesaRateioMensal define como ratear
        2. Execução: Não há persistência de rateios por despesa
        3. Consulta: Rateios são calculados dinamicamente quando necessário
        
        Para obter rateio de uma despesa, use:
        ItemDespesaRateioMensal.objects.filter(
            item_despesa=self.item,
            mes_referencia=self.data.replace(day=1),
            ativo=True
        )
        
        Benefícios desta abordagem:
        - Elimina redundância de dados
        - Evita inconsistências entre configuração e execução  
        - Simplifica manutenção do sistema
        - Rateios sempre atualizados conforme configuração atual
        """
        raise NotImplementedError(
            "Sistema simplificado: Use ItemDespesaRateioMensal para consultar "
            "configurações de rateio. Não há persistência de rateios por despesa."
        )
    
    def criar_lancamentos_financeiros(self, usuario=None):
        """
        MÉTODO DESABILITADO: Sistema manual simplificado
        
        No sistema simplificado, lançamentos financeiros devem ser feitos
        manualmente pela contabilidade, sem automação de rateios.
        
        Fluxo recomendado:
        1. Contabilidade configura ItemDespesaRateioMensal por mês
        2. Despesas são lançadas e classificadas por item
        3. Relatórios mostram rateios calculados dinamicamente
        4. Lançamentos financeiros individuais são feitos manualmente
        
        Esta abordagem garante:
        - Controle total da contabilidade sobre lançamentos
        - Auditabilidade completa de todas as operações
        - Flexibilidade para ajustes e correções
        - Eliminação de automação que pode gerar inconsistências
        """
        raise NotImplementedError(
            "Sistema manual: Lançamentos devem ser feitos manualmente pela contabilidade. "
            "Use relatórios de rateio dinâmicos como base para os lançamentos."
        )
    
    def obter_configuracao_rateio(self):
        """
        Obtém a configuração de rateio para esta despesa
        
        Returns:
            QuerySet: Configurações de rateio do item no mês da despesa
        """
        if not self.pode_ser_rateada:
            return ItemDespesaRateioMensal.objects.none()
        
        mes_referencia = self.data.replace(day=1)
        return ItemDespesaRateioMensal.objects.filter(
            item_despesa=self.item,
            mes_referencia=mes_referencia,
            ativo=True
        ).select_related('socio__pessoa')
    
    def calcular_rateio_dinamico(self, valor_despesa=None):
        """
        Calcula rateio dinâmico baseado na configuração mensal percentual
        
        Args:
            valor_despesa: Valor total da despesa para calcular rateios.
                          Se não informado, usa self.valor
            
        Returns:
            list: Lista de dicts com rateio por médico
        """
        if not self.pode_ser_rateada:
            return []
        
        # Usar valor da despesa se não foi passado como parâmetro
        if valor_despesa is None:
            valor_despesa = self.valor
        
        if not valor_despesa or valor_despesa <= 0:
            return []
        
        configuracoes = self.obter_configuracao_rateio()
        rateios_calculados = []
        
        for config in configuracoes:
            if config.percentual_rateio:
                valor_rateio = valor_despesa * (config.percentual_rateio / 100)
                rateios_calculados.append({
                    'socio': config.socio,
                    'percentual': config.percentual_rateio,
                    'valor_rateio': valor_rateio,
                    'observacoes': config.observacoes
                })
        
        return rateios_calculados
    
    def tem_configuracao_rateio(self):
        """Verifica se existe configuração de rateio para esta despesa"""
        return self.obter_configuracao_rateio().exists()
    
    @property
    def medicos_participantes_rateio(self):
        """Lista de médicos que participam do rateio desta despesa"""
        if not self.pode_ser_rateada:
            return []
        
        return [config.socio for config in self.obter_configuracao_rateio()]
