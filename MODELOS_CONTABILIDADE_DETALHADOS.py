# ================================
# MODELOS ATUALIZADOS PARA CONTABILIDADE DE ASSOCIAÇÕES MÉDICAS
# Com rateio de notas e despesas entre médicos associados
# ================================

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

#--------------------------------------------------------------
# MODELO BASE PARA ISOLAMENTO POR ASSOCIAÇÃO
class AssociacaoScopedModel(models.Model):
    """Modelo base para todos os modelos que precisam de isolamento por associação"""
    class Meta:
        abstract = True
    
    associacao = models.ForeignKey('AssociacaoMedica', on_delete=models.CASCADE)

#--------------------------------------------------------------
# ASSOCIAÇÃO DE MÉDICOS (Cliente da contabilidade)
class AssociacaoMedica(models.Model):
    """Associação/empresa de médicos - cliente da empresa de contabilidade"""
    
    # Dados básicos
    nome = models.CharField(max_length=255, unique=True, verbose_name="Nome da Associação")
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    
    # Contato
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    telefone = models.CharField(max_length=20, blank=True)
    email_contato = models.EmailField(blank=True)
    
    # Dados contábeis
    regime_tributario = models.IntegerField(choices=[
        (1, 'Simples Nacional'),
        (2, 'Lucro Presumido'),
        (3, 'Lucro Real'),
    ], default=1)
    
    # Status
    ativo = models.BooleanField(default=True)
    data_inicio_servicos = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'associacao_medica'
        verbose_name = "Associação de Médicos"
        verbose_name_plural = "Associações de Médicos"
    
    def __str__(self):
        return self.nome

#--------------------------------------------------------------
# MÉDICOS ASSOCIADOS À EMPRESA
class MedicoAssociado(AssociacaoScopedModel):
    """Médicos vinculados a uma associação médica"""
    
    # Dados pessoais
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    crm = models.CharField(max_length=20, verbose_name="CRM", blank=True)
    especialidade = models.CharField(max_length=100, blank=True)
    
    # Contato
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    
    # Dados bancários para transferências
    banco = models.CharField(max_length=10, blank=True)
    agencia = models.CharField(max_length=10, blank=True)
    conta = models.CharField(max_length=20, blank=True)
    
    # Percentuais de participação
    percentual_rateio_geral = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Percentual para rateio de despesas gerais (0-100%)"
    )
    percentual_rateio_folha = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Percentual para rateio de despesas de folha (0-100%)"
    )
    
    # Status
    ativo = models.BooleanField(default=True)
    data_admissao = models.DateField()
    data_saida = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'medico_associado'
        unique_together = ['associacao', 'cpf']
        verbose_name = "Médico Associado"
        verbose_name_plural = "Médicos Associados"
    
    def clean(self):
        """Validações personalizadas"""
        if self.percentual_rateio_geral < 0 or self.percentual_rateio_geral > 100:
            raise ValidationError("Percentual de rateio geral deve estar entre 0 e 100%")
        if self.percentual_rateio_folha < 0 or self.percentual_rateio_folha > 100:
            raise ValidationError("Percentual de rateio de folha deve estar entre 0 e 100%")
    
    def __str__(self):
        return f"{self.nome} ({self.crm})"

#--------------------------------------------------------------
# NOTAS FISCAIS
class NotaFiscal(AssociacaoScopedModel):
    """Notas fiscais recebidas das associações"""
    
    # Dados da nota
    numero = models.CharField(max_length=50, verbose_name="Número")
    serie = models.CharField(max_length=10, default="1")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_recebimento = models.DateField(verbose_name="Data de Recebimento na Contabilidade")
    
    # Prestador do serviço (pode ser um médico da associação ou externo)
    medico_prestador = models.ForeignKey(
        MedicoAssociado, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        verbose_name="Médico Prestador (se associado)"
    )
    prestador_externo_nome = models.CharField(
        max_length=255, blank=True,
        verbose_name="Nome do Prestador (se externo)"
    )
    prestador_externo_cpf = models.CharField(
        max_length=14, blank=True,
        verbose_name="CPF do Prestador (se externo)"
    )
    
    # Valores
    valor_bruto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Bruto")
    valor_liquido = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Líquido")
    
    # Impostos retidos
    irrf = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IRRF")
    pis = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="PIS")
    cofins = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="COFINS")
    iss = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="ISS")
    
    # Classificação
    tipo_servico = models.CharField(max_length=50, choices=[
        ('consulta', 'Consultas Médicas'),
        ('procedimento', 'Procedimentos'),
        ('exame', 'Exames'),
        ('plantao', 'Plantão'),
        ('cirurgia', 'Cirurgias'),
        ('outros', 'Outros Serviços'),
    ], default='consulta')
    
    # Rateio
    permitir_rateio = models.BooleanField(
        default=True, 
        verbose_name="Permitir Rateio",
        help_text="Se marcado, esta nota pode ser rateada entre médicos"
    )
    
    # Status de processamento
    status = models.CharField(max_length=20, choices=[
        ('recebida', 'Recebida'),
        ('processada', 'Processada'),
        ('rateada', 'Rateada'),
        ('lancada', 'Lançada na Contabilidade'),
        ('erro', 'Erro no Processamento'),
    ], default='recebida')
    
    # Controle
    processada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Processada Por"
    )
    data_processamento = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'nota_fiscal'
        unique_together = ['associacao', 'numero', 'serie']
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
    
    def __str__(self):
        return f"NF {self.numero}/{self.serie} - {self.associacao.nome}"

