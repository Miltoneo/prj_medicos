from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# CONSTANTES GLOBAIS
app_name = 'medicos'

REGIME_TRIBUTACAO_COMPETENCIA = 1
REGIME_TRIBUTACAO_CAIXA = 2

NFISCAL_ALIQUOTA_CONSULTAS = 1
NFISCAL_ALIQUOTA_PLANTAO = 2
NFISCAL_ALIQUOTA_OUTROS = 3

# PERIODICIDADES DE APURAÇÃO CONFORME LEGISLAÇÃO
PERIODICIDADE_MENSAL = 'MENSAL'
PERIODICIDADE_TRIMESTRAL = 'TRIMESTRAL'

# TIPOS DE IMPOSTOS E SUAS CARACTERÍSTICAS
IMPOSTOS_INFO = {
    'ISS': {
        'periodicidade': PERIODICIDADE_MENSAL,
        'dia_vencimento': 10,  # Padrão - varia por município
        'regime_obrigatorio': REGIME_TRIBUTACAO_COMPETENCIA,
        'base_legal': 'LC 116/2003',
        'observacao': 'Sempre regime de competência, vencimento varia por município'
    },
    'PIS': {
        'periodicidade': PERIODICIDADE_MENSAL,
        'dia_vencimento': 25,
        'regime_flexivel': True,
        'base_legal': 'Lei 10.833/2003',
        'observacao': 'Pode seguir regime da empresa se receita ≤ R$ 78 milhões'
    },
    'COFINS': {
        'periodicidade': PERIODICIDADE_MENSAL,
        'dia_vencimento': 25,
        'regime_flexivel': True,
        'base_legal': 'Lei 10.833/2003',
        'observacao': 'Pode seguir regime da empresa se receita ≤ R$ 78 milhões'
    },
    'IRPJ': {
        'periodicidades': [PERIODICIDADE_MENSAL, PERIODICIDADE_TRIMESTRAL],
        'dia_vencimento': 'ultimo_dia_util',
        'regime_flexivel': True,
        'base_legal': 'Lei 9.430/1996',
        'observacao': 'Empresa pode optar por apuração mensal ou trimestral'
    },
    'CSLL': {
        'periodicidades': [PERIODICIDADE_MENSAL, PERIODICIDADE_TRIMESTRAL],
        'dia_vencimento': 'ultimo_dia_util',
        'regime_flexivel': True,
        'base_legal': 'Lei 9.249/1995',
        'observacao': 'Segue a mesma periodicidade escolhida para IRPJ'
    }
}

TIPO_MOVIMENTACAO_CONTA_CREDITO = 1
TIPO_MOVIMENTACAO_CONTA_DEBITO = 2

DESC_MOVIMENTACAO_CREDITO_SALDO_MES_SEGUINTE = 'CREDITO SALDO MES ANTERIOR'
DESC_MOVIMENTACAO_DEBITO_IMPOSTO_PROVISIONADOS = 'DEBITO PAGAMENTO DE IMPOSTOS '

CODIGO_GRUPO_DESPESA_GERAL = 'GERAL'
CODIGO_GRUPO_DESPESA_FOLHA = 'FOLHA'
CODIGO_GRUPO_DESPESA_SOCIO = 'SOCIO'

TIPO_DESPESA_COM_RATEIO = 1
TIPO_DESPESA_SEM_RATEIO = 2

GRUPO_ITEM_COM_RATEIO = 1
GRUPO_ITEM_SEM_RATEIO = 2

#--------------------------------------------------------------
# MANAGERS CUSTOMIZADOS PARA SAAS
#--------------------------------------------------------------
class ContaScopedManager(models.Manager):
    """Manager que filtra automaticamente por conta (tenant)"""
    def get_queryset(self):
        if hasattr(self.model, '_current_conta'):
            return super().get_queryset().filter(conta=self.model._current_conta)
        return super().get_queryset()

    def for_conta(self, conta):
        """Método para filtrar por uma conta específica"""
        return super().get_queryset().filter(conta=conta)

class CustomUserManager(UserManager):
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # Preenche username com email se não informado
        if not extra_fields.get('username'):
            extra_fields['username'] = email
        return super().create_user(email=email, password=password, **extra_fields)

