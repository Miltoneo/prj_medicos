
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .base import SaaSBaseModel, Empresa, Socio

from django.utils.translation import gettext_lazy as _

# MODELO ABSTRATO DE AUDITORIA
class AuditoriaModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_criados",
        verbose_name="Criado Por"
    )

    class Meta:
        abstract = True



TIPO_DESPESA_COM_RATEIO = 1
TIPO_DESPESA_SEM_RATEIO = 2

GRUPO_ITEM_COM_RATEIO = 1
GRUPO_ITEM_SEM_RATEIO = 2


class GrupoDespesa(AuditoriaModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='grupos_despesa',
        verbose_name="Empresa/Associação",
        help_text="Empresa ou associação responsável pelo grupo de despesa",
        null=False,
        blank=False
    )
    """Grupos de despesas para organização contábil"""
    
    class Meta:
        db_table = 'despesa_grupo'
        unique_together = ('codigo',)
        verbose_name = "Grupo de Despesa"
        verbose_name_plural = "Grupos de Despesas"
    # ...
    
    class Tipo_t(models.IntegerChoices):
        COM_RATEIO = GRUPO_ITEM_COM_RATEIO, "COM RATEIO"
        SEM_RATEIO = GRUPO_ITEM_SEM_RATEIO, "SEM RATEIO"

    codigo = models.CharField(max_length=20, null=False)
    descricao = models.CharField(max_length=255, null=False, default="")
    tipo_rateio = models.PositiveSmallIntegerField(
        choices=Tipo_t.choices,
        default=Tipo_t.COM_RATEIO
    )

    # campos de auditoria herdados de AuditoriaModel

    def __str__(self):
        return f"{self.codigo}"


class ItemDespesa(AuditoriaModel):
    """Itens específicos de despesas dentro de cada grupo"""
    
    class Meta:
        db_table = 'despesa_item'
        unique_together = ('grupo_despesa', 'codigo')
        verbose_name = "Item de Despesa"
        verbose_name_plural = "Itens de Despesas"
    # ...
    grupo_despesa = models.ForeignKey(
        GrupoDespesa,
        on_delete=models.CASCADE,
        related_name="itens_despesa",
        verbose_name="Grupo de Despesa",
        help_text="Grupo ao qual este item pertence",
        null=True,
        blank=True
    )
    codigo = models.CharField(max_length=20, null=False, verbose_name="Código", help_text="Código do item dentro do grupo")
    descricao = models.CharField(max_length=255, null=False, default="", verbose_name="Descrição", help_text="Descrição detalhada do item de despesa")

    # campos de auditoria herdados de AuditoriaModel


    @property
    def permite_rateio(self):
        """Verifica se o item permite rateio baseado no grupo (COM RATEIO)"""
        return self.grupo_despesa and self.grupo_despesa.tipo_rateio == self.grupo_despesa.Tipo_t.COM_RATEIO

    @property
    def codigo_completo(self):
        """Retorna código completo no formato GRUPO.ITEM"""
        if self.grupo_despesa:
            return f"{self.grupo_despesa.codigo}.{self.codigo}"
        return self.codigo

    def __str__(self):
        if self.grupo_despesa:
            return f"{self.grupo_despesa.codigo} {self.descricao}"
        return self.descricao