#--------------------------------------------------------------
# RATEIO DE NOTAS FISCAIS
class RateioNotaFiscal(models.Model):
    """Rateio de uma nota fiscal entre médicos associados"""
    
    nota_fiscal = models.ForeignKey(NotaFiscal, on_delete=models.CASCADE, related_name='rateios')
    medico = models.ForeignKey(MedicoAssociado, on_delete=models.CASCADE)
    
    # Valores do rateio
    percentual = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Percentual (%)",
        help_text="Percentual da nota que cabe a este médico"
    )
    valor_bruto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Bruto")
    valor_liquido = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Líquido")
    
    # Impostos proporcionais
    irrf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cofins = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    data_rateio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rateio_nota_fiscal'
        unique_together = ['nota_fiscal', 'medico']
        verbose_name = "Rateio de Nota Fiscal"
        verbose_name_plural = "Rateios de Notas Fiscais"
    
    def clean(self):
        if self.percentual <= 0 or self.percentual > 100:
            raise ValidationError("Percentual deve estar entre 0.01 e 100%")
    
    def save(self, *args, **kwargs):
        # Calcular valores proporcionais automaticamente
        if self.nota_fiscal and self.percentual:
            fator = self.percentual / 100
            self.valor_bruto = self.nota_fiscal.valor_bruto * fator
            self.valor_liquido = self.nota_fiscal.valor_liquido * fator
            self.irrf = self.nota_fiscal.irrf * fator
            self.pis = self.nota_fiscal.pis * fator
            self.cofins = self.nota_fiscal.cofins * fator
            self.iss = self.nota_fiscal.iss * fator
        super().save(*args, **kwargs)

#--------------------------------------------------------------
# DESPESAS - MODELO BASE
class DespesaBase(AssociacaoScopedModel):
    """Modelo base para todas as despesas"""
    
    # Dados básicos
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    
    # Documento
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name="Número do Documento")
    fornecedor = models.CharField(max_length=255, verbose_name="Fornecedor")
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ], default='pendente')
    
    # Controle
    lancada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Lançada Por"
    )
    data_lancamento = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        abstract = True

#--------------------------------------------------------------
# DESPESAS GERAIS (com rateio por percentual)
class DespesaGeral(DespesaBase):
    """Despesas gerais da associação - rateadas por percentual entre médicos"""
    
    categoria = models.CharField(max_length=50, choices=[
        ('aluguel', 'Aluguel'),
        ('energia', 'Energia Elétrica'),
        ('telefone', 'Telefone/Internet'),
        ('material', 'Material de Escritório'),
        ('limpeza', 'Limpeza'),
        ('seguranca', 'Segurança'),
        ('manutencao', 'Manutenção'),
        ('outros', 'Outras Despesas Gerais'),
    ], default='outros')
    
    # Flag para indicar se já foi rateada
    rateada = models.BooleanField(default=False)
    data_rateio = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'despesa_geral'
        verbose_name = "Despesa Geral"
        verbose_name_plural = "Despesas Gerais"

#--------------------------------------------------------------
# DESPESAS DE FOLHA (com rateio por percentual)
class DespesaFolha(DespesaBase):
    """Despesas de folha de pagamento - rateadas por percentual entre médicos"""
    
    categoria = models.CharField(max_length=50, choices=[
        ('salarios', 'Salários'),
        ('encargos', 'Encargos Sociais'),
        ('ferias', 'Férias'),
        ('decimo_terceiro', '13º Salário'),
        ('fgts', 'FGTS'),
        ('inss', 'INSS'),
        ('outros', 'Outras Despesas de Folha'),
    ], default='salarios')
    
    # Flag para indicar se já foi rateada
    rateada = models.BooleanField(default=False)
    data_rateio = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'despesa_folha'
        verbose_name = "Despesa de Folha"
        verbose_name_plural = "Despesas de Folha"