#--------------------------------------------------------------
# MODELO DE USUÁRIO CUSTOMIZADO
class CustomUser(AbstractUser):
    objects = CustomUserManager()  # Usa o manager customizado
    class Meta:
        db_table = 'customUser'

    email = models.EmailField('e-mail address', unique=True)
    invite_token = models.CharField('Token de convite', max_length=64, blank=True, null=True)
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=False,
        verbose_name='username'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

#--------------------------------------------------------------
# MODELO DE CONTA (substitui Organization)
class Conta(models.Model):
    class Meta:
        db_table = 'conta'

    name = models.CharField(max_length=255, unique=True)
    cnpj = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_criadas',
        verbose_name="Criado Por"
    )

    def __str__(self):
        return self.name

#--------------------------------------------------------------
# PREFERÊNCIAS DA CONTA (customização por tenant)
class ContaPreferencias(models.Model):
    class Meta:
        db_table = 'conta_preferencias'
        verbose_name = "Preferências da Conta"
        verbose_name_plural = "Preferências das Contas"

    conta = models.OneToOneField(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='preferencias',
        primary_key=True
    )
    
    # Configurações de UI/UX
    tema = models.CharField(
        max_length=20, 
        choices=[
            ('claro', 'Tema Claro'),
            ('escuro', 'Tema Escuro'),
            ('auto', 'Automático')
        ], 
        default='claro',
        verbose_name="Tema da Interface"
    )
    idioma = models.CharField(
        max_length=5, 
        choices=[
            ('pt-br', 'Português (Brasil)'),
            ('en', 'English'),
            ('es', 'Español')
        ], 
        default='pt-br',
        verbose_name="Idioma"
    )
    timezone = models.CharField(
        max_length=50, 
        default='America/Sao_Paulo',
        verbose_name="Fuso Horário"
    )
    
    # Configurações de relatórios
    formato_data_padrao = models.CharField(
        max_length=20,
        choices=[
            ('dd/mm/yyyy', 'DD/MM/AAAA'),
            ('mm/dd/yyyy', 'MM/DD/AAAA'),
            ('yyyy-mm-dd', 'AAAA-MM-DD')
        ],
        default='dd/mm/yyyy',
        verbose_name="Formato de Data Padrão"
    )
    moeda_padrao = models.CharField(
        max_length=3,
        default='BRL',
        verbose_name="Moeda Padrão"
    )
    decimais_valor = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="Casas Decimais para Valores"
    )
    
    # Configurações de notificações
    notificacoes_email = models.BooleanField(
        default=True,
        verbose_name="Receber Notificações por Email"
    )
    notificacoes_vencimento = models.BooleanField(
        default=True,
        verbose_name="Alertas de Vencimento"
    )
    dias_antecedencia_vencimento = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Dias de Antecedência para Alertas"
    )
    
    # Configurações de segurança
    sessao_timeout_minutos = models.PositiveIntegerField(
        default=120,
        verbose_name="Timeout da Sessão (minutos)"
    )
    requerer_2fa = models.BooleanField(
        default=False,
        verbose_name="Exigir Autenticação Dupla (2FA)"
    )
    
    # Configurações de backup/exportação
    backup_automatico = models.BooleanField(
        default=False,
        verbose_name="Backup Automático"
    )
    frequencia_backup = models.CharField(
        max_length=10,
        choices=[
            ('diario', 'Diário'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal')
        ],
        default='semanal',
        verbose_name="Frequência do Backup"
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conta_preferencias_criadas',
        verbose_name="Criado Por"
    )

    def __str__(self):
        return f"Preferências - {self.conta.name}"

#--------------------------------------------------------------
# AUDITORIA DA CONTA (rastreamento de ações)
class ContaAuditLog(models.Model):
    class Meta:
        db_table = 'conta_audit_log'
        verbose_name = "Log de Auditoria da Conta"
        verbose_name_plural = "Logs de Auditoria das Contas"
        indexes = [
            models.Index(fields=['conta', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['acao', '-timestamp']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="Usuário"
    )
    
    # Dados da ação
    acao = models.CharField(
        max_length=50,
        choices=[
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('create', 'Criação'),
            ('update', 'Atualização'),
            ('delete', 'Exclusão'),
            ('export', 'Exportação'),
            ('import', 'Importação'),
            ('config_change', 'Mudança de Configuração'),
            ('user_invite', 'Convite de Usuário'),
            ('user_remove', 'Remoção de Usuário'),
            ('backup', 'Backup'),
            ('restore', 'Restauração'),
        ],
        verbose_name="Ação"
    )
    objeto_tipo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Tipo do Objeto"
    )
    objeto_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID do Objeto"
    )
    objeto_nome = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome do Objeto"
    )
    
    # Detalhes da ação
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    dados_anteriores = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados Anteriores"
    )
    dados_novos = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados Novos"
    )
    
    # Metadados técnicos
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Endereço IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data/Hora"
    )
    
    def __str__(self):
        user_info = self.user.email if self.user else 'Sistema'
        return f"{self.timestamp.strftime('%d/%m/%Y %H:%M')} - {user_info} - {self.acao}"

