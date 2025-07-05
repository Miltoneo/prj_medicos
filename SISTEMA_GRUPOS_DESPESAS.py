# ================================
# SISTEMA DE AGRUPAMENTO DE DESPESAS ATUALIZADO
# Despesas organizadas por grupos: Folha, Geral, Sócio
# ================================

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

#--------------------------------------------------------------
# GRUPOS DE DESPESAS
class GrupoDespesa(models.Model):
    """Grupos para organização das despesas"""
    
    TIPO_GRUPO_CHOICES = [
        ('folha', 'Despesas de Folha'),
        ('geral', 'Despesas Gerais'), 
        ('socio', 'Despesas de Sócio'),
    ]
    
    # Identificação
    codigo = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Código do Grupo",
        help_text="Ex: FOLHA, GERAL, SOCIO"
    )
    nome = models.CharField(max_length=100, verbose_name="Nome do Grupo")
    tipo_grupo = models.CharField(
        max_length=10, 
        choices=TIPO_GRUPO_CHOICES,
        verbose_name="Tipo do Grupo"
    )
    
    # Configurações de rateio
    permite_rateio = models.BooleanField(
        default=True,
        verbose_name="Permite Rateio",
        help_text="Se as despesas deste grupo podem ser rateadas"
    )
    rateio_obrigatorio = models.BooleanField(
        default=False,
        verbose_name="Rateio Obrigatório",
        help_text="Se o rateio é obrigatório para despesas deste grupo"
    )
    
    # Configuração visual
    cor_grupo = models.CharField(
        max_length=7, 
        default="#007bff",
        verbose_name="Cor do Grupo",
        help_text="Cor em hexadecimal para identificação visual"
    )
    icone = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Ícone",
        help_text="Classe do ícone FontAwesome ou Bootstrap"
    )
    
    # Controle
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=0, verbose_name="Ordem de Exibição")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'grupo_despesa'
        ordering = ['ordem_exibicao', 'nome']
        verbose_name = "Grupo de Despesa"
        verbose_name_plural = "Grupos de Despesas"
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

#--------------------------------------------------------------
# SUBGRUPOS DE DESPESAS (Categorias dentro dos grupos)
class SubgrupoDespesa(models.Model):
    """Subgrupos/categorias dentro de cada grupo de despesa"""
    
    grupo = models.ForeignKey(
        GrupoDespesa, 
        on_delete=models.CASCADE, 
        related_name='subgrupos'
    )
    
    # Identificação
    codigo = models.CharField(max_length=30, verbose_name="Código do Subgrupo")
    nome = models.CharField(max_length=100, verbose_name="Nome do Subgrupo")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    
    # Configurações contábeis
    conta_contabil = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Conta Contábil",
        help_text="Código da conta no plano de contas"
    )
    centro_custo_padrao = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Centro de Custo Padrão"
    )
    
    # Controle
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'subgrupo_despesa'
        unique_together = ['grupo', 'codigo']
        ordering = ['grupo', 'ordem_exibicao', 'nome']
        verbose_name = "Subgrupo de Despesa"
        verbose_name_plural = "Subgrupos de Despesas"
    
    def __str__(self):
        return f"{self.grupo.codigo}.{self.codigo} - {self.nome}"