#--------------------------------------------------------------
# DESPESAS DE SÓCIO (sem rateio, direto na conta do médico)
class DespesaSocio(DespesaBase):
    """Despesas específicas de um médico - sem rateio"""
    
    medico = models.ForeignKey(
        MedicoAssociado, 
        on_delete=models.CASCADE,
        verbose_name="Médico Responsável"
    )
    
    categoria = models.CharField(max_length=50, choices=[
        ('pro_labore', 'Pró-labore'),
        ('retirada', 'Retirada de Sócio'),
        ('reembolso', 'Reembolso'),
        ('adiantamento', 'Adiantamento'),
        ('equipamento_pessoal', 'Equipamento Pessoal'),
        ('viagem', 'Viagem'),
        ('curso', 'Curso/Capacitação'),
        ('outros', 'Outras Despesas Pessoais'),
    ], default='outros')
    
    class Meta:
        db_table = 'despesa_socio'
        verbose_name = "Despesa de Sócio"
        verbose_name_plural = "Despesas de Sócios"

#--------------------------------------------------------------
# RATEIOS DE DESPESAS GERAIS
class RateioDespesaGeral(models.Model):
    """Rateio de despesa geral entre médicos"""
    
    despesa = models.ForeignKey(DespesaGeral, on_delete=models.CASCADE, related_name='rateios')
    medico = models.ForeignKey(MedicoAssociado, on_delete=models.CASCADE)
    
    percentual = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentual (%)")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    
    data_rateio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rateio_despesa_geral'
        unique_together = ['despesa', 'medico']
        verbose_name = "Rateio de Despesa Geral"
    
    def save(self, *args, **kwargs):
        # Usar o percentual definido no médico
        if not self.percentual:
            self.percentual = self.medico.percentual_rateio_geral
        
        # Calcular valor proporcional
        if self.despesa and self.percentual:
            self.valor = self.despesa.valor * (self.percentual / 100)
        
        super().save(*args, **kwargs)

#--------------------------------------------------------------
# RATEIOS DE DESPESAS DE FOLHA
class RateioDespesaFolha(models.Model):
    """Rateio de despesa de folha entre médicos"""
    
    despesa = models.ForeignKey(DespesaFolha, on_delete=models.CASCADE, related_name='rateios')
    medico = models.ForeignKey(MedicoAssociado, on_delete=models.CASCADE)
    
    percentual = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentual (%)")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    
    data_rateio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rateio_despesa_folha'
        unique_together = ['despesa', 'medico']
        verbose_name = "Rateio de Despesa de Folha"
    
    def save(self, *args, **kwargs):
        # Usar o percentual definido no médico
        if not self.percentual:
            self.percentual = self.medico.percentual_rateio_folha
        
        # Calcular valor proporcional
        if self.despesa and self.percentual:
            self.valor = self.despesa.valor * (self.percentual / 100)
        
        super().save(*args, **kwargs)

#--------------------------------------------------------------
# CONTRATO DE PRESTAÇÃO DE SERVIÇOS CONTÁBEIS
class ContratoContabil(models.Model):
    """Contrato entre a contabilidade e a associação médica"""
    
    associacao = models.OneToOneField(
        AssociacaoMedica, 
        on_delete=models.CASCADE, 
        related_name='contrato'
    )
    
    # Dados do contrato
    numero_contrato = models.CharField(max_length=50, unique=True)
    tipo_servico = models.CharField(max_length=50, choices=[
        ('completo', 'Contabilidade Completa'),
        ('fiscal', 'Apenas Obrigações Fiscais'),
        ('folha', 'Folha de Pagamento'),
        ('personalizado', 'Serviços Personalizados'),
    ], default='completo')
    
    # Valores
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    valor_por_nota = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Valor adicional por nota fiscal processada"
    )
    
    # Vigência
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    
    # Limites
    limite_notas_mes = models.IntegerField(default=500)
    limite_medicos = models.IntegerField(default=20)
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contrato_contabil'
        verbose_name = "Contrato Contábil"
        verbose_name_plural = "Contratos Contábeis"
    
    def __str__(self):
        return f"Contrato {self.numero_contrato} - {self.associacao.nome}"

#--------------------------------------------------------------
# RESPONSÁVEL CONTÁBIL (Contador da empresa responsável pela associação)
class ResponsavelContabil(models.Model):
    """Contador responsável por uma associação médica"""
    
    associacao = models.ForeignKey(AssociacaoMedica, on_delete=models.CASCADE)
    contador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    role = models.CharField(max_length=20, choices=[
        ('responsavel', 'Contador Responsável'),
        ('assistente', 'Assistente Contábil'),
        ('supervisor', 'Supervisor'),
        ('estagiario', 'Estagiário'),
    ], default='responsavel')
    
    # Permissões específicas
    pode_aprovar_rateios = models.BooleanField(default=False)
    pode_gerar_relatorios = models.BooleanField(default=True)
    pode_lancar_despesas = models.BooleanField(default=True)
    
    # Controle
    data_atribuicao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'responsavel_contabil'
        unique_together = ['associacao', 'contador']
        verbose_name = "Responsável Contábil"
        verbose_name_plural = "Responsáveis Contábeis"
    
    def __str__(self):
        return f"{self.contador.get_full_name()} → {self.associacao.nome}"