#--------------------------------------------------------------
# MÉTRICAS DA CONTA (analytics e usage tracking)
class ContaMetrics(models.Model):
    class Meta:
        db_table = 'conta_metrics'
        verbose_name = "Métricas da Conta"
        verbose_name_plural = "Métricas das Contas"
        indexes = [
            models.Index(fields=['conta', '-data']),
            models.Index(fields=['metrica_tipo', '-data']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='metrics'
    )
    
    # Tipo da métrica
    metrica_tipo = models.CharField(
        max_length=50,
        choices=[
            ('usuarios_ativos', 'Usuários Ativos'),
            ('logins_dia', 'Logins por Dia'),
            ('relatorios_gerados', 'Relatórios Gerados'),
            ('despesas_lancadas', 'Despesas Lançadas'),
            ('receitas_lancadas', 'Receitas Lançadas'),
            ('notas_fiscais', 'Notas Fiscais'),
            ('backup_executado', 'Backup Executado'),
            ('storage_usado', 'Armazenamento Usado (MB)'),
            ('api_calls', 'Chamadas de API'),
            ('tempo_sessao_medio', 'Tempo Médio de Sessão (min)'),
        ],
        verbose_name="Tipo de Métrica"
    )
    
    # Dados da métrica
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Valor"
    )
    unidade = models.CharField(
        max_length=20,
        default='quantidade',
        verbose_name="Unidade"
    )
    
    # Período
    data = models.DateField(
        verbose_name="Data"
    )
    periodo_tipo = models.CharField(
        max_length=10,
        choices=[
            ('dia', 'Diário'),
            ('semana', 'Semanal'),
            ('mes', 'Mensal'),
            ('ano', 'Anual')
        ],
        default='dia',
        verbose_name="Tipo de Período"
    )
    
    # Metadados adicionais
    metadados = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Metadados Adicionais"
    )
    
    # Controle
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    def __str__(self):
        return f"{self.conta.name} - {self.metrica_tipo} ({self.data}): {self.valor}"

#--------------------------------------------------------------
# MODELO DE LICENÇA (vinculado à Conta)
class Licenca(models.Model):
    class Meta:
        db_table = 'licenca'

    conta = models.OneToOneField(Conta, on_delete=models.CASCADE, related_name='licenca')
    plano = models.CharField(max_length=50)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativa = models.BooleanField(default=True)
    limite_usuarios = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='licencas_criadas',
        verbose_name="Criado Por"
    )

    def is_valida(self):
        from django.utils import timezone
        hoje = timezone.now().date()
        return self.ativa and self.data_inicio <= hoje <= self.data_fim

#--------------------------------------------------------------
# ASSOCIAÇÃO USUÁRIOS <-> CONTAS (com papéis)
class ContaMembership(models.Model):
    class Meta:
        db_table = 'conta_membership'
        unique_together = ('conta', 'user')

    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('contabilidade', 'Contabilidade'),
        ('medico', 'Médico'),
        ('readonly', 'Somente Leitura'),
    ]

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conta_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='readonly')
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conta_memberships_criadas',
        verbose_name="Criado Por"
    )

    def __str__(self):
        return f"{self.user.email} - {self.conta.name} ({self.role})"