#--------------------------------------------------------------
# MODELO UNIFICADO DE DESPESAS
class Despesa(AssociacaoScopedModel):
    """Modelo unificado para todas as despesas da associação"""
    
    # Classificação
    grupo = models.ForeignKey(
        GrupoDespesa, 
        on_delete=models.PROTECT,
        verbose_name="Grupo de Despesa"
    )
    subgrupo = models.ForeignKey(
        SubgrupoDespesa, 
        on_delete=models.PROTECT,
        verbose_name="Subgrupo/Categoria"
    )
    
    # Dados básicos
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    numero_documento = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Número do Documento"
    )
    fornecedor = models.CharField(max_length=255, verbose_name="Fornecedor")
    
    # Valores
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor Total"
    )
    
    # Datas
    data_documento = models.DateField(verbose_name="Data do Documento")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Data de Pagamento"
    )
    
    # Para despesas de sócio (sem rateio)
    medico_responsavel = models.ForeignKey(
        'MedicoAssociado', 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        verbose_name="Médico Responsável",
        help_text="Obrigatório apenas para despesas de sócio"
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
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ], default='pendente')
    
    # Dados contábeis
    centro_custo = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Centro de Custo"
    )
    conta_contabil = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Conta Contábil"
    )
    
    # Controle
    lancada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Lançada Por"
    )
    data_lancamento = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        db_table = 'despesa'
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        indexes = [
            models.Index(fields=['associacao', 'grupo', 'data_vencimento']),
            models.Index(fields=['associacao', 'status']),
            models.Index(fields=['medico_responsavel']),
        ]
    
    def clean(self):
        """Validações personalizadas"""
        # Para despesas de sócio, médico_responsável é obrigatório
        if self.grupo and self.grupo.tipo_grupo == 'socio':
            if not self.medico_responsavel:
                raise ValidationError({
                    'medico_responsavel': 'Médico responsável é obrigatório para despesas de sócio.'
                })
        
        # Para outros tipos, médico_responsável deve estar vazio
        elif self.grupo and self.grupo.tipo_grupo in ['folha', 'geral']:
            if self.medico_responsavel:
                raise ValidationError({
                    'medico_responsavel': 'Médico responsável deve ser vazio para despesas de folha e gerais.'
                })
        
        # Subgrupo deve pertencer ao grupo selecionado
        if self.subgrupo and self.grupo:
            if self.subgrupo.grupo != self.grupo:
                raise ValidationError({
                    'subgrupo': f'O subgrupo deve pertencer ao grupo {self.grupo.nome}.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.grupo.codigo} - {self.descricao} - R$ {self.valor}"
    
    @property
    def pode_ser_rateada(self):
        """Verifica se a despesa pode ser rateada"""
        return (
            self.grupo.permite_rateio and 
            self.grupo.tipo_grupo in ['folha', 'geral'] and
            not self.ja_rateada
        )
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado em real brasileiro"""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

#--------------------------------------------------------------
# RATEIO DE DESPESAS (Unificado)
class RateioDespesa(models.Model):
    """Rateio de despesas entre médicos associados"""
    
    despesa = models.ForeignKey(
        Despesa, 
        on_delete=models.CASCADE, 
        related_name='rateios'
    )
    medico = models.ForeignKey(
        'MedicoAssociado', 
        on_delete=models.CASCADE
    )
    
    # Valores do rateio
    percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Percentual (%)",
        help_text="Percentual da despesa que cabe a este médico"
    )
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor"
    )
    
    # Controle
    data_rateio = models.DateTimeField(auto_now_add=True)
    rateado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Rateado Por"
    )
    
    class Meta:
        db_table = 'rateio_despesa'
        unique_together = ['despesa', 'medico']
        verbose_name = "Rateio de Despesa"
        verbose_name_plural = "Rateios de Despesas"
    
    def clean(self):
        if self.percentual <= 0 or self.percentual > 100:
            raise ValidationError("Percentual deve estar entre 0.01 e 100%")
    
    def save(self, *args, **kwargs):
        # Calcular valor proporcional automaticamente
        if self.despesa and self.percentual:
            self.valor = self.despesa.valor * (self.percentual / 100)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medico.nome} - {self.percentual}% - R$ {self.valor}"

#--------------------------------------------------------------
# DADOS INICIAIS DOS GRUPOS (para popular o banco)
GRUPOS_DESPESA_INICIAL = [
    {
        'codigo': 'FOLHA',
        'nome': 'Despesas de Folha de Pagamento',
        'tipo_grupo': 'folha',
        'permite_rateio': True,
        'rateio_obrigatorio': True,
        'cor_grupo': '#28a745',  # Verde
        'icone': 'fas fa-users',
        'ordem_exibicao': 1,
        'subgrupos': [
            {'codigo': 'SAL', 'nome': 'Salários', 'conta_contabil': '3.1.1.01'},
            {'codigo': 'ENC', 'nome': 'Encargos Sociais', 'conta_contabil': '3.1.1.02'},
            {'codigo': 'FER', 'nome': 'Férias', 'conta_contabil': '3.1.1.03'},
            {'codigo': '13º', 'nome': '13º Salário', 'conta_contabil': '3.1.1.04'},
            {'codigo': 'FGTS', 'nome': 'FGTS', 'conta_contabil': '3.1.1.05'},
            {'codigo': 'INSS', 'nome': 'INSS', 'conta_contabil': '3.1.1.06'},
            {'codigo': 'VT', 'nome': 'Vale Transporte', 'conta_contabil': '3.1.1.07'},
            {'codigo': 'VR', 'nome': 'Vale Refeição', 'conta_contabil': '3.1.1.08'},
        ]
    },
    {
        'codigo': 'GERAL',
        'nome': 'Despesas Gerais da Associação',
        'tipo_grupo': 'geral',
        'permite_rateio': True,
        'rateio_obrigatorio': True,
        'cor_grupo': '#007bff',  # Azul
        'icone': 'fas fa-building',
        'ordem_exibicao': 2,
        'subgrupos': [
            {'codigo': 'ALU', 'nome': 'Aluguel', 'conta_contabil': '3.1.2.01'},
            {'codigo': 'ENE', 'nome': 'Energia Elétrica', 'conta_contabil': '3.1.2.02'},
            {'codigo': 'TEL', 'nome': 'Telefone/Internet', 'conta_contabil': '3.1.2.03'},
            {'codigo': 'MAT', 'nome': 'Material de Escritório', 'conta_contabil': '3.1.2.04'},
            {'codigo': 'LIM', 'nome': 'Limpeza', 'conta_contabil': '3.1.2.05'},
            {'codigo': 'SEG', 'nome': 'Segurança', 'conta_contabil': '3.1.2.06'},
            {'codigo': 'MAN', 'nome': 'Manutenção', 'conta_contabil': '3.1.2.07'},
            {'codigo': 'CON', 'nome': 'Contabilidade', 'conta_contabil': '3.1.2.08'},
            {'codigo': 'JUR', 'nome': 'Honorários Jurídicos', 'conta_contabil': '3.1.2.09'},
            {'codigo': 'OUT', 'nome': 'Outras Despesas Gerais', 'conta_contabil': '3.1.2.99'},
        ]
    },
    {
        'codigo': 'SOCIO',
        'nome': 'Despesas de Sócio',
        'tipo_grupo': 'socio',
        'permite_rateio': False,
        'rateio_obrigatorio': False,
        'cor_grupo': '#fd7e14',  # Laranja
        'icone': 'fas fa-user-md',
        'ordem_exibicao': 3,
        'subgrupos': [
            {'codigo': 'PRO', 'nome': 'Pró-labore', 'conta_contabil': '3.1.3.01'},
            {'codigo': 'RET', 'nome': 'Retirada de Sócio', 'conta_contabil': '3.1.3.02'},
            {'codigo': 'REE', 'nome': 'Reembolso', 'conta_contabil': '3.1.3.03'},
            {'codigo': 'ADA', 'nome': 'Adiantamento', 'conta_contabil': '3.1.3.04'},
            {'codigo': 'EQP', 'nome': 'Equipamento Pessoal', 'conta_contabil': '3.1.3.05'},
            {'codigo': 'VIA', 'nome': 'Viagem', 'conta_contabil': '3.1.3.06'},
            {'codigo': 'CUR', 'nome': 'Curso/Capacitação', 'conta_contabil': '3.1.3.07'},
            {'codigo': 'OUT', 'nome': 'Outras Despesas Pessoais', 'conta_contabil': '3.1.3.99'},
        ]
    }
]

#--------------------------------------------------------------
# FUNÇÃO PARA POPULAR DADOS INICIAIS
def criar_grupos_despesa_inicial():
    """Função para criar os grupos e subgrupos iniciais de despesas"""
    
    for grupo_data in GRUPOS_DESPESA_INICIAL:
        # Extrair subgrupos
        subgrupos_data = grupo_data.pop('subgrupos', [])
        
        # Criar ou atualizar grupo
        grupo, created = GrupoDespesa.objects.get_or_create(
            codigo=grupo_data['codigo'],
            defaults=grupo_data
        )
        
        if created:
            print(f"✓ Grupo criado: {grupo.codigo} - {grupo.nome}")
        
        # Criar subgrupos
        for subgrupo_data in subgrupos_data:
            subgrupo, sub_created = SubgrupoDespesa.objects.get_or_create(
                grupo=grupo,
                codigo=subgrupo_data['codigo'],
                defaults={
                    'nome': subgrupo_data['nome'],
                    'conta_contabil': subgrupo_data.get('conta_contabil', ''),
                }
            )
            
            if sub_created:
                print(f"  ✓ Subgrupo criado: {subgrupo.codigo} - {subgrupo.nome}")

# Para executar a criação dos dados iniciais:
# from django.core.management.base import BaseCommand
# criar_grupos_despesa_inicial()
