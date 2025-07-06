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
    Configuração de rateio mensal para itens de despesa entre médicos/sócios
    
    Este modelo é fundamental para o sistema de gestão financeira, definindo como
    os custos operacionais da clínica/associação médica devem ser distribuídos
    entre os médicos sócios a cada mês.
    
    FUNCIONALIDADES PRINCIPAIS:
    
    1. RATEIO POR PERCENTUAL (mais comum):
       - Cada médico tem um percentual fixo do custo (ex: Dr. A: 40%, Dr. B: 35%, Dr. C: 25%)
       - A soma de todos os percentuais deve ser exatamente 100%
       - Ideal para despesas fixas como aluguel, energia, telefone
    
    2. RATEIO POR VALOR FIXO:
       - Cada médico paga um valor específico independente do total da despesa
       - Útil para despesas com valores conhecidos por médico (ex: mensalidade CRM)
       - O total pode não corresponder a 100% do valor da despesa
    
    3. RATEIO PROPORCIONAL (automático):
       - O sistema calcula automaticamente baseado em critérios definidos
       - Ex: proporcional ao faturamento, número de consultas, etc.
       - Flexível para regras de negócio complexas
    
    FLUXO DE FUNCIONAMENTO:
    
    1. Configuração mensal: Define-se como cada item será rateado no mês
    2. Lançamento de despesas: Despesas são classificadas por item/grupo
    3. Processamento de rateio: Sistema distribui valores conforme configuração
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
    
    Mensalidade CRM:
    - Dr. João: R$ 450,00 (valor fixo)
    - Dr. Maria: R$ 450,00 (valor fixo)
    - Dr. Pedro: R$ 450,00 (valor fixo)
    
    Material de consumo:
    - Rateio proporcional baseado no número de atendimentos do mês
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
    
    # Tipos de rateio
    TIPO_RATEIO_CHOICES = [
        ('percentual', 'Por Percentual - Cada médico tem uma % fixa do total da despesa'),
        ('valor_fixo', 'Por Valor Fixo - Cada médico paga um valor específico independente do total'),
        ('proporcional', 'Proporcional Automático - Sistema calcula baseado em critérios definidos'),
    ]
    
    tipo_rateio = models.CharField(
        max_length=20,
        choices=TIPO_RATEIO_CHOICES,
        default='percentual',
        verbose_name="Tipo de Rateio",
        help_text="Define como será calculado o rateio: por percentual fixo (mais comum), por valor fixo, ou proporcional automático"
    )
    
    # Valores de rateio
    percentual_rateio = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Percentual de Rateio (%)",
        help_text="Percentual que este médico deve pagar deste item (0-100%). Usado quando tipo_rateio = 'percentual'. A soma de todos os médicos deve ser 100%."
    )
    
    valor_fixo_rateio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Fixo de Rateio (R$)",
        help_text="Valor fixo que este médico deve pagar independente do total da despesa. Usado quando tipo_rateio = 'valor_fixo'. Ex: mensalidades, taxas individuais."
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
        Validações personalizadas para garantir consistência do rateio
        
        Validações implementadas:
        1. Obrigatoriedade de valores conforme tipo de rateio escolhido
        2. Limites válidos para percentuais (0-100%)
        3. Valores não negativos para rateios fixos
        4. Verificação se o item permite rateio (apenas grupos FOLHA e GERAL)
        5. Consistência entre sócio e item (mesma conta/empresa)
        """
        # Verificar se pelo menos um tipo de rateio foi definido corretamente
        if self.tipo_rateio == 'percentual' and not self.percentual_rateio:
            raise ValidationError({
                'percentual_rateio': 'Percentual de rateio é obrigatório quando tipo é "Por Percentual"'
            })
        
        if self.tipo_rateio == 'valor_fixo' and not self.valor_fixo_rateio:
            raise ValidationError({
                'valor_fixo_rateio': 'Valor fixo é obrigatório quando tipo é "Por Valor Fixo"'
            })
        
        # Verificar se o percentual está no range válido (0-100%)
        if self.percentual_rateio is not None:
            if self.percentual_rateio < 0 or self.percentual_rateio > 100:
                raise ValidationError({
                    'percentual_rateio': 'Percentual deve estar entre 0 e 100%'
                })
        
        # Verificar se o valor fixo não é negativo
        if self.valor_fixo_rateio is not None and self.valor_fixo_rateio < 0:
            raise ValidationError({
                'valor_fixo_rateio': 'Valor fixo não pode ser negativo'
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
        3. Limpa campos não utilizados baseado no tipo de rateio selecionado
        4. Executa todas as validações antes de salvar
        """
        # Normalizar a data para o primeiro dia do mês (formato padrão do sistema)
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        
        # Garantir que a conta seja consistente (tenant isolation)
        if self.item_despesa:
            self.conta = self.item_despesa.conta
        
        # Limpar campos não utilizados baseado no tipo de rateio
        # Isso evita inconsistências e garante que apenas o campo relevante tenha valor
        if self.tipo_rateio == 'percentual':
            # Para rateio por percentual, limpar valor fixo
            self.valor_fixo_rateio = None
        elif self.tipo_rateio == 'valor_fixo':
            # Para rateio por valor fixo, limpar percentual
            self.percentual_rateio = None
        elif self.tipo_rateio == 'proporcional':
            # Para rateio proporcional, os valores podem ser calculados dinamicamente
            # Mantém os campos para permitir cache de cálculos automáticos
            pass
        
        # Executar todas as validações antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.tipo_rateio == 'percentual' and self.percentual_rateio:
            valor_display = f"{self.percentual_rateio}%"
        elif self.tipo_rateio == 'valor_fixo' and self.valor_fixo_rateio:
            valor_display = f"R$ {self.valor_fixo_rateio:.2f}"
        else:
            valor_display = "Proporcional"
            
        return (
            f"{self.item_despesa.codigo_completo} - "
            f"{self.socio.pessoa.name} - "
            f"{valor_display} "
            f"({self.mes_referencia.strftime('%m/%Y')})"
        )
    
    @property
    def mes_ano_formatado(self):
        """Retorna o mês/ano formatado"""
        return self.mes_referencia.strftime('%m/%Y')
    
    @property
    def valor_rateio_display(self):
        """Retorna o valor do rateio formatado conforme o tipo"""
        if self.tipo_rateio == 'percentual' and self.percentual_rateio is not None:
            return f"{self.percentual_rateio:.2f}%"
        elif self.tipo_rateio == 'valor_fixo' and self.valor_fixo_rateio is not None:
            return f"R$ {self.valor_fixo_rateio:.2f}"
        elif self.tipo_rateio == 'proporcional':
            return "Proporcional"
        else:
            return "Não definido"
    
    @property
    def percentual_formatado(self):
        """Retorna o percentual formatado"""
        return f"{self.percentual}%"

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
        Valida se a configuração de rateios para um item em um mês específico está correta
        """
        rateios = cls.objects.filter(
            item_despesa=item_despesa,
            mes_referencia=mes_referencia,
            ativo=True
        )
        
        # Para rateios por percentual, verificar se somam 100%
        rateios_percentual = rateios.filter(tipo_rateio='percentual')
        total_percentual = sum(r.percentual_rateio or 0 for r in rateios_percentual)
        
        # Para rateios por valor fixo, só verificar se não são negativos
        rateios_valor_fixo = rateios.filter(tipo_rateio='valor_fixo')
        valores_validos = all(r.valor_fixo_rateio and r.valor_fixo_rateio >= 0 for r in rateios_valor_fixo)
        
        return {
            'valido': (
                (not rateios_percentual.exists() or abs(total_percentual - 100) < 0.01) and
                valores_validos
            ),
            'total_percentual': total_percentual,
            'total_rateios': rateios.count(),
            'tipos_rateio': list(rateios.values_list('tipo_rateio', flat=True).distinct()),
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
                tipo_rateio='percentual',
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
                tipo_rateio='percentual',
                percentual_rateio=percentual,
                created_by=usuario,
                observacoes=config.get('observacoes', '')
            )
            rateios_criados.append(rateio)
        
        return rateios_criados


class TemplateRateioMensalDespesas(models.Model):
    """Template/configuração geral de rateio mensal para despesas"""
    
    class Meta:
        db_table = 'configuracao_rateio_mensal'
        unique_together = ('conta', 'mes_referencia')
        verbose_name = "Template de Rateio Mensal de Despesas"
        verbose_name_plural = "Templates de Rateio Mensal de Despesas"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='templates_rateio_despesas'
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
        related_name='templates_rateio_criados',
        verbose_name="Criada Por"
    )
    finalizada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates_rateio_finalizados',
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
        
        percentuais_anteriores = ItemDespesaRateioMensal.objects.filter(
            conta=self.conta,
            mes_referencia=mes_anterior,
            ativo=True
        )
        
        novos_percentuais = []
        for perc_anterior in percentuais_anteriores:
            # Verificar se já não existe para este mês
            existe = ItemDespesaRateioMensal.objects.filter(
                conta=self.conta,
                item_despesa=perc_anterior.item_despesa,
                socio=perc_anterior.socio,
                mes_referencia=self.mes_referencia
            ).exists()
            
            if not existe:
                novo_percentual = ItemDespesaRateioMensal(
                    conta=self.conta,
                    item_despesa=perc_anterior.item_despesa,
                    socio=perc_anterior.socio,
                    mes_referencia=self.mes_referencia,
                    tipo_rateio=perc_anterior.tipo_rateio,
                    percentual_rateio=perc_anterior.percentual_rateio,
                    valor_fixo_rateio=perc_anterior.valor_fixo_rateio,
                    created_by=perc_anterior.created_by,
                    observacoes=f"Copiado do mês {mes_anterior.strftime('%m/%Y')}"
                )
                novos_percentuais.append(novo_percentual)
        
        if novos_percentuais:
            ItemDespesaRateioMensal.objects.bulk_create(novos_percentuais)
        
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
        percentuais = ItemDespesaRateioMensal.objects.filter(
            item_despesa=self.item,
            mes_referencia=mes_referencia,
            ativo=True
        ).select_related('socio')
        
        if not percentuais.exists():
            raise ValidationError(
                f"Não há rateios cadastrados para o item "
                f"'{self.item.descricao}' no mês {mes_referencia.strftime('%m/%Y')}"
            )
        
        # Para rateios por percentual, verificar se a soma é válida
        rateios_percentual = percentuais.filter(tipo_rateio='percentual')
        if rateios_percentual.exists():
            total_percentual = sum(p.percentual_rateio or 0 for p in rateios_percentual)
            # Verificar se há outros tipos de rateio misturados
            if percentuais.exclude(tipo_rateio='percentual').exists():
                # Mix de tipos - validar separadamente
                pass
            else:
                # Só percentuais - deve somar 100%
                if abs(total_percentual - 100) > 0.01:
                    raise ValidationError(
                        f"A soma dos percentuais para o item '{self.item.descricao}' "
                        f"no mês {mes_referencia.strftime('%m/%Y')} é {total_percentual:.2f}%. "
                        f"Deve ser exatamente 100%."
                    )
        
        # Criar os rateios
        rateios_criados = []
        for rateio_mensal in percentuais:
            # Calcular valor baseado no tipo de rateio
            if rateio_mensal.tipo_rateio == 'percentual' and rateio_mensal.percentual_rateio:
                valor_calculado = self.valor * (rateio_mensal.percentual_rateio / 100)
                percentual_aplicado = rateio_mensal.percentual_rateio
            elif rateio_mensal.tipo_rateio == 'valor_fixo' and rateio_mensal.valor_fixo_rateio:
                valor_calculado = rateio_mensal.valor_fixo_rateio
                percentual_aplicado = (valor_calculado / self.valor) * 100 if self.valor > 0 else 0
            else:
                # Tipo proporcional ou valores não definidos - calcular igualmente
                valor_calculado = self.valor / percentuais.count()
                percentual_aplicado = 100 / percentuais.count()
            
            rateio = DespesaSocioRateio(
                conta=self.conta,
                despesa=self,
                socio=rateio_mensal.socio,
                percentual=percentual_aplicado,
                vl_rateio=valor_calculado,
                observacoes=f"Rateio {rateio_mensal.get_tipo_rateio_display().lower()}: {rateio_mensal.valor_rateio_display}"
            )
            rateio.save()
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


class DespesaSocioRateio(models.Model):
    """Rateio de despesas entre sócios/médicos"""
    
    class Meta:
        db_table = 'despesa_socio_rateio'
        unique_together = ('despesa', 'socio')  # Evita rateio duplicado
        verbose_name = "Rateio de Despesa"
        verbose_name_plural = "Rateios de Despesas"

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='rateios_socios_despesa', 
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
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre este rateio específico"
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