#--------------------------------------------------------------
# MODELO BASE PARA TODOS OS MODELOS QUE PRECISAM DE TENANT ISOLATION
class SaaSBaseModel(models.Model):
    class Meta:
        abstract = True

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, null=False)
    objects = ContaScopedManager()

    def save(self, *args, **kwargs):
        if not self.conta_id:
            raise ValueError("Conta é obrigatória para todos os modelos SaaS")
        super().save(*args, **kwargs)

#--------------------------------------------------------------
# PERFIL PESSOA (pode ser usado para usuários e não-usuários)
class Pessoa(SaaSBaseModel):
    class Meta:
        db_table = 'pessoa'
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

    # Relacionamento com usuário (opcional)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pessoa_profile'
    )

    # Dados pessoais
    name = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, blank=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, verbose_name="RG")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")

    # Contatos
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    celular = models.CharField(max_length=20, blank=True, verbose_name="Celular")
    email = models.EmailField(blank=True, verbose_name="Email")

    # Endereço
    endereco = models.CharField(max_length=255, blank=True, verbose_name="Endereço")
    numero = models.CharField(max_length=10, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    cep = models.CharField(max_length=9, blank=True, verbose_name="CEP")

    # Dados profissionais
    crm = models.CharField(max_length=20, blank=True, verbose_name="CRM")
    especialidade = models.CharField(max_length=100, blank=True, verbose_name="Especialidade")

    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def nome_curto(self):
        """Retorna as duas primeiras palavras do nome"""
        palavras = self.name.split()
        return ' '.join(palavras[:2]) if len(palavras) >= 2 else self.name

#--------------------------------------------------------------
class Empresa(models.Model):
    class Meta:
        db_table = 'empresa'
        verbose_name = "Empresa/Associação"
        verbose_name_plural = "Empresas/Associações"
        unique_together = ('conta', 'cnpj')

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='empresas', null=False)

    # Dados da empresa
    name = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, blank=True, verbose_name="Nome Fantasia")
    cnpj = models.CharField(max_length=18, verbose_name="CNPJ")
    inscricao_estadual = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Estadual")
    inscricao_municipal = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Municipal")

    # Contatos
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="Email")
    site = models.URLField(blank=True, verbose_name="Site")

    # Endereço
    endereco = models.CharField(max_length=255, blank=True, verbose_name="Endereço")
    numero = models.CharField(max_length=10, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    cep = models.CharField(max_length=9, blank=True, verbose_name="CEP")

    # Dados tributários
    REGIME_CHOICES = [
        (REGIME_TRIBUTACAO_COMPETENCIA, 'Competência'),
        (REGIME_TRIBUTACAO_CAIXA, 'Caixa'),
    ]
    
    regime_tributario = models.IntegerField(
        choices=REGIME_CHOICES,
        default=REGIME_TRIBUTACAO_COMPETENCIA,
        verbose_name="Regime de Tributação",
        help_text="Regime de tributação que impacta no cálculo e recolhimento dos impostos (exceto ISS que é sempre competência)"
    )
    
    # Controle de receita para validação do regime de caixa
    receita_bruta_ano_anterior = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name="Receita Bruta Ano Anterior (R$)",
        help_text="Receita bruta do ano anterior para validação do direito ao regime de caixa (limite R$ 78 milhões)"
    )
    
    # Data da última alteração de regime (para controle anual)
    data_ultima_alteracao_regime = models.DateField(
        null=True, blank=True,
        verbose_name="Data Última Alteração de Regime",
        help_text="Data da última alteração de regime tributário (para controle de mudanças anuais)"
    )
    
    # Periodicidade de apuração de IRPJ/CSLL
    PERIODICIDADE_CHOICES = [
        (PERIODICIDADE_MENSAL, 'Mensal'),
        (PERIODICIDADE_TRIMESTRAL, 'Trimestral'),
    ]
    
    periodicidade_irpj_csll = models.CharField(
        max_length=12,
        choices=PERIODICIDADE_CHOICES,
        default=PERIODICIDADE_TRIMESTRAL,
        verbose_name="Periodicidade IRPJ/CSLL",
        help_text="Periodicidade de apuração e recolhimento do IRPJ e CSLL (opção da empresa)"
    )
    
    # Dia de vencimento específico do ISS no município
    dia_vencimento_iss = models.PositiveIntegerField(
        default=10,
        verbose_name="Dia Vencimento ISS",
        help_text="Dia do mês para vencimento do ISS conforme legislação municipal (geralmente 10, 15 ou 20)"
    )
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_fantasia or self.name

    def clean(self):
        # Validar regime de caixa conforme legislação
        if self.regime_tributario == REGIME_TRIBUTACAO_CAIXA:
            # Limite de R$ 78 milhões para regime de caixa (Lei 9.718/1998)
            limite_receita_caixa = 78000000.00  # R$ 78 milhões
            
            if (self.receita_bruta_ano_anterior and 
                self.receita_bruta_ano_anterior > limite_receita_caixa):
                raise ValidationError({
                    'regime_tributario': 
                    f'Empresa com receita bruta de R$ {self.receita_bruta_ano_anterior:,.2f} '
                    f'não pode optar pelo regime de caixa (limite: R$ {limite_receita_caixa:,.2f})'
                })
        
        # Validar que mudanças de regime respeitam periodicidade anual
        if self.pk and self.data_ultima_alteracao_regime:
            hoje = timezone.now().date()
            # Verificar se a última alteração foi no mesmo ano fiscal
            if (self.data_ultima_alteracao_regime.year == hoje.year and 
                self._state.adding == False):  # Não é criação, é alteração
                
                # Verificar se realmente houve mudança de regime
                empresa_original = Empresa.objects.get(pk=self.pk)
                if empresa_original.regime_tributario != self.regime_tributario:
                    raise ValidationError({
                        'regime_tributario': 
                        f'Alteração de regime já realizada em {self.data_ultima_alteracao_regime.year}. '
                        'Mudanças de regime são permitidas apenas uma vez por ano fiscal.'
                    })
        
        # Validar dia de vencimento do ISS
        if self.dia_vencimento_iss:
            if not (1 <= self.dia_vencimento_iss <= 31):
                raise ValidationError({
                    'dia_vencimento_iss': 'Dia de vencimento deve estar entre 1 e 31'
                })
            
            # Dias mais comuns conforme legislação municipal
            dias_comuns = [5, 10, 15, 20, 25]
            if self.dia_vencimento_iss not in dias_comuns:
                # Apenas aviso, não erro bloqueante
                import warnings
                warnings.warn(
                    f"Dia {self.dia_vencimento_iss} não é comum para vencimento de ISS. "
                    f"Dias mais comuns: {', '.join(map(str, dias_comuns))}",
                    UserWarning
                )
    
    @property
    def regime_tributario_nome(self):
        """Retorna o nome legível do regime tributário"""
        return self.get_regime_tributario_display()
    
    @property
    def eh_regime_competencia(self):
        """Verifica se a empresa usa regime de competência"""
        return self.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA
    
    @property
    def eh_regime_caixa(self):
        """Verifica se a empresa usa regime de caixa"""
        return self.regime_tributario == REGIME_TRIBUTACAO_CAIXA
    
    def obter_regime_vigente_na_data(self, data_referencia=None):
        """
        Obtém o regime tributário vigente para esta empresa em uma data específica
        
        Args:
            data_referencia: Data para consulta (default: hoje)
            
        Returns:
            dict: Informações do regime vigente na data ou regime atual da empresa
        """
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        # Importação lazy para evitar importação circular
        try:
            from .fiscal import RegimeTributarioHistorico
            regime_historico = RegimeTributarioHistorico.obter_regime_vigente(self, data_referencia)
            
            if regime_historico:
                return {
                    'codigo': regime_historico.regime_tributario,
                    'nome': regime_historico.get_regime_tributario_display(),
                    'data_inicio': regime_historico.data_inicio,
                    'data_fim': regime_historico.data_fim,
                    'fonte': 'historico'
                }
        except ImportError:
            pass  # Modelo fiscal ainda não foi importado
        
        # Fallback para regime atual
        return {
            'codigo': self.regime_tributario,
            'nome': self.regime_tributario_nome,
            'fonte': 'atual'
        }
    
    def alterar_regime_tributario(self, novo_regime, data_inicio=None, observacoes="", receita_bruta_ano_anterior=None):
        """
        Altera o regime tributário da empresa criando registro no histórico
        Inclui validações conforme legislação brasileira
        
        Args:
            novo_regime: Novo regime tributário (código)
            data_inicio: Data de início do novo regime (default: 1º de janeiro do próximo ano)
            observacoes: Observações sobre a mudança
            receita_bruta_ano_anterior: Receita para validação do regime de caixa
            
        Returns:
            RegimeTributarioHistorico: Novo registro criado
            
        Raises:
            ValidationError: Se alteração não atender requisitos legais
        """
        hoje = timezone.now().date()
        
        # Data padrão: 1º de janeiro do próximo ano (conforme legislação)
        if data_inicio is None:
            from datetime import date
            data_inicio = date(hoje.year + 1, 1, 1)
        
        # Validar que a data não é no passado
        if data_inicio < hoje:
            raise ValidationError("Alteração de regime não pode ter data de início no passado")
        
        # Validar periodicidade anual - mudanças só no início do ano fiscal
        if data_inicio.month != 1 or data_inicio.day != 1:
            raise ValidationError(
                "Alterações de regime tributário devem ter início em 1º de janeiro "
                "(Art. 12 da Lei 9.718/1998)"
            )
        
        # Validar se já houve alteração no ano fiscal atual
        if (self.data_ultima_alteracao_regime and 
            self.data_ultima_alteracao_regime.year == data_inicio.year):
            raise ValidationError(
                f"Já foi realizada alteração de regime em {data_inicio.year}. "
                "É permitida apenas uma alteração por ano fiscal."
            )
        
        # Validar limite de receita para regime de caixa
        if novo_regime == REGIME_TRIBUTACAO_CAIXA:
            limite_receita = 78000000.00  # R$ 78 milhões (Lei 9.718/1998)
            receita_validacao = receita_bruta_ano_anterior or self.receita_bruta_ano_anterior
            
            if receita_validacao and receita_validacao > limite_receita:
                raise ValidationError(
                    f"Empresa com receita bruta de R$ {receita_validacao:,.2f} não pode "
                    f"optar pelo regime de caixa (limite legal: R$ {limite_receita:,.2f})"
                )
        
        # Importação lazy para evitar importação circular
        from .fiscal import RegimeTributarioHistorico
        
        # Finalizar regime atual se existe
        regime_atual = RegimeTributarioHistorico.obter_regime_vigente(self)
        if regime_atual and not regime_atual.data_fim:
            # Finalizar o regime atual no dia anterior ao novo
            from datetime import timedelta
            regime_atual.data_fim = data_inicio - timedelta(days=1)
            regime_atual.save()
        
        # Criar novo registro de regime
        novo_registro = RegimeTributarioHistorico.objects.create(
            empresa=self,
            regime_tributario=novo_regime,
            data_inicio=data_inicio,
            observacoes=observacoes or f"Alteração de regime para {self.get_regime_tributario_display()} - {data_inicio.year}",
            receita_bruta_ano_anterior=receita_bruta_ano_anterior
        )
        
        # Atualizar os campos da empresa
        self.regime_tributario = novo_regime
        self.data_ultima_alteracao_regime = data_inicio
        if receita_bruta_ano_anterior is not None:
            self.receita_bruta_ano_anterior = receita_bruta_ano_anterior
        
        self.save(update_fields=[
            'regime_tributario', 
            'data_ultima_alteracao_regime', 
            'receita_bruta_ano_anterior',
            'updated_at'
        ])
        
        return novo_registro