class ItemDespesaRateioMensal(AuditoriaModel):
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
        unique_together = ('item_despesa', 'socio', 'data_referencia')
        verbose_name = "Rateio Mensal de Item de Despesa"
        verbose_name_plural = "Rateios Mensais de Itens de Despesa"
        indexes = [
            models.Index(fields=['data_referencia', 'item_despesa']),
            models.Index(fields=['socio', 'data_referencia']),
            models.Index(fields=['item_despesa', 'ativo']),
            models.Index(fields=['item_despesa', 'data_referencia', 'ativo']),
        ]
    # ...
    
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
        related_name='rateios_mensais_despesa',
        verbose_name="Médico/Sócio",
        help_text="Médico que participará do rateio"
    )
    
    # Data de referência (mês/ano)
    data_referencia = models.DateField(
        verbose_name="Data de Referência (Mês/Ano)",
        help_text="Data no formato YYYY-MM-01 (primeiro dia do mês). Define o período em que esta configuração de rateio será aplicada."
    )
    
    # Valor de rateio percentual
    percentual_rateio = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Percentual de Rateio (%)",
        help_text="Percentual que este médico deve pagar deste item (0-100%). A soma de todos os médicos deve ser 100%."
    )
    
    # Controle
    ativo = models.BooleanField(
        default=True, 
        verbose_name="Ativo",
        help_text="Se este rateio está ativo para o período"
    )
    # campos de auditoria herdados de AuditoriaModel
    
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações",
        help_text="Observações sobre este rateio específico. Ex: 'Sala maior', 'Meio período', 'Acordo especial', etc. Importante para justificar percentuais diferenciados."
    )

    def clean(self):
        """
        Validações personalizadas para garantir consistência do rateio percentual
        """
        # Verificar se o percentual de rateio foi informado
        if self.percentual_rateio is None:
            raise ValidationError({
                'percentual_rateio': 'Percentual de rateio é obrigatório'
            })
        # Verificar se o percentual está no range válido (0-100%)
        if self.percentual_rateio < 0 or self.percentual_rateio > 100:
            raise ValidationError({
                'percentual_rateio': 'Percentual deve estar entre 0 e 100%'
            })
        # Verificar se o item permite rateio (grupo com tipo_rateio=COM_RATEIO)
        if self.item_despesa and (
            not self.item_despesa.grupo_despesa or
            self.item_despesa.grupo_despesa.tipo_rateio != self.item_despesa.grupo_despesa.Tipo_t.COM_RATEIO
        ):
            raise ValidationError({
                'item_despesa': (
                    f'O item "{self.item_despesa.descricao}" não permite rateio. '
                    f'Apenas itens de grupos COM RATEIO permitem rateio.'
                )
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
        if self.data_referencia:
            self.data_referencia = self.data_referencia.replace(day=1)
        
        # ajuste de conta removido
        
        # Executar todas as validações antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        nome = getattr(getattr(self.socio, 'pessoa', None), 'name', str(self.socio))
        return (
            f"{self.item_despesa.codigo_completo} - "
            f"{nome} - "
            f"{self.percentual_rateio}% "
            f"({self.data_referencia.strftime('%m/%Y')})"
        )
    
    @property
    def mes_ano_formatado(self):
        """Retorna o mês/ano formatado"""
        return self.data_referencia.strftime('%m/%Y')
    
    @property
    def valor_rateio_display(self):
        """Retorna o percentual formatado"""
        return f"{self.percentual_rateio:.2f}%"
    
    @classmethod
    def obter_rateio_para_despesa(cls, item_despesa, socio, data_despesa):
        """
        Obtém o rateio para um item/sócio em uma data específica.
        Se não existir para o mês de competência, busca o mês anterior imediato.
        Se encontrar, copia para o mês de competência para todos os sócios do item.
        Se não houver nenhum anterior, cria rateio zerado para todos os sócios do item.
        """
        from django.db import transaction
        data_referencia = data_despesa.replace(day=1)
        try:
            return cls.objects.get(
                item_despesa=item_despesa,
                socio=socio,
                data_referencia=data_referencia,
                ativo=True
            )
        except cls.DoesNotExist:
            # Buscar mês anterior imediato com rateio
            anterior = cls.objects.filter(
                item_despesa=item_despesa,
                socio=socio,
                data_referencia__lt=data_referencia,
                ativo=True
            ).order_by('-data_referencia').first()
            if anterior:
                # Copia todos os rateios do mês anterior para o mês de competência
                with transaction.atomic():
                    anteriores = cls.objects.filter(
                        item_despesa=item_despesa,
                        data_referencia=anterior.data_referencia,
                        ativo=True
                    )
                    novos = []
                    for r in anteriores:
                        novo, created = cls.objects.get_or_create(
                            item_despesa=r.item_despesa,
                            socio=r.socio,
                            data_referencia=data_referencia,
                            defaults={
                                'percentual_rateio': r.percentual_rateio,
                                'ativo': True,
                                'created_by': r.created_by,
                                'observacoes': f'Rateio copiado automaticamente de {anterior.data_referencia.strftime("%m/%Y")}'
                            }
                        )
                        novos.append(novo)
                # Retorna o rateio recém-copiado para o sócio
                return cls.objects.get(
                    item_despesa=item_despesa,
                    socio=socio,
                    data_referencia=data_referencia,
                    ativo=True
                )
            else:
                # Não existe rateio anterior: cria zerado para todos os sócios do item
                from medicos.models.base import Socio
                empresa = item_despesa.grupo_despesa.empresa
                socios = Socio.objects.filter(empresa=empresa, ativo=True)
                with transaction.atomic():
                    for s in socios:
                        cls.objects.get_or_create(
                            item_despesa=item_despesa,
                            socio=s,
                            data_referencia=data_referencia,
                            defaults={
                                'percentual_rateio': 0,
                                'ativo': True,
                                'observacoes': 'Rateio zerado criado automaticamente'
                            }
                        )
                return cls.objects.get(
                    item_despesa=item_despesa,
                    socio=socio,
                    data_referencia=data_referencia,
                    ativo=True
                )
    
    @classmethod
    def validar_rateios_mes(cls, item_despesa, data_referencia):
        """
        Valida se a configuração de rateios percentuais para um item em um mês específico está correta
        """
        rateios = cls.objects.filter(
            item_despesa=item_despesa,
            data_referencia=data_referencia,
            ativo=True
        )
        
        # Verificar se os percentuais somam 100% usando Decimal para precisão
        total_percentual = sum(
            Decimal(str(r.percentual_rateio or 0)) for r in rateios
        )
        
        return {
            'valido': abs(total_percentual - Decimal('100')) < Decimal('0.01'),
            'total_percentual': float(total_percentual),  # Converte para float para compatibilidade
            'total_rateios': rateios.count(),
            'rateios': list(rateios)
        }
    
    @classmethod
    def criar_rateio_igualitario(cls, item_despesa, medicos_lista, data_referencia, usuario=None):
        """
        Cria rateio igualitário entre uma lista de médicos para um item de despesa
        
        Args:
            item_despesa: Instância do ItemDespesa
            medicos_lista: Lista de instâncias de Socio
            data_referencia: Data do mês de referência
            usuario: Usuário que está criando o rateio
        
        Returns:
            list: Lista dos rateios criados
        """
        if not medicos_lista:
            raise ValidationError("Lista de médicos não pode estar vazia")
        
        # Calcular percentual igual para todos usando Decimal
        num_medicos = len(medicos_lista)
        percentual_por_medico = (Decimal('100') / Decimal(str(num_medicos))).quantize(Decimal('0.01'))
        
        # Limpar rateios existentes para este item/mês
        cls.objects.filter(
            item_despesa=item_despesa,
            data_referencia=data_referencia.replace(day=1)
        ).delete()
        
        rateios_criados = []
        for medico in medicos_lista:
            rateio = cls.objects.create(
                item_despesa=item_despesa,
                socio=medico,
                data_referencia=data_referencia.replace(day=1),
                percentual_rateio=percentual_por_medico,
                created_by=usuario,
                observacoes=f'Rateio igualitário entre {len(medicos_lista)} médicos'
            )
            rateios_criados.append(rateio)
        
        return rateios_criados
    
    @classmethod
    def criar_rateio_por_percentuais(cls, item_despesa, rateios_config, data_referencia, usuario=None):
        """
        Cria rateio baseado em percentuais específicos
        
        Args:
            item_despesa: Instância do ItemDespesa
            rateios_config: Lista de dicts com 'medico' e 'percentual'
            data_referencia: Data do mês de referência
            usuario: Usuário que está criando o rateio
        
        Returns:
            list: Lista dos rateios criados
        """
        # Validar que o total dos percentuais seja exatamente 100%
        total_percentual = sum(Decimal(str(config['percentual'])) for config in rateios_config)
        if abs(total_percentual - Decimal('100')) > Decimal('0.01'):
            raise ValidationError(f'Total dos percentuais ({total_percentual}%) deve ser exatamente 100%')
        
        # Limpar rateios existentes
        cls.objects.filter(
            item_despesa=item_despesa,
            data_referencia=data_referencia.replace(day=1)
        ).delete()
        
        rateios_criados = []
        for config in rateios_config:
            medico = config['medico']
            percentual = config['percentual']
            
            rateio = cls.objects.create(
                item_despesa=item_despesa,
                socio=medico,
                data_referencia=data_referencia.replace(day=1),
                percentual_rateio=percentual,
                created_by=usuario,
                observacoes=config.get('observacoes', '')
            )
            rateios_criados.append(rateio)
        
        return rateios_criados



# ===============================
# ESPECIALIZAÇÃO: DESPESA BASE, RATEADA E DE SÓCIO
# ===============================

class DespesaBase(AuditoriaModel):
    """Base abstrata para despesas"""
    item_despesa = models.ForeignKey(
        'ItemDespesa',
        on_delete=models.PROTECT,
        related_name="%(class)s_set",
        verbose_name="Item de Despesa",
        help_text="Item de despesa relacionado a esta despesa",
        null=True,
        blank=True
    )
    # ...
    data = models.DateField(null=False, verbose_name="Data da Despesa")
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        verbose_name="Valor da Despesa",
        help_text="Valor total da despesa"
    )
    possui_rateio = models.BooleanField(
        default=False,
        verbose_name="Possui Rateio",
        help_text="Indica se a despesa é rateada entre sócios/participantes"
    )

    class Meta:
        abstract = True

    def __str__(self):
        grupo = getattr(getattr(self.item_despesa, 'grupo_despesa', None), 'codigo', '-')
        descricao = getattr(self.item_despesa, 'descricao', '-')
        empresa = getattr(getattr(self.item_despesa, 'grupo_despesa', None), 'empresa', None)
        empresa_nome = getattr(empresa, 'nome_fantasia', getattr(empresa, 'name', '-')) if empresa else '-'
        return f"[{grupo}] {descricao} - {empresa_nome} - {self.data}"

    @property
    def empresa(self):
        if self.item_despesa and self.item_despesa.grupo_despesa:
            return self.item_despesa.grupo_despesa.empresa
        return None

class DespesaRateada(DespesaBase):
    """Despesas FOLHA/GERAL - COM RATEIO (sem sócio)"""
    class Meta:
        db_table = 'despesa_rateada'
        verbose_name = _(u"Despesa Rateada")
        verbose_name_plural = _(u"Despesas Rateadas")
        indexes = [
            models.Index(fields=['item_despesa', 'data']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        # Só permite itens cujo grupo tem tipo COM_RATEIO
        if self.item_despesa and self.item_despesa.grupo_despesa:
            grupo = self.item_despesa.grupo_despesa
            from medicos.models.despesas import GrupoDespesa
            if grupo.tipo_rateio != GrupoDespesa.Tipo_t.COM_RATEIO:
                raise ValidationError({'item_despesa': 'Para despesas rateadas, o grupo do item deve ser do tipo COM RATEIO.'})

    @property
    def pode_ser_rateada(self):
        return True

    def obter_configuracao_rateio(self):
        if not self.pode_ser_rateada:
            return ItemDespesaRateioMensal.objects.none()
        data_referencia = self.data.replace(day=1)
        return ItemDespesaRateioMensal.objects.filter(
            item_despesa=self.item_despesa,
            data_referencia=data_referencia,
            ativo=True
        ).select_related('socio__pessoa')

    def calcular_rateio_dinamico(self, valor_despesa=None):
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
        return self.obter_configuracao_rateio().exists()

    @property
    def medicos_participantes_rateio(self):
        return [config.socio for config in self.obter_configuracao_rateio()]

class DespesaSocio(DespesaBase):
    """Despesas SEM RATEIO (com sócio obrigatório)"""
    socio = models.ForeignKey(
        Socio,
        on_delete=models.CASCADE,
        related_name='despesas_socio',
        verbose_name="Sócio Responsável",
        help_text="Sócio responsável pela despesa"
    )

    class Meta:
        db_table = 'despesa_socio'
        verbose_name = _(u"Despesa de Sócio")
        verbose_name_plural = _(u"Despesas de Sócio")
        indexes = [
            models.Index(fields=['item_despesa', 'data']),
            models.Index(fields=['socio', 'data']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        # Só permite itens de grupo SEM RATEIO
        if self.item_despesa and self.item_despesa.grupo_despesa and self.item_despesa.grupo_despesa.tipo_rateio != self.item_despesa.grupo_despesa.Tipo_t.SEM_RATEIO:
            raise ValidationError({'item_despesa': 'Para despesas de sócio, o item deve ser de grupo SEM RATEIO.'})
    def __str__(self):
        socio_nome = getattr(getattr(self.socio, 'pessoa', None), 'name', str(self.socio))
        item = self.item_despesa.descricao if self.item_despesa else '-'
        return f"{socio_nome} - {item} - {self.data}"