#--------------------------------------------------------------
class Socio(models.Model):
    class Meta:
        db_table = 'socio'
        verbose_name = "Sócio/Médico"
        verbose_name_plural = "Sócios/Médicos"
        # Removido unique_together para permitir o mesmo CPF/pessoa em várias empresas
        indexes = [
            models.Index(fields=['conta', 'empresa', 'pessoa']),
            models.Index(fields=['ativo']),
        ]

    conta = models.ForeignKey(Conta, on_delete=models.PROTECT, related_name='socios', null=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    pessoa = models.ForeignKey(Pessoa, on_delete=models.PROTECT)

    # Status e controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_entrada = models.DateField(null=True, blank=True, verbose_name="Data de Entrada")
    data_saida = models.DateField(null=True, blank=True, verbose_name="Data de Saída")

    # Dados adicionais
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def __str__(self):
        return f"{self.pessoa.name} - {self.empresa.name}"

    def obter_percentual_item_mensal(self, item_despesa, mes_referencia):
        """Obtém o percentual de rateio para um item em um mês específico"""
        from .despesas import PercentualRateioMensal
        try:
            percentual = PercentualRateioMensal.objects.get(
                socio=self,
                item_despesa=item_despesa,
                mes_referencia=mes_referencia.replace(day=1),
                ativo=True
            )
            return percentual.percentual
        except PercentualRateioMensal.DoesNotExist:
            return 0

    def listar_percentuais_mes(self, mes_referencia):
        """Lista todos os percentuais de rateio para este sócio em um mês"""
        from .despesas import PercentualRateioMensal
        return PercentualRateioMensal.objects.filter(
            socio=self,
            mes_referencia=mes_referencia.replace(day=1),
            ativo=True
        ).select_related('item_despesa')

    def calcular_data_vencimento_imposto(self, tipo_imposto, data_competencia):
        """
        Calcula a data de vencimento de um imposto específico
        
        Args:
            tipo_imposto: 'ISS', 'PIS', 'COFINS', 'IRPJ', 'CSLL'
            data_competencia: Data da competência (prestação ou recebimento)
            
        Returns:
            date: Data de vencimento do imposto
        """
        from datetime import date, timedelta
        from calendar import monthrange
        
        if tipo_imposto == 'ISS':
            # ISS vence no dia configurado do mês seguinte
            if data_competencia.month == 12:
                ano_vencimento = data_competencia.year + 1
                mes_vencimento = 1
            else:
                ano_vencimento = data_competencia.year
                mes_vencimento = data_competencia.month + 1
            
            # Verificar se o dia existe no mês (ex: 31 em fevereiro)
            ultimo_dia_mes = monthrange(ano_vencimento, mes_vencimento)[1]
            dia_vencimento = min(self.dia_vencimento_iss, ultimo_dia_mes)
            
            return date(ano_vencimento, mes_vencimento, dia_vencimento)
        
        elif tipo_imposto in ['PIS', 'COFINS']:
            # PIS/COFINS vencem até o dia 25 do mês seguinte
            if data_competencia.month == 12:
                return date(data_competencia.year + 1, 1, 25)
            else:
                return date(data_competencia.year, data_competencia.month + 1, 25)
        
        elif tipo_imposto in ['IRPJ', 'CSLL']:
            if self.periodicidade_irpj_csll == PERIODICIDADE_MENSAL:
                # Mensal: último dia útil do mês seguinte
                if data_competencia.month == 12:
                    ano_vencimento = data_competencia.year + 1
                    mes_vencimento = 1
                else:
                    ano_vencimento = data_competencia.year
                    mes_vencimento = data_competencia.month + 1
                
                # Último dia do mês
                ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
                data_vencimento = date(ano_vencimento, mes_vencimento, ultimo_dia)
                
                # Ajustar para dia útil (implementação básica - sábado/domingo)
                while data_vencimento.weekday() >= 5:  # 5=sábado, 6=domingo
                    data_vencimento += timedelta(days=1)
                
                return data_vencimento
            
            else:  # TRIMESTRAL
                # Determinar o trimestre
                if data_competencia.month <= 3:
                    # 1º trimestre - vence até último dia útil de abril
                    data_base = date(data_competencia.year, 4, 30)
                elif data_competencia.month <= 6:
                    # 2º trimestre - vence até último dia útil de julho
                    data_base = date(data_competencia.year, 7, 31)
                elif data_competencia.month <= 9:
                    # 3º trimestre - vence até último dia útil de outubro
                    data_base = date(data_competencia.year, 10, 31)
                else:
                    # 4º trimestre - vence até último dia útil de janeiro do ano seguinte
                    data_base = date(data_competencia.year + 1, 1, 31)
                
                # Ajustar para dia útil
                while data_base.weekday() >= 5:
                    data_base += timedelta(days=1)
                
                return data_base
        
        else:
            raise ValueError(f"Tipo de imposto '{tipo_imposto}' não reconhecido")
    
    def gerar_cronograma_impostos_mes(self, mes_referencia):
        """
        Gera cronograma de vencimentos de impostos para um mês
        
        Args:
            mes_referencia: Data do mês de referência
            
        Returns:
            dict: Cronograma com datas de vencimento por imposto
        """
        cronograma = {}
        
        for tipo_imposto in ['ISS', 'PIS', 'COFINS', 'IRPJ', 'CSLL']:
            try:
                data_vencimento = self.calcular_data_vencimento_imposto(tipo_imposto, mes_referencia)
                
                # Determinar regime aplicado
                if tipo_imposto == 'ISS':
                    regime_aplicado = 'Competência (obrigatório)'
                else:
                    if (self.regime_tributario == REGIME_TRIBUTACAO_CAIXA and 
                        self.receita_bruta_ano_anterior and 
                        self.receita_bruta_ano_anterior <= 78000000.00):
                        regime_aplicado = 'Caixa'
                    else:
                        regime_aplicado = 'Competência'
                
                cronograma[tipo_imposto] = {
                    'data_vencimento': data_vencimento,
                    'regime_aplicado': regime_aplicado,
                    'periodicidade': IMPOSTOS_INFO[tipo_imposto].get('periodicidade', 
                                                                   self.periodicidade_irpj_csll if tipo_imposto in ['IRPJ', 'CSLL'] else PERIODICIDADE_MENSAL),
                    'base_legal': IMPOSTOS_INFO[tipo_imposto]['base_legal'],
                    'observacao': IMPOSTOS_INFO[tipo_imposto]['observacao']
                }
                
            except Exception as e:
                cronograma[tipo_imposto] = {
                    'erro': str(e),
                    'data_vencimento': None
                }
        
        return cronograma
    
    def obter_proximos_vencimentos(self, dias_antecedencia=30):
        """
        Obtém os próximos vencimentos de impostos
        
        Args:
            dias_antecedencia: Quantos dias à frente buscar vencimentos
            
        Returns:
            list: Lista de vencimentos ordenada por data
        """
        from datetime import date, timedelta
        
        hoje = date.today()
        data_limite = hoje + timedelta(days=dias_antecedencia)
        
        vencimentos = []
        
        # Verificar vencimentos dos próximos meses
        data_atual = hoje.replace(day=1)  # Primeiro dia do mês atual
        
        while data_atual <= data_limite:
            cronograma = self.gerar_cronograma_impostos_mes(data_atual)
            
            for tipo_imposto, info in cronograma.items():
                if (info.get('data_vencimento') and 
                    hoje <= info['data_vencimento'] <= data_limite):
                    
                    vencimentos.append({
                        'tipo_imposto': tipo_imposto,
                        'data_vencimento': info['data_vencimento'],
                        'regime_aplicado': info['regime_aplicado'],
                        'periodicidade': info['periodicidade'],
                        'dias_restantes': (info['data_vencimento'] - hoje).days,
                        'mes_competencia': data_atual.strftime('%m/%Y')
                    })
            
            # Próximo mês
            if data_atual.month == 12:
                data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
            else:
                data_atual = data_atual.replace(month=data_atual.month + 1)
        
        # Ordenar por data de vencimento
        vencimentos.sort(key=lambda x: x['data_vencimento'])
        
        return vencimentos

def ensure_conta_exists(conta_id, name=None):
    obj, created = Conta.objects.get_or_create(id=conta_id, defaults={
        'name': name or f'Conta {conta_id}',
        'cnpj': '',
    })
    return obj


