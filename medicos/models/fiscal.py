from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .base import (
    Conta, Empresa, NFISCAL_ALIQUOTA_CONSULTAS, NFISCAL_ALIQUOTA_PLANTAO, 
    NFISCAL_ALIQUOTA_OUTROS, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
)


class RegimeTributarioHistorico(models.Model):
    """
    Histórico de regimes tributários das empresas
    
    Este modelo controla as mudanças de regime tributário ao longo do tempo,
    garantindo que alterações não afetem períodos passados e que sempre
    seja possível determinar qual regime estava vigente em uma data específica.
    
    Implementa as regras da legislação brasileira:
    - Lei 9.718/1998 (regime de caixa)
    - CTN Art. 177 (regime de competência)
    - Lei Complementar 116/2003 (ISS sempre competência)
    """
    
    class Meta:
        db_table = 'regime_tributario_historico'
        verbose_name = "Histórico de Regime Tributário"
        verbose_name_plural = "Históricos de Regimes Tributários"
        unique_together = ['empresa', 'data_inicio']
        indexes = [
            models.Index(fields=['empresa', 'data_inicio']),
            models.Index(fields=['empresa', 'data_inicio', 'data_fim']),
            models.Index(fields=['regime_tributario', 'data_inicio']),
        ]
        ordering = ['empresa', '-data_inicio']

    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='historico_regimes',
        verbose_name="Empresa"
    )
    
    REGIME_CHOICES = [
        (REGIME_TRIBUTACAO_COMPETENCIA, 'Competência'),
        (REGIME_TRIBUTACAO_CAIXA, 'Caixa'),
    ]
    
    regime_tributario = models.IntegerField(
        choices=REGIME_CHOICES,
        verbose_name="Regime de Tributação",
        help_text="Regime tributário vigente neste período (ISS sempre competência independente da escolha)"
    )
    
    data_inicio = models.DateField(
        verbose_name="Data de Início",
        help_text="Data de início da vigência deste regime tributário (deve ser 1º de janeiro conforme legislação)"
    )
    
    data_fim = models.DateField(
        null=True, blank=True,
        verbose_name="Data de Fim",
        help_text="Data de fim da vigência (deixe vazio se ainda vigente)"
    )
    
    # Controle de receita para validação do regime de caixa (Lei 9.718/1998)
    receita_bruta_ano_anterior = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name="Receita Bruta Ano Anterior (R$)",
        help_text="Receita bruta do ano anterior que justifica a opção pelo regime (limite R$ 78 milhões para caixa)"
    )
    
    # Controle de comunicação aos órgãos fiscais
    comunicado_receita_federal = models.BooleanField(
        default=False,
        verbose_name="Comunicado à Receita Federal",
        help_text="Indica se a alteração foi devidamente comunicada à Receita Federal"
    )
    
    data_comunicacao_rf = models.DateField(
        null=True, blank=True,
        verbose_name="Data Comunicação RF",
        help_text="Data da comunicação à Receita Federal"
    )
    
    comunicado_municipio = models.BooleanField(
        default=False,
        verbose_name="Comunicado ao Município",
        help_text="Indica se a alteração foi comunicada ao município (relevante para ISS)"
    )
    
    data_comunicacao_municipio = models.DateField(
        null=True, blank=True,
        verbose_name="Data Comunicação Município",
        help_text="Data da comunicação ao município"
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='regimes_criados',
        verbose_name="Criado por"
    )
    
    observacoes = models.TextField(
        blank=True, verbose_name="Observações",
        help_text="Motivo da alteração, base legal aplicada ou observações sobre este período"
    )

    def clean(self):
        """Validações do modelo conforme legislação brasileira"""
        # Validar datas
        if self.data_fim and self.data_inicio >= self.data_fim:
            raise ValidationError({
                'data_fim': 'Data fim deve ser posterior à data início'
            })
        
        # Validar que data de início é 1º de janeiro (legislação brasileira)
        if self.data_inicio and (self.data_inicio.month != 1 or self.data_inicio.day != 1):
            raise ValidationError({
                'data_inicio': 'Alterações de regime devem iniciar em 1º de janeiro conforme legislação (Art. 12 Lei 9.718/1998)'
            })
        
        # Validar limite de receita para regime de caixa
        if self.regime_tributario == REGIME_TRIBUTACAO_CAIXA:
            limite_receita = 78000000.00  # R$ 78 milhões
            if (self.receita_bruta_ano_anterior and 
                self.receita_bruta_ano_anterior > limite_receita):
                raise ValidationError({
                    'receita_bruta_ano_anterior': 
                    f'Receita bruta de R$ {self.receita_bruta_ano_anterior:,.2f} excede o limite '
                    f'de R$ {limite_receita:,.2f} para regime de caixa (Lei 9.718/1998)'
                })
        
        # Validar que não há sobreposição de períodos para a mesma empresa
        if self.empresa_id:
            qs = RegimeTributarioHistorico.objects.filter(empresa=self.empresa)
            
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            for regime in qs:
                if self._periodos_se_sobrepoe(regime):
                    raise ValidationError({
                        'data_inicio': 
                        f'Período sobrepõe com regime existente de '
                        f'{regime.data_inicio} até {regime.data_fim or "vigente"}'
                    })
        
        # Validar que só há um regime por ano fiscal para a mesma empresa
        if self.empresa_id and self.data_inicio:
            ano_fiscal = self.data_inicio.year
            regimes_mesmo_ano = RegimeTributarioHistorico.objects.filter(
                empresa=self.empresa,
                data_inicio__year=ano_fiscal
            )
            
            if self.pk:
                regimes_mesmo_ano = regimes_mesmo_ano.exclude(pk=self.pk)
            
            if regimes_mesmo_ano.exists():
                raise ValidationError({
                    'data_inicio': 
                    f'Já existe alteração de regime para o ano fiscal {ano_fiscal}. '
                    'É permitida apenas uma alteração por ano.'
                })
        
        # Validar comunicação obrigatória para regime de caixa
        if (self.regime_tributario == REGIME_TRIBUTACAO_CAIXA and 
            not self.comunicado_receita_federal and 
            self.data_inicio and 
            self.data_inicio <= timezone.now().date()):
            # Apenas aviso, não erro bloqueante
            import warnings
            warnings.warn(
                "Regime de caixa requer comunicação à Receita Federal até 31/01 do ano de vigência",
                UserWarning
            )
    
    def _periodos_se_sobrepoe(self, outro_regime):
        """Verifica se dois períodos de regime se sobrepõem"""
        from datetime import date, timedelta
        
        inicio_self = self.data_inicio
        fim_self = self.data_fim or date.today() + timedelta(days=36500)  # ~100 anos no futuro
        
        inicio_outro = outro_regime.data_inicio
        fim_outro = outro_regime.data_fim or date.today() + timedelta(days=36500)
        
        # Dois períodos se sobrepõem se um não termina antes do outro começar
        return not (fim_self < inicio_outro or fim_outro < inicio_self)
    
    def __str__(self):
        regime_nome = self.get_regime_tributario_display()
        if self.data_fim:
            return f"{self.empresa.name} - {regime_nome} ({self.data_inicio} até {self.data_fim})"
        else:
            return f"{self.empresa.name} - {regime_nome} (desde {self.data_inicio})"
    
    @property
    def eh_vigente(self):
        """Verifica se este regime está vigente hoje"""
        hoje = timezone.now().date()
        return self.data_inicio <= hoje and (not self.data_fim or self.data_fim >= hoje)
    
    @classmethod
    def obter_regime_vigente(cls, empresa, data_referencia=None):
        """
        Obtém o regime tributário vigente para uma empresa em uma data específica
        
        Args:
            empresa: Instância da empresa
            data_referencia: Data para consulta (default: hoje)
            
        Returns:
            RegimeTributarioHistorico ou None se não encontrar
        """
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        return cls.objects.filter(
            empresa=empresa,
            data_inicio__lte=data_referencia
        ).filter(
            models.Q(data_fim__isnull=True) | 
            models.Q(data_fim__gte=data_referencia)
        ).first()
    
    @classmethod
    def obter_ou_criar_regime_atual(cls, empresa):
        """
        Obtém o regime atual ou cria baseado no regime da empresa
        
        Este método garante compatibilidade com o sistema existente,
        criando automaticamente o histórico baseado no regime atual da empresa
        """
        regime_atual = cls.obter_regime_vigente(empresa)
        
        if not regime_atual:
            # Criar registro para o regime atual da empresa
            hoje = timezone.now().date()
            regime_atual = cls.objects.create(
                empresa=empresa,
                regime_tributario=empresa.regime_tributario,
                data_inicio=hoje,
                observacoes="Regime inicial criado automaticamente baseado na configuração da empresa"
            )
        
        return regime_atual


class Aliquotas(models.Model):
    """
    Alíquotas de impostos e regras para cálculo da tributação
    
    Este modelo define as alíquotas e parâmetros necessários para o cálculo automático
    dos impostos incidentes sobre as notas fiscais (ISS, PIS, COFINS, IRPJ, CSLL).
    
    Cada conta/cliente pode ter suas próprias alíquotas configuradas conforme
    sua situação tributária específica.
    """
    
    class Meta:
        db_table = 'aliquotas'
        verbose_name = "Configuração de Alíquotas"
        verbose_name_plural = "Configurações de Alíquotas"
        # Permitir múltiplas configurações por conta com vigências diferentes
        # A unicidade será garantida por validação personalizada
        indexes = [
            models.Index(fields=['conta', 'ativa', 'data_vigencia_inicio']),
            models.Index(fields=['conta', 'data_vigencia_inicio', 'data_vigencia_fim']),
        ]

    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='aliquotas', 
        null=False,
        verbose_name="Conta",
        help_text="Conta/cliente proprietária destas configurações tributárias"
    )
    
    # === IMPOSTOS MUNICIPAIS POR TIPO DE SERVIÇO ===
    ISS_CONSULTAS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Consultas (%)",
        help_text="Alíquota do ISS para prestação de serviços de consulta médica"
    )
    
    ISS_PLANTAO = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Plantão (%)",
        help_text="Alíquota do ISS para prestação de serviços de plantão médico"
    )
    
    ISS_OUTROS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Outros Serviços (%)",
        help_text="Alíquota do ISS para vacinação, exames, procedimentos e outros serviços"
    )
    
    # === CONTRIBUIÇÕES FEDERAIS ===
    PIS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="PIS (%)",
        help_text="Alíquota do PIS (geralmente 0,65%)"
    )
    
    COFINS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="COFINS (%)",
        help_text="Alíquota da COFINS (geralmente 3%)"
    )
    
    # === IMPOSTO DE RENDA PESSOA JURÍDICA ===
    IRPJ_BASE_CAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=32.00,
        verbose_name="IRPJ - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo do IRPJ (padrão 32%)"
    )
    
    IRPJ_ALIC_1 = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=15.00,
        verbose_name="IRPJ - Alíquota Normal (%)",
        help_text="Alíquota normal do IRPJ (padrão 15%)"
    )
    
    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = models.DecimalField(
        max_digits=12, decimal_places=2, null=False, default=60000.00,
        verbose_name="IRPJ - Limite para Adicional (R$)",
        help_text="Valor limite trimestral para adicional (padrão R$ 60.000,00)"
    )
    
    IRPJ_ADICIONAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=10.00,
        verbose_name="IRPJ - Adicional (%)",
        help_text="Alíquota do adicional de IRPJ (padrão 10%)"
    )
    
    # === CONTRIBUIÇÃO SOCIAL SOBRE O LUCRO LÍQUIDO ===
    CSLL_BASE_CAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=32.00,
        verbose_name="CSLL - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo da CSLL (padrão 32%)"
    )
    
    CSLL_ALIC_1 = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=9.00,
        verbose_name="CSLL - Alíquota Normal (%)",
        help_text="Alíquota normal da CSLL (padrão 9%)"
    )
    
    CSLL_ALIC_2 = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=15.00,
        verbose_name="CSLL - Alíquota Adicional (%)",
        help_text="Alíquota adicional da CSLL para prestadores de serviços (padrão 15%)"
    )
    
    # === CONTROLE E AUDITORIA ===
    ativa = models.BooleanField(
        default=True,
        verbose_name="Configuração Ativa",
        help_text="Indica se esta configuração está ativa para uso nos cálculos"
    )
    
    data_vigencia_inicio = models.DateField(
        null=True, blank=True,
        verbose_name="Início da Vigência",
        help_text="Data de início da vigência desta configuração tributária"
    )
    
    data_vigencia_fim = models.DateField(
        null=True, blank=True,
        verbose_name="Fim da Vigência",
        help_text="Data de fim da vigência (deixe vazio se não há limite)"
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='aliquotas_criadas',
        verbose_name="Criado por"
    )
    
    observacoes = models.TextField(
        blank=True, verbose_name="Observações",
        help_text="Observações sobre as particularidades desta configuração tributária"
    )

    def clean(self):
        campos_percentuais = [
            ('ISS_CONSULTAS', self.ISS_CONSULTAS, 0, 20),
            ('ISS_PLANTAO', self.ISS_PLANTAO, 0, 20),
            ('ISS_OUTROS', self.ISS_OUTROS, 0, 20),
            ('PIS', self.PIS, 0, 10),
            ('COFINS', self.COFINS, 0, 10),
            ('IRPJ_BASE_CAL', self.IRPJ_BASE_CAL, 0, 100),
            ('IRPJ_ALIC_1', self.IRPJ_ALIC_1, 0, 50),
            ('IRPJ_ADICIONAL', self.IRPJ_ADICIONAL, 0, 50),
            ('CSLL_BASE_CAL', self.CSLL_BASE_CAL, 0, 100),
            ('CSLL_ALIC_1', self.CSLL_ALIC_1, 0, 50),
            ('CSLL_ALIC_2', self.CSLL_ALIC_2, 0, 50),
        ]
        
        for nome, valor, minimo, maximo in campos_percentuais:
            if valor < minimo or valor > maximo:
                raise ValidationError({
                    nome.lower(): f'{nome} deve estar entre {minimo}% e {maximo}%'
                })
        
        # Validar datas de vigência
        if (self.data_vigencia_inicio and self.data_vigencia_fim and 
            self.data_vigencia_inicio > self.data_vigencia_fim):
            raise ValidationError({
                'data_vigencia_fim': 'Data fim deve ser posterior à data início'
            })
        
        # Validar sobreposição de vigências para a mesma conta
        if self.ativa and self.data_vigencia_inicio:
            qs = Aliquotas.objects.filter(
                conta=self.conta,
                ativa=True
            )
            
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            # Verificar sobreposição de datas
            for aliquota in qs:
                if self._vigencias_se_sobrepoe(aliquota):
                    raise ValidationError({
                        'data_vigencia_inicio': 
                        f'Período de vigência sobrepõe com configuração existente de '
                        f'{aliquota.data_vigencia_inicio} até {aliquota.data_vigencia_fim or "indeterminado"}'
                    })
    
    def _vigencias_se_sobrepoe(self, outra_aliquota):
        """Verifica se as vigências de duas configurações se sobrepõem"""
        # Se alguma das configurações não tem data de início definida, não verifica
        if not self.data_vigencia_inicio or not outra_aliquota.data_vigencia_inicio:
            return False
        
        inicio_self = self.data_vigencia_inicio
        fim_self = self.data_vigencia_fim
        inicio_outra = outra_aliquota.data_vigencia_inicio
        fim_outra = outra_aliquota.data_vigencia_fim
        
        # Se não há data fim, considera como vigência indefinida (até hoje + 100 anos)
        from datetime import date, timedelta
        data_muito_futura = date.today() + timedelta(days=36500)  # ~100 anos
        
        if fim_self is None:
            fim_self = data_muito_futura
        if fim_outra is None:
            fim_outra = data_muito_futura
        
        # Verifica sobreposição: duas vigências se sobrepõem se uma não termina antes da outra começar
        return not (fim_self < inicio_outra or fim_outra < inicio_self)

    def __str__(self):
        return f"Alíquotas - {self.conta.name} (ISS Consultas: {self.ISS_CONSULTAS}%, Plantão: {self.ISS_PLANTAO}%, Outros: {self.ISS_OUTROS}%)"
    
    @property
    def eh_vigente(self):
        hoje = timezone.now().date()
        if self.data_vigencia_inicio and hoje < self.data_vigencia_inicio:
            return False
        if self.data_vigencia_fim and hoje > self.data_vigencia_fim:
            return False
        return self.ativa
    
    def calcular_impostos_nf(self, valor_bruto, tipo_servico='consultas', empresa=None):
        """Calcula os impostos para uma nota fiscal baseado no tipo de serviço prestado"""
        if not self.eh_vigente:
            raise ValidationError("Esta configuração de alíquotas não está vigente.")
        
        # Determinar alíquota ISS baseada no tipo de serviço
        if tipo_servico == 'consultas':
            aliquota_iss = self.ISS_CONSULTAS
            descricao_servico = "Consultas Médicas"
        elif tipo_servico == 'plantao':
            aliquota_iss = self.ISS_PLANTAO
            descricao_servico = "Plantão Médico"
        elif tipo_servico == 'outros':
            aliquota_iss = self.ISS_OUTROS
            descricao_servico = "Vacinação/Exames/Procedimentos"
        else:
            aliquota_iss = self.ISS_CONSULTAS
            descricao_servico = "Consultas Médicas"
        
        # Cálculos básicos
        valor_iss = valor_bruto * (aliquota_iss / 100)
        valor_pis = valor_bruto * (self.PIS / 100)
        valor_cofins = valor_bruto * (self.COFINS / 100)
        
        # Base de cálculo para IR e CSLL
        base_calculo_ir = valor_bruto * (self.IRPJ_BASE_CAL / 100)
        base_calculo_csll = valor_bruto * (self.CSLL_BASE_CAL / 100)
        
        # IRPJ
        valor_ir_normal = base_calculo_ir * (self.IRPJ_ALIC_1 / 100)
        valor_ir_adicional = 0
        if base_calculo_ir > self.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL:
            excesso = base_calculo_ir - self.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL
            valor_ir_adicional = excesso * (self.IRPJ_ADICIONAL / 100)
        
        valor_ir_total = valor_ir_normal + valor_ir_adicional
        
        # CSLL
        valor_csll = base_calculo_csll * (self.CSLL_ALIC_1 / 100)
        
        # Valor líquido
        total_impostos = valor_iss + valor_pis + valor_cofins + valor_ir_total + valor_csll
        valor_liquido = valor_bruto - total_impostos
        
        # Determinar regime tributário
        regime_info = self._obter_info_regime_tributario(empresa)
        
        return {
            'valor_bruto': valor_bruto,
            'tipo_servico': tipo_servico,
            'descricao_servico': descricao_servico,
            'aliquota_iss_aplicada': aliquota_iss,
            'valor_iss': valor_iss,
            'valor_pis': valor_pis,
            'valor_cofins': valor_cofins,
            'valor_ir': valor_ir_total,
            'valor_ir_normal': valor_ir_normal,
            'valor_ir_adicional': valor_ir_adicional,
            'valor_csll': valor_csll,
            'total_impostos': total_impostos,
            'valor_liquido': valor_liquido,
            'base_calculo_ir': base_calculo_ir,
            'base_calculo_csll': base_calculo_csll,
            'regime_tributario': regime_info,
        }
    
    def calcular_impostos_com_regime(self, valor_bruto, tipo_servico='consultas', empresa=None, data_referencia=None):
        """
        Calcula impostos considerando o regime tributário da empresa vigente na data específica
        Aplica regras específicas da legislação brasileira por tipo de imposto
        
        Args:
            valor_bruto: Valor bruto da nota fiscal
            tipo_servico: Tipo de serviço prestado
            empresa: Instância da empresa (para determinar regime)
            data_referencia: Data para cálculo (relevante para regime caixa e histórico)
            
        Returns:
            dict: Detalhamento completo dos impostos com impacto do regime tributário
        """
        if not self.eh_vigente:
            raise ValidationError("Esta configuração de alíquotas não está vigente.")
        
        # Se não há data de referência, usar hoje
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        # Determinar regime tributário vigente na data específica
        regime_info = self._obter_regime_vigente_na_data(empresa, data_referencia)
        
        # Cálculo base dos impostos
        resultado_base = self.calcular_impostos_nf(valor_bruto, tipo_servico, empresa)
        
        # Aplicar regras específicas por tipo de imposto conforme legislação
        regimes_por_imposto = self._obter_regimes_especificos_por_imposto(
            regime_info, empresa, data_referencia
        )
        
        # Aplicar cálculos considerando regime específico de cada imposto
        resultado_regime = self._aplicar_regimes_especificos(
            resultado_base, regimes_por_imposto, data_referencia
        )
        
        # Adicionar informações detalhadas do regime
        resultado_regime.update({
            'regime_tributario': regime_info,
            'regimes_por_imposto': regimes_por_imposto,
            'data_referencia_calculo': data_referencia,
            'observacoes_legais': self._gerar_observacoes_legais(regimes_por_imposto)
        })
        
        return resultado_regime
    
    def _obter_regimes_especificos_por_imposto(self, regime_info, empresa, data_referencia):
        """
        Determina o regime específico para cada tipo de imposto conforme legislação
        
        Returns:
            dict: Regime aplicado para cada tipo de imposto
        """
        regime_empresa = regime_info['codigo']
        
        # Verificar se empresa pode usar regime de caixa (limite de receita)
        pode_usar_caixa = True
        if empresa and regime_empresa == REGIME_TRIBUTACAO_CAIXA:
            limite_receita = 78000000.00  # R$ 78 milhões
            receita_empresa = empresa.receita_bruta_ano_anterior
            
            if receita_empresa and receita_empresa > limite_receita:
                pode_usar_caixa = False
        
        return {
            'ISS': {
                'regime': REGIME_TRIBUTACAO_COMPETENCIA,  # Sempre competência (LC 116/2003)
                'nome': 'Competência',
                'motivo': 'ISS sempre competência conforme Lei Complementar 116/2003',
                'base_legal': 'LC 116/2003, Art. 7º'
            },
            'PIS': {
                'regime': regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA,
                'nome': self._nome_regime(regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA),
                'motivo': 'Segue regime da empresa' if pode_usar_caixa else 'Competência por limite de receita',
                'base_legal': 'Lei 9.718/1998' if pode_usar_caixa and regime_empresa == REGIME_TRIBUTACAO_CAIXA else 'CTN Art. 177'
            },
            'COFINS': {
                'regime': regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA,
                'nome': self._nome_regime(regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA),
                'motivo': 'Segue regime da empresa' if pode_usar_caixa else 'Competência por limite de receita',
                'base_legal': 'Lei 9.718/1998' if pode_usar_caixa and regime_empresa == REGIME_TRIBUTACAO_CAIXA else 'CTN Art. 177'
            },
            'IRPJ': {
                'regime': regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA,
                'nome': self._nome_regime(regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA),
                'motivo': 'Segue regime da empresa' if pode_usar_caixa else 'Competência por limite de receita',
                'base_legal': 'Lei 9.718/1998' if pode_usar_caixa and regime_empresa == REGIME_TRIBUTACAO_CAIXA else 'CTN Art. 177'
            },
            'CSLL': {
                'regime': regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA,
                'nome': self._nome_regime(regime_empresa if pode_usar_caixa else REGIME_TRIBUTACAO_COMPETENCIA),
                'motivo': 'Segue regime da empresa' if pode_usar_caixa else 'Competência por limite de receita',
                'base_legal': 'Lei 9.718/1998' if pode_usar_caixa and regime_empresa == REGIME_TRIBUTACAO_CAIXA else 'CTN Art. 177'
            }
        }
    
    def _nome_regime(self, codigo_regime):
        """Retorna nome do regime pelo código"""
        return 'Competência' if codigo_regime == REGIME_TRIBUTACAO_COMPETENCIA else 'Caixa'
    
    def _aplicar_regimes_especificos(self, resultado_base, regimes_por_imposto, data_referencia):
        """
        Aplica as regras específicas de cada regime por tipo de imposto
        """
        resultado = resultado_base.copy()
        
        # ISS - sempre competência, sem alterações no cálculo base
        # (valores já calculados corretamente no método base)
        
        # PIS/COFINS - podem ter regime de caixa se empresa atender critérios
        if regimes_por_imposto['PIS']['regime'] == REGIME_TRIBUTACAO_CAIXA:
            resultado['observacoes_pis'] = [
                "PIS calculado pelo regime de caixa",
                "Recolhimento devido no mês do recebimento",
                f"Base legal: {regimes_por_imposto['PIS']['base_legal']}"
            ]
        else:
            resultado['observacoes_pis'] = [
                "PIS calculado pelo regime de competência",
                "Recolhimento devido no mês da prestação",
                f"Base legal: {regimes_por_imposto['PIS']['base_legal']}"
            ]
        
        if regimes_por_imposto['COFINS']['regime'] == REGIME_TRIBUTACAO_CAIXA:
            resultado['observacoes_cofins'] = [
                "COFINS calculado pelo regime de caixa",
                "Recolhimento devido no mês do recebimento",
                f"Base legal: {regimes_por_imposto['COFINS']['base_legal']}"
            ]
        else:
            resultado['observacoes_cofins'] = [
                "COFINS calculado pelo regime de competência",
                "Recolhimento devido no mês da prestação",
                f"Base legal: {regimes_por_imposto['COFINS']['base_legal']}"
            ]
        
        # IRPJ/CSLL - podem ter regime de caixa se empresa atender critérios
        if regimes_por_imposto['IRPJ']['regime'] == REGIME_TRIBUTACAO_CAIXA:
            resultado['observacoes_irpj'] = [
                "IRPJ calculado pelo regime de caixa",
                "Base de cálculo considerada no recebimento",
                f"Base legal: {regimes_por_imposto['IRPJ']['base_legal']}"
            ]
        else:
            resultado['observacoes_irpj'] = [
                "IRPJ calculado pelo regime de competência",
                "Base de cálculo considerada na prestação",
                f"Base legal: {regimes_por_imposto['IRPJ']['base_legal']}"
            ]
        
        if regimes_por_imposto['CSLL']['regime'] == REGIME_TRIBUTACAO_CAIXA:
            resultado['observacoes_csll'] = [
                "CSLL calculado pelo regime de caixa",
                "Base de cálculo considerada no recebimento",
                f"Base legal: {regimes_por_imposto['CSLL']['base_legal']}"
            ]
        else:
            resultado['observacoes_csll'] = [
                "CSLL calculado pelo regime de competência",
                "Base de cálculo considerada na prestação",
                f"Base legal: {regimes_por_imposto['CSLL']['base_legal']}"
            ]
        
        # ISS - sempre competência
        resultado['observacoes_iss'] = [
            "ISS calculado pelo regime de competência (obrigatório)",
            "Recolhimento sempre no mês da prestação do serviço",
            f"Base legal: {regimes_por_imposto['ISS']['base_legal']}"
        ]
        
        return resultado
    
    def _gerar_observacoes_legais(self, regimes_por_imposto):
        """Gera observações legais sobre os regimes aplicados"""
        observacoes = []
        
        # Verificar se há regimes mistos
        regimes_utilizados = set(r['regime'] for r in regimes_por_imposto.values())
        
        if len(regimes_utilizados) > 1:
            observacoes.append("⚠️ REGIME MISTO APLICADO:")
            observacoes.append("• ISS: Sempre competência (Lei Complementar 116/2003)")
            
            if any(r['regime'] == REGIME_TRIBUTACAO_CAIXA for r in regimes_por_imposto.values() if r != regimes_por_imposto['ISS']):
                observacoes.append("• PIS/COFINS/IRPJ/CSLL: Regime de caixa (Lei 9.718/1998)")
            else:
                observacoes.append("• PIS/COFINS/IRPJ/CSLL: Regime de competência")
        else:
            regime_unico = list(regimes_utilizados)[0]
            if regime_unico == REGIME_TRIBUTACAO_COMPETENCIA:
                observacoes.append("✓ REGIME DE COMPETÊNCIA aplicado para todos os impostos")
            else:
                observacoes.append("⚠️ Regime de caixa aplicado (exceto ISS que é sempre competência)")
        
        observacoes.extend([
            "",
            "PRAZOS DE RECOLHIMENTO:",
            "• ISS: Conforme cronograma municipal",
            "• PIS/COFINS: Até o 25º dia do mês seguinte",
            "• IRPJ/CSLL: Conforme opção (mensal ou trimestral)"
        ])
        
        return observacoes
    
    def _obter_info_regime_tributario(self, empresa):
        """Obtém informações sobre o regime tributário atual"""
        if not empresa:
            return {
                'codigo': REGIME_TRIBUTACAO_COMPETENCIA,
                'nome': 'Competência (padrão)',
                'observacoes': ['Regime não especificado - usando competência como padrão']
            }
        
        return {
            'codigo': empresa.regime_tributario,
            'nome': empresa.regime_tributario_nome,
            'observacoes': self._obter_observacoes_regime(empresa.regime_tributario)
        }
    
    def _obter_regime_vigente_na_data(self, empresa, data_referencia):
        """
        Obtém o regime tributário vigente para uma empresa em uma data específica
        
        Args:
            empresa: Instância da empresa
            data_referencia: Data para consulta
            
        Returns:
            dict: Informações do regime tributário vigente na data
        """
        if not empresa:
            return {
                'codigo': REGIME_TRIBUTACAO_COMPETENCIA,
                'nome': 'Competência (padrão)',
                'observacoes': ['Empresa não especificada - usando competência como padrão'],
                'fonte': 'padrao'
            }
        
        # Buscar no histórico de regimes
        regime_historico = RegimeTributarioHistorico.obter_regime_vigente(empresa, data_referencia)
        
        if regime_historico:
            return {
                'codigo': regime_historico.regime_tributario,
                'nome': regime_historico.get_regime_tributario_display(),
                'observacoes': self._obter_observacoes_regime(regime_historico.regime_tributario, data_referencia),
                'periodo_vigencia': {
                    'inicio': regime_historico.data_inicio,
                    'fim': regime_historico.data_fim
                },
                'fonte': 'historico'
            }
        else:
            # Fallback para o regime atual da empresa (compatibilidade)
            return {
                'codigo': empresa.regime_tributario,
                'nome': empresa.regime_tributario_nome,
                'observacoes': self._obter_observacoes_regime(empresa.regime_tributario, data_referencia) + 
                              ['⚠️ Regime obtido da configuração atual da empresa - recomenda-se configurar histórico'],
                'fonte': 'empresa_atual'
            }
    
    def _aplicar_regime_competencia(self, resultado_base, data_referencia=None):
        """
        Aplica regras específicas do regime de competência
        
        No regime de competência:
        - Impostos são devidos no mês da prestação do serviço
        - Não há diferimento por recebimento
        - Cálculo padrão se aplica
        """
        resultado_base['regime_observacoes'] = [
            "Regime de Competência:",
            "• Impostos devidos no mês da prestação do serviço",
            "• Independe da data de recebimento",
            "• Recolhimento conforme cronograma legal"
        ]
        
        return resultado_base
    
    def _aplicar_regime_caixa(self, resultado_base, data_referencia=None):
        """
        Aplica regras específicas do regime de caixa
        
        No regime de caixa:
        - Impostos são devidos no mês do recebimento
        - Pode haver diferimento se recebimento for em mês posterior
        - Ajustes podem ser necessários
        """
        from django.utils import timezone
        
        resultado = resultado_base.copy()
        
        # Se não há data de referência, usar hoje
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        resultado['regime_observacoes'] = [
            "Regime de Caixa:",
            "• Impostos devidos no mês do recebimento",
            "• Diferimento permitido conforme legislação",
            "• Atenção aos prazos de recolhimento"
        ]
        
        # No regime de caixa, pode haver diferimento
        # Aqui podem ser implementadas regras específicas se necessário
        resultado['permite_diferimento'] = True
        resultado['data_base_calculo'] = data_referencia
        
        return resultado
    
    def _obter_observacoes_regime(self, regime, data_referencia=None):
        """Retorna observações específicas sobre o regime tributário"""
        if regime == REGIME_TRIBUTACAO_CAIXA:
            observacoes = [
                "Regime de Caixa aplicado",
                "Impostos calculados para recolhimento no mês do recebimento",
                "Verifique cronograma específico de cada imposto"
            ]
        else:
            observacoes = [
                "Regime de Competência aplicado", 
                "Impostos calculados para recolhimento no mês da prestação",
                "Cronograma padrão de recolhimento"
            ]
        
        # Adicionar informação sobre data de referência se fornecida
        if data_referencia:
            hoje = timezone.now().date()
            if data_referencia < hoje:
                observacoes.append(f"⏰ Cálculo para data passada: {data_referencia}")
            elif data_referencia > hoje:
                observacoes.append(f"📅 Cálculo para data futura: {data_referencia}")
        
        return observacoes
    
    @classmethod
    def obter_aliquota_vigente(cls, conta, data_referencia=None):
        """Obtém a configuração de alíquotas vigente para uma conta"""
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        return cls.objects.filter(
            conta=conta,
            ativa=True,
            data_vigencia_inicio__lte=data_referencia
        ).filter(
            models.Q(data_vigencia_fim__isnull=True) | 
            models.Q(data_vigencia_fim__gte=data_referencia)
        ).first()
    
    @classmethod
    def obter_aliquota_ou_padrao(cls, conta, tipo_servico='consultas', data_referencia=None):
        """
        Obtém a alíquota ISS específica ou valor padrão se não houver configuração
        
        Args:
            conta: Conta para buscar configuração
            tipo_servico: 'consultas', 'plantao' ou 'outros'
            data_referencia: Data para qual buscar a alíquota (default: hoje)
            
        Returns:
            Decimal: Alíquota a ser aplicada
        """
        aliquotas = cls.obter_aliquota_vigente(conta, data_referencia)
        
        if aliquotas:
            if tipo_servico == 'consultas':
                return aliquotas.ISS_CONSULTAS
            elif tipo_servico == 'plantao':
                return aliquotas.ISS_PLANTAO
            elif tipo_servico == 'outros':
                return aliquotas.ISS_OUTROS
        
        # Valores padrão baseados na legislação comum quando não há configuração
        valores_padrao = {
            'consultas': 2.00,  # 2% - alíquota comum para consultas
            'plantao': 2.00,    # 2% - alíquota comum para plantões  
            'outros': 3.00,     # 3% - alíquota comum para procedimentos
        }
        
        return valores_padrao.get(tipo_servico, 2.00)
    
    @classmethod
    def calcular_impostos_para_empresa(cls, empresa, valor_bruto, tipo_servico='consultas', data_referencia=None):
        """
        Método de conveniência para calcular impostos considerando a empresa e seu regime
        
        Args:
            empresa: Instância da empresa
            valor_bruto: Valor bruto da nota fiscal
            tipo_servico: Tipo de serviço prestado
            data_referencia: Data para cálculo
            
        Returns:
            dict: Detalhamento completo dos impostos
        """
        aliquotas = cls.obter_aliquota_vigente(empresa.conta, data_referencia)
        
        if aliquotas:
            return aliquotas.calcular_impostos_com_regime(
                valor_bruto=valor_bruto,
                tipo_servico=tipo_servico,
                empresa=empresa,
                data_referencia=data_referencia
            )
        else:
            # Fallback - cálculo básico usando alíquotas padrão
            from decimal import Decimal
            
            aliquota_iss = cls.obter_aliquota_ou_padrao(empresa.conta, tipo_servico, data_referencia)
            valor_iss = valor_bruto * (aliquota_iss / 100)
            
            return {
                'valor_bruto': valor_bruto,
                'valor_iss': valor_iss,
                'valor_liquido': valor_bruto - valor_iss,
                'aliquota_iss_aplicada': aliquota_iss,
                'regime_tributario': {
                    'codigo': empresa.regime_tributario,
                    'nome': empresa.regime_tributario_nome,
                    'observacoes': ['Cálculo básico - configure alíquotas da conta para cálculo completo']
                },
                'observacao': 'Cálculo simplificado - recomenda-se configurar alíquotas específicas da conta'
            }





class NotaFiscal(models.Model):
    """
    Modelo para gerenciamento de Notas Fiscais de Serviços
    
    Este modelo representa as notas fiscais emitidas pelas empresas prestadoras de serviços,
    incluindo o cálculo automático de impostos (ISS, PIS, COFINS, IRPJ, CSLL) baseado
    nas alíquotas configuradas e no regime tributário vigente.
    
    Integra-se com o sistema de meios de pagamento e controle de recebimento,
    permitindo rastreamento completo do ciclo financeiro das notas fiscais.
    """
    
    class Meta:
        db_table = 'nota_fiscal'
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        unique_together = [['numero', 'serie', 'empresa_destinataria']]
        indexes = [
            models.Index(fields=['numero', 'serie']),
            models.Index(fields=['empresa_destinataria', 'dtEmissao']),
            models.Index(fields=['tomador', 'dtEmissao']),
            models.Index(fields=['status_recebimento', 'dtVencimento']),
            models.Index(fields=['dtEmissao', 'val_bruto']),
            models.Index(fields=['tipo_aliquota', 'dtEmissao']),
        ]
        ordering = ['-dtEmissao', '-numero']

    # === IDENTIFICAÇÃO DA NOTA FISCAL ===
    numero = models.CharField(
        max_length=20,
        verbose_name="Número da NF",
        help_text="Número sequencial da nota fiscal"
    )
    
    serie = models.CharField(
        max_length=10, 
        default="1",
        verbose_name="Série",
        help_text="Série da nota fiscal (geralmente 1)"
    )
    
    empresa_destinataria = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='notas_fiscais_emitidas',
        verbose_name="Empresa Emitente",
        help_text="Empresa que emitiu a nota fiscal"
    )
    
    tomador = models.CharField(
        max_length=200,
        verbose_name="Tomador do Serviço", 
        help_text="Nome da empresa/pessoa que tomou o serviço"
    )
    
    # === TIPO DE SERVIÇO E ALÍQUOTAS ===
    TIPO_ALIQUOTA_CHOICES = [
        (NFISCAL_ALIQUOTA_CONSULTAS, 'Consultas Médicas'),
        (NFISCAL_ALIQUOTA_PLANTAO, 'Plantão Médico'),
        (NFISCAL_ALIQUOTA_OUTROS, 'Vacinação/Exames/Procedimentos'),
    ]
    
    tipo_aliquota = models.IntegerField(
        choices=TIPO_ALIQUOTA_CHOICES,
        default=NFISCAL_ALIQUOTA_CONSULTAS,
        verbose_name="Tipo de Serviço",
        help_text="Tipo de serviço prestado para aplicação da alíquota correta de ISS"
    )
    
    descricao_servicos = models.TextField(
        verbose_name="Descrição dos Serviços",
        help_text="Descrição detalhada dos serviços prestados"
    )
    
    # === DATAS ===
    dtEmissao = models.DateField(
        verbose_name="Data de Emissão",
        help_text="Data de emissão da nota fiscal"
    )
    
    dtVencimento = models.DateField(
        null=True, blank=True,
        verbose_name="Data de Vencimento",
        help_text="Data de vencimento para pagamento"
    )
    
    dtRecebimento = models.DateField(
        null=True, blank=True,
        verbose_name="Data de Recebimento",
        help_text="Data efetiva do recebimento do pagamento"
    )
    
    # === VALORES FINANCEIROS ===
    val_bruto = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Valor Bruto (R$)",
        help_text="Valor bruto da nota fiscal antes dos impostos"
    )
    
    val_ISS = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor ISS (R$)",
        help_text="Valor do Imposto sobre Serviços (ISS)"
    )
    
    val_PIS = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor PIS (R$)",
        help_text="Valor da contribuição para o PIS"
    )
    
    val_COFINS = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor COFINS (R$)",
        help_text="Valor da contribuição para o COFINS"
    )
    
    val_IR = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor IRPJ (R$)",
        help_text="Valor do Imposto de Renda Pessoa Jurídica"
    )
    
    val_CSLL = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor CSLL (R$)",
        help_text="Valor da Contribuição Social sobre o Lucro Líquido"
    )
    
    val_liquido = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Valor Líquido (R$)",
        help_text="Valor líquido após dedução dos impostos"
    )
    
    # === CONTROLE DE RECEBIMENTO ===
    STATUS_RECEBIMENTO_CHOICES = [
        ('pendente', 'Pendente'),
        ('completo', 'Recebido Completamente'),
        ('cancelado', 'Cancelado'),
    ]
    
    status_recebimento = models.CharField(
        max_length=20,
        choices=STATUS_RECEBIMENTO_CHOICES,
        default='pendente',
        verbose_name="Status do Recebimento",
        help_text="Status atual do recebimento da nota fiscal"
    )
    
    # === INTEGRAÇÃO COM MEIO DE PAGAMENTO ===
    meio_pagamento = models.ForeignKey(
        'MeioPagamento',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notas_fiscais',
        verbose_name="Meio de Pagamento",
        help_text="Meio de pagamento utilizado para recebimento"
    )
    
    # === CONTROLE E AUDITORIA SIMPLIFICADO ===
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notas_fiscais_criadas',
        verbose_name="Criado por"
    )

    def clean(self):
        """Validações do modelo"""
        # Validar datas
        if self.dtVencimento and self.dtEmissao and self.dtVencimento < self.dtEmissao:
            raise ValidationError({
                'dtVencimento': 'Data de vencimento não pode ser anterior à data de emissão'
            })
        
        if self.dtRecebimento and self.dtEmissao and self.dtRecebimento < self.dtEmissao:
            raise ValidationError({
                'dtRecebimento': 'Data de recebimento não pode ser anterior à data de emissão'
            })
        
        # Validar valores
        if self.val_bruto <= 0:
            raise ValidationError({
                'val_bruto': 'Valor bruto deve ser maior que zero'
            })
        
        # Validar total de impostos vs valor bruto
        total_impostos = (self.val_ISS + self.val_PIS + self.val_COFINS + 
                         self.val_IR + self.val_CSLL)
        
        if total_impostos > self.val_bruto:
            raise ValidationError({
                'val_bruto': 'Total de impostos não pode ser maior que o valor bruto'
            })
        
        # Validar valor líquido
        valor_liquido_calculado = self.val_bruto - total_impostos
        if abs(self.val_liquido - valor_liquido_calculado) > 0.01:  # Tolerância de 1 centavo
            raise ValidationError({
                'val_liquido': f'Valor líquido deve ser R$ {valor_liquido_calculado:.2f} '
                              f'(valor bruto - impostos)'
            })
        
        # Validar meio de pagamento quando há recebimento
        if self.dtRecebimento and not self.meio_pagamento:
            raise ValidationError({
                'meio_pagamento': 'Meio de pagamento é obrigatório quando há data de recebimento'
            })
        
        # Validar consistência do status de recebimento
        if self.status_recebimento == 'completo' and not self.dtRecebimento:
            raise ValidationError({
                'status_recebimento': 'Status "Recebido Completamente" requer data de recebimento'
            })
        
        # NOVA REGRA: Validar que toda nota fiscal deve ter pelo menos um sócio vinculado
        if self.pk:  # Apenas para notas já salvas (para permitir criação inicial)
            total_rateios = self.rateios_medicos.count()
            if total_rateios == 0:
                raise ValidationError({
                    '__all__': 'Toda nota fiscal deve ter pelo menos um sócio/médico vinculado através do rateio. '
                              'Configure o rateio antes de finalizar a nota fiscal.'
                })
            
            # Validar que a soma dos valores de rateio corresponde ao valor bruto da nota
            soma_valores_rateio = sum(
                rateio.valor_bruto_medico for rateio in self.rateios_medicos.all()
            )
            if abs(soma_valores_rateio - self.val_bruto) > 0.01:  # Tolerância de 1 centavo
                raise ValidationError({
                    '__all__': f'A soma dos valores de rateio (R$ {soma_valores_rateio:.2f}) deve '
                              f'corresponder ao valor bruto da nota fiscal (R$ {self.val_bruto:.2f}). '
                              'Ajuste os valores de rateio para os sócios.'
                })

    def save(self, *args, **kwargs):
        """Override do save para cálculos automáticos"""
        # Se é uma nova nota ou os valores básicos mudaram, recalcular impostos
        if (not self.pk or 
            'val_bruto' in kwargs.get('update_fields', []) or
            'tipo_aliquota' in kwargs.get('update_fields', [])):
            self.calcular_impostos()
        
        # Atualizar status de recebimento automaticamente
        self.atualizar_status_recebimento()
        
        super().save(*args, **kwargs)

    def calcular_impostos(self):
        """
        Calcula todos os impostos baseado nas alíquotas configuradas
        e no regime tributário vigente na data de emissão
        """
        try:
            # Obter alíquotas vigentes para a conta da empresa
            conta = self.empresa_destinataria.conta
            aliquotas = Aliquotas.obter_aliquota_vigente(conta, self.dtEmissao)
            
            if aliquotas:
                # Determinar tipo de serviço para as alíquotas
                tipo_servico_map = {
                    NFISCAL_ALIQUOTA_CONSULTAS: 'consultas',
                    NFISCAL_ALIQUOTA_PLANTAO: 'plantao',
                    NFISCAL_ALIQUOTA_OUTROS: 'outros',
                }
                tipo_servico = tipo_servico_map.get(self.tipo_aliquota, 'consultas')
                
                # Calcular impostos considerando regime tributário
                resultado = aliquotas.calcular_impostos_com_regime(
                    valor_bruto=self.val_bruto,
                    tipo_servico=tipo_servico,
                    empresa=self.empresa_destinataria,
                    data_referencia=self.dtEmissao
                )
                
                # Aplicar valores calculados
                self.val_ISS = resultado['valor_iss']
                self.val_PIS = resultado['valor_pis']
                self.val_COFINS = resultado['valor_cofins']
                self.val_IR = resultado['valor_ir']
                self.val_CSLL = resultado['valor_csll']
                self.val_liquido = resultado['valor_liquido']
                
            else:
                # Fallback: cálculo básico usando apenas ISS padrão
                aliquota_iss = Aliquotas.obter_aliquota_ou_padrao(
                    conta, 
                    tipo_servico_map.get(self.tipo_aliquota, 'consultas'),
                    self.dtEmissao
                )
                
                self.val_ISS = self.val_bruto * (aliquota_iss / 100)
                self.val_PIS = 0
                self.val_COFINS = 0
                self.val_IR = 0
                self.val_CSLL = 0
                self.val_liquido = self.val_bruto - self.val_ISS
                
        except Exception as e:
            # Em caso de erro, manter valores zerados para impostos federais
            # e calcular apenas ISS básico
            self.val_ISS = self.val_bruto * 0.02  # 2% padrão
            self.val_PIS = 0
            self.val_COFINS = 0
            self.val_IR = 0
            self.val_CSLL = 0
            self.val_liquido = self.val_bruto - self.val_ISS

    def atualizar_status_recebimento(self):
        """Atualiza o status de recebimento baseado na data de recebimento"""
        if not self.dtRecebimento:
            self.status_recebimento = 'pendente'
        else:
            self.status_recebimento = 'completo'

    def __str__(self):
        return f"NF {self.numero}/{self.serie} - {self.tomador} - R$ {self.val_bruto:.2f}"

    @property
    def total_impostos(self):
        """Retorna o total de impostos da nota fiscal"""
        return self.val_ISS + self.val_PIS + self.val_COFINS + self.val_IR + self.val_CSLL

    @property
    def percentual_impostos(self):
        """Retorna o percentual total de impostos sobre o valor bruto"""
        if self.val_bruto > 0:
            return (self.total_impostos / self.val_bruto) * 100
        return 0

    @property
    def dias_atraso(self):
        """Retorna quantos dias de atraso no pagamento"""
        if not self.dtVencimento or self.status_recebimento == 'completo':
            return 0
        
        hoje = timezone.now().date()
        if hoje > self.dtVencimento:
            return (hoje - self.dtVencimento).days
        return 0

    @property
    def eh_vencida(self):
        """Verifica se a nota fiscal está vencida"""
        return self.dias_atraso > 0

    @property
    def tem_rateio_configurado(self):
        """Verifica se a nota fiscal tem rateio configurado"""
        return self.rateios_medicos.exists()

    @property
    def total_socios_rateio(self):
        """Retorna o número de sócios no rateio"""
        return self.rateios_medicos.count()

    def criar_rateio_unico_medico(self, medico, observacoes=""):
        """
        Cria rateio para um único médico (100% para ele)
        
        Args:
            medico: Instância do Socio (médico)
            observacoes: Observações sobre o rateio
        """
        # Limpar rateios existentes
        self.rateios_medicos.all().delete()
        
        # Criar novo rateio único
        return NotaFiscalRateioMedico.objects.create(
            nota_fiscal=self,
            medico=medico,
            percentual_participacao=100.00,
            valor_bruto_medico=self.val_bruto,  # 100% do valor para o médico
            tipo_rateio='automatico',
            data_rateio=timezone.now().date(),
            observacoes_rateio=observacoes or 'Rateio único - 100% para um médico'
        )

    def criar_rateio_multiplos_medicos(self, medicos_lista, observacoes=""):
        """
        Cria rateio igualitário entre múltiplos médicos
        
        Args:
            medicos_lista: Lista de instâncias de Socio (médicos)
            observacoes: Observações sobre o rateio
        """
        if not medicos_lista:
            raise ValidationError("Lista de médicos não pode estar vazia")
        
        # Validar se todos os médicos pertencem à mesma empresa
        empresa_nf = self.empresa_destinataria
        for medico in medicos_lista:
            if medico.empresa != empresa_nf:
                raise ValidationError(
                    'Todos os médicos do rateio devem pertencer à mesma empresa da nota fiscal'
                )
        
        # Limpar rateios existentes
        self.rateios_medicos.all().delete()
        
        # Calcular percentual e valor por médico
        num_medicos = len(medicos_lista)
        percentual_por_medico = 100.00 / num_medicos
        valor_por_medico = self.val_bruto / num_medicos
        
        # Criar rateios
        rateios_criados = []
        for medico in medicos_lista:
            rateio = NotaFiscalRateioMedico.objects.create(
                nota_fiscal=self,
                medico=medico,
                percentual_participacao=percentual_por_medico,
                valor_bruto_medico=valor_por_medico,
                tipo_rateio='automatico',
                data_rateio=timezone.now().date(),
                observacoes_rateio=observacoes or f'Rateio automático entre {num_medicos} médicos'
            )
            rateios_criados.append(rateio)
        
        return rateios_criados

    @classmethod
    def obter_resumo_financeiro_por_medico(cls, empresa=None, medico=None, periodo_inicio=None, periodo_fim=None):
        """
        Obtém resumo financeiro das notas fiscais por médico (considerando rateios)
        
        Args:
            empresa: Filtrar por empresa específica
            medico: Filtrar por médico específico
            periodo_inicio: Data de início do período
            periodo_fim: Data de fim do período
            
        Returns:
            dict: Resumo com totais por médico
        """
        from django.db.models import Sum, Count, Avg
        
        # Filtrar notas fiscais
        qs_notas = cls.objects.all()
        
        if empresa:
            qs_notas = qs_notas.filter(empresa_destinataria=empresa)
        
        if periodo_inicio:
            qs_notas = qs_notas.filter(dtEmissao__gte=periodo_inicio)
        
        if periodo_fim:
            qs_notas = qs_notas.filter(dtEmissao__lte=periodo_fim)
        
        # Obter rateios relacionados
        qs_rateios = NotaFiscalRateioMedico.objects.filter(
            nota_fiscal__in=qs_notas
        )
        
        if medico:
            qs_rateios = qs_rateios.filter(medico=medico)
        
        # Agregações por médico
        resumo_por_medico = qs_rateios.values(
            'medico__id',
            'medico__pessoa__name'
        ).annotate(
            total_notas=Count('nota_fiscal', distinct=True),
            valor_bruto_total=Sum('valor_bruto_medico'),
            valor_liquido_total=Sum('valor_liquido_medico'),
            valor_impostos_total=Sum(
                models.F('valor_iss_medico') + models.F('valor_pis_medico') + 
                models.F('valor_cofins_medico') + models.F('valor_ir_medico') + 
                models.F('valor_csll_medico')
            ),
            percentual_medio=Avg('percentual_participacao')
        ).order_by('-valor_bruto_total')
        
        # Totais gerais
        totais_gerais = qs_rateios.aggregate(
            total_notas_com_rateio=Count('nota_fiscal', distinct=True),
            valor_bruto_geral=Sum('valor_bruto_medico'),
            valor_liquido_geral=Sum('valor_liquido_medico'),
        )
        
        return {
            'resumo_por_medico': list(resumo_por_medico),
            'totais_gerais': totais_gerais,
            'filtros_aplicados': {
                'empresa': empresa.name if empresa else None,
                'medico': medico.pessoa.name if medico else None,
                'periodo': {
                    'inicio': periodo_inicio,
                    'fim': periodo_fim
                }
            }
        }

    def get_tipo_aliquota_display_extended(self):
        """Retorna descrição extendida do tipo de serviço"""
        descricoes = {
            NFISCAL_ALIQUOTA_CONSULTAS: 'Consultas Médicas - Atendimento ambulatorial',
            NFISCAL_ALIQUOTA_PLANTAO: 'Plantão Médico - Serviços de emergência e plantão',
            NFISCAL_ALIQUOTA_OUTROS: 'Outros Serviços - Vacinação, exames, procedimentos',
        }
        return descricoes.get(self.tipo_aliquota, self.get_tipo_aliquota_display())

    def get_status_recebimento_display_extended(self):
        """Retorna descrição extendida do status de recebimento"""
        if self.status_recebimento == 'pendente':
            if self.eh_vencida:
                return f"Pendente (vencida há {self.dias_atraso} dias)"
            return "Pendente"
        elif self.status_recebimento == 'completo':
            return f"Completo (recebido em {self.dtRecebimento})"
        return self.get_status_recebimento_display()

    def get_meio_pagamento_display(self):
        """Retorna nome do meio de pagamento ou 'Não definido'"""
        return self.meio_pagamento.nome if self.meio_pagamento else 'Não definido'

    # === MÉTODOS DE RATEIO ===
    
    @property
    def tem_rateio(self):
        """Verifica se a nota fiscal possui rateio configurado"""
        return self.rateios_medicos.exists()
    
    @property
    def total_medicos_rateio(self):
        """Retorna o número de médicos no rateio"""
        return self.rateios_medicos.count()
    
    @property
    def percentual_total_rateado(self):
        """Retorna o percentual total já rateado"""
        return self.rateios_medicos.aggregate(
            total=models.Sum('percentual_participacao')
        )['total'] or 0
    
    @property
    def valor_total_rateado(self):
        """Retorna o valor total já rateado"""
        return self.rateios_medicos.aggregate(
            total=models.Sum('valor_bruto_medico')
        )['total'] or 0
    
    @property
    def valor_pendente_rateio(self):
        """Retorna o valor ainda não rateado"""
        return self.val_bruto - self.valor_total_rateado
    
    @property
    def percentual_pendente_rateio(self):
        """Retorna o percentual ainda não rateado"""
        return 100 - self.percentual_total_rateado
    
    @property
    def rateio_completo(self):
        """Verifica se o rateio está completo (100%)"""
        return abs(self.percentual_total_rateado - 100) < 0.01
    
    def obter_rateio_resumo(self):
        """
        Obtém resumo do rateio da nota fiscal
        
        Returns:
            dict: Resumo com informações do rateio
        """
        rateios = self.rateios_medicos.select_related('medico__pessoa').all()
        
        resumo = {
            'tem_rateio': self.tem_rateio,
            'total_medicos': self.total_medicos_rateio,
            'percentual_total': self.percentual_total_rateado,
            'valor_total': self.valor_total_rateado,
            'valor_pendente': self.valor_pendente_rateio,
            'percentual_pendente': self.percentual_pendente_rateio,
            'rateio_completo': self.rateio_completo,
            'medicos': []
        }
        
        for rateio in rateios:
            resumo['medicos'].append({
                'medico_nome': rateio.medico.pessoa.name,
                'medico_crm': rateio.medico.pessoa.crm,
                'percentual': rateio.percentual_participacao,
                'valor_bruto': rateio.valor_bruto_medico,
                'valor_liquido': rateio.valor_liquido_medico,
                'total_impostos': rateio.total_impostos_medico,
                'tipo_rateio': rateio.get_tipo_rateio_display(),
                'observacoes': rateio.observacoes_rateio
            })
        
        return resumo
    
    def criar_rateio_unico_medico(self, medico, usuario=None):
        """
        Cria rateio para um único médico (100% para ele)
        
        Args:
            medico: Instância do Socio (médico)
            usuario: Usuário que está criando o rateio
        """
        # Limpar rateios existentes
        self.rateios_medicos.all().delete()
        
        # Criar rateio único
        NotaFiscalRateioMedico.objects.create(
            nota_fiscal=self,
            medico=medico,
            valor_bruto_medico=self.val_bruto,  # 100% do valor para o médico
            # percentual_participacao será calculado automaticamente como 100%
            tipo_rateio='percentual',
            configurado_por=usuario,
            observacoes_rateio='Rateio único - 100% para um médico'
        )
    
    def limpar_rateio(self):
        """Remove todos os rateios da nota fiscal"""
        self.rateios_medicos.all().delete()
    
    def validar_rateio_completo(self):
        """
        Valida se o rateio está completo e correto
        
        Raises:
            ValidationError: Se o rateio não estiver correto
        """
        if not self.tem_rateio:
            return  # Não é obrigatório ter rateio
        
        if not self.rateio_completo:
            raise ValidationError(
                f'Rateio incompleto. Total: {self.percentual_total_rateado:.2f}%. '
                f'Faltam {self.percentual_pendente_rateio:.2f}% para completar 100%.'
            )
        
        # Validar se todos os médicos pertencem à mesma empresa
        empresas_diferentes = self.rateios_medicos.exclude(
            medico__empresa=self.empresa_destinataria
        ).exists()
        
        if empresas_diferentes:
            raise ValidationError(
                'Todos os médicos do rateio devem pertencer à mesma empresa da nota fiscal'
            )

    @classmethod
    def obter_resumo_financeiro(cls, empresa=None, periodo_inicio=None, periodo_fim=None):
        """
        Obtém resumo financeiro das notas fiscais para análise gerencial
        
        Args:
            empresa: Filtrar por empresa específica
            periodo_inicio: Data de início do período
            periodo_fim: Data de fim do período
            
        Returns:
            dict: Resumo com totais e estatísticas
        """
        qs = cls.objects.filter(status='ativa')
        
        if empresa:
            qs = qs.filter(empresa_destinataria=empresa)
        
        if periodo_inicio:
            qs = qs.filter(dtEmissao__gte=periodo_inicio)
        
        if periodo_fim:
            qs = qs.filter(dtEmissao__lte=periodo_fim)
        
        from django.db.models import Sum, Count, Avg
        
        resumo = qs.aggregate(
            total_notas=Count('id'),
            valor_bruto_total=Sum('val_bruto'),
            valor_liquido_total=Sum('val_liquido'),
            total_impostos=Sum(
                models.F('val_ISS') + models.F('val_PIS') + 
                models.F('val_COFINS') + models.F('val_IR') + models.F('val_CSLL')
            ),
            valor_medio=Avg('val_bruto'),
        )
        
        # Adicionar estatísticas por status
        for status, _ in cls.STATUS_RECEBIMENTO_CHOICES:
            count = qs.filter(status_recebimento=status).count()
            resumo[f'total_{status}'] = count
        
        # Calcular valores pendentes (notas não recebidas)
        pendentes = qs.filter(status_recebimento='pendente').aggregate(
            valor_pendente=Sum('val_liquido')
        )
        resumo['valor_pendente'] = pendentes['valor_pendente'] or 0
        
        # Calcular vencidas
        hoje = timezone.now().date()
        vencidas = qs.filter(
            status_recebimento='pendente',
            dtVencimento__lt=hoje
        ).count()
        resumo['total_vencidas'] = vencidas
        
        return resumo
    
    @classmethod
    def obter_resumo_por_medico(cls, medico=None, empresa=None, periodo_inicio=None, periodo_fim=None):
        """
        Obtém resumo financeiro das notas fiscais por médico (considerando rateios)
        
        Args:
            medico: Filtrar por médico específico
            empresa: Filtrar por empresa específica
            periodo_inicio: Data de início do período
            periodo_fim: Data de fim do período
            
        Returns:
            dict: Resumo com totais por médico
        """
        from django.db.models import Sum, Count, Avg, Q
        
        # Base query para rateios
        rateios_qs = NotaFiscalRateioMedico.objects.select_related(
            'nota_fiscal', 'medico__pessoa'
        )
        
        if medico:
            rateios_qs = rateios_qs.filter(medico=medico)
        
        if empresa:
            rateios_qs = rateios_qs.filter(medico__empresa=empresa)
        
        if periodo_inicio:
            rateios_qs = rateios_qs.filter(nota_fiscal__dtEmissao__gte=periodo_inicio)
        
        if periodo_fim:
            rateios_qs = rateios_qs.filter(nota_fiscal__dtEmissao__lte=periodo_fim)
        
        # Agregações por médico
        resumo_por_medico = rateios_qs.values(
            'medico__id',
            'medico__pessoa__name',
            'medico__pessoa__crm'
        ).annotate(
            total_notas=Count('nota_fiscal', distinct=True),
            valor_bruto_total=Sum('valor_bruto_medico'),
            valor_liquido_total=Sum('valor_liquido_medico'),
            total_impostos=Sum(
                models.F('valor_iss_medico') + models.F('valor_pis_medico') + 
                models.F('valor_cofins_medico') + models.F('valor_ir_medico') + 
                models.F('valor_csll_medico')
            ),
            valor_medio=Avg('valor_bruto_medico'),
            percentual_medio=Avg('percentual_participacao')
        ).order_by('-valor_bruto_total')
        
        # Resumo geral
        totais_gerais = rateios_qs.aggregate(
            total_rateios=Count('id'),
            total_notas_com_rateio=Count('nota_fiscal', distinct=True),
            valor_bruto_geral=Sum('valor_bruto_medico'),
            valor_liquido_geral=Sum('valor_liquido_medico'),
            total_impostos_geral=Sum(
                models.F('valor_iss_medico') + models.F('valor_pis_medico') + 
                models.F('valor_cofins_medico') + models.F('valor_ir_medico') + 
                models.F('valor_csll_medico')
            )
        )
        
        return {
            'resumo_por_medico': list(resumo_por_medico),
            'totais_gerais': totais_gerais,
            'periodo': {
                'inicio': periodo_inicio,
                'fim': periodo_fim
            }
        }


class NotaFiscalRateioMedico(models.Model):
    """
    Rateio de Nota Fiscal entre Médicos/Sócios
    
    Este modelo permite que uma nota fiscal seja rateada entre um ou mais médicos,
    com base no valor bruto que cada um deve receber. A contabilidade pode configurar
    os percentuais ou valores específicos para cada médico participante.
    
    REGRA PRINCIPAL DE ENTRADA:
    - valor_bruto_medico: É o campo de ENTRADA - o usuário informa quanto cada médico deve receber
    - percentual_participacao: É CALCULADO AUTOMATICAMENTE a partir do valor_bruto_medico
    - Esta lógica garante que a entrada seja sempre por valor, com percentual para relatórios
    
    O sistema calcula automaticamente os impostos proporcionais para cada médico
    baseado na sua participação no valor total da nota fiscal.
    """
    
    class Meta:
        db_table = 'nota_fiscal_rateio_medico'
        verbose_name = "Rateio de NF por Médico"
        verbose_name_plural = "Rateios de NF por Médico"
        unique_together = [['nota_fiscal', 'medico']]
        indexes = [
            models.Index(fields=['nota_fiscal', 'medico']),
            models.Index(fields=['medico', 'data_rateio']),
            models.Index(fields=['nota_fiscal', 'percentual_participacao']),
        ]
        ordering = ['nota_fiscal', '-percentual_participacao']

    nota_fiscal = models.ForeignKey(
        'NotaFiscal',
        on_delete=models.CASCADE,
        related_name='rateios_medicos',
        verbose_name="Nota Fiscal",
        help_text="Nota fiscal que será rateada"
    )
    
    medico = models.ForeignKey(
        'Socio',
        on_delete=models.CASCADE,
        related_name='rateios_notas_fiscais',
        verbose_name="Médico/Sócio",
        help_text="Médico que receberá parte do valor da nota fiscal"
    )
    
    # === VALORES DO RATEIO ===
    percentual_participacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Participação (%)",
        help_text="Percentual de participação do médico no valor total da NF (CALCULADO AUTOMATICAMENTE)"
    )
    
    valor_bruto_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Bruto do Médico (R$)",
        help_text="Valor bruto que o médico receberá da nota fiscal (CAMPO DE ENTRADA PRINCIPAL)"
    )
    
    # === IMPOSTOS PROPORCIONAIS ===
    valor_iss_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="ISS do Médico (R$)",
        help_text="Valor proporcional de ISS para este médico"
    )
    
    valor_pis_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="PIS do Médico (R$)",
        help_text="Valor proporcional de PIS para este médico"
    )
    
    valor_cofins_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="COFINS do Médico (R$)",
        help_text="Valor proporcional de COFINS para este médico"
    )
    
    valor_ir_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="IRPJ do Médico (R$)",
        help_text="Valor proporcional de IRPJ para este médico"
    )
    
    valor_csll_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="CSLL do Médico (R$)",
        help_text="Valor proporcional de CSLL para este médico"
    )
    
    valor_liquido_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Líquido do Médico (R$)",
        help_text="Valor líquido que o médico receberá (bruto - impostos proporcionais)"
    )
    
    # === CONTROLE E CONFIGURAÇÃO ===
    tipo_rateio = models.CharField(
        max_length=20,
        choices=[
            ('percentual', 'Por Percentual'),
            ('valor_fixo', 'Por Valor Fixo'),
            ('automatico', 'Automático (Igual)'),
        ],
        default='percentual',
        verbose_name="Tipo de Rateio",
        help_text="Como foi definido o rateio para este médico"
    )
    
    observacoes_rateio = models.TextField(
        blank=True,
        verbose_name="Observações do Rateio",
        help_text="Observações sobre o critério usado para este rateio"
    )
    
    # === AUDITORIA ===
    data_rateio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do Rateio",
        help_text="Quando o rateio foi configurado"
    )
    
    configurado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rateios_nf_configurados',
        verbose_name="Configurado Por",
        help_text="Usuário que configurou este rateio"
    )
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def clean(self):
        """Validações do modelo"""
        # Validar percentual
        if self.percentual_participacao < 0 or self.percentual_participacao > 100:
            raise ValidationError({
                'percentual_participacao': 'Percentual deve estar entre 0 e 100%'
            })
        
        # Validar valor bruto
        if self.valor_bruto_medico <= 0:
            raise ValidationError({
                'valor_bruto_medico': 'Valor bruto deve ser maior que zero'
            })
        
        # Validar se médico pertence à mesma empresa da nota fiscal
        if (self.medico and self.nota_fiscal and 
            self.medico.empresa != self.nota_fiscal.empresa_destinataria):
            raise ValidationError({
                'medico': 'Médico deve pertencer à mesma empresa da nota fiscal'
            })
        
        # Validar se valor bruto do médico não excede valor da nota fiscal
        if (self.nota_fiscal and 
            self.valor_bruto_medico > self.nota_fiscal.val_bruto):
            raise ValidationError({
                'valor_bruto_medico': 'Valor do médico não pode exceder o valor total da nota fiscal'
            })

    def save(self, *args, **kwargs):
        """Override do save para cálculos automáticos"""
        # Calcular percentual automaticamente baseado no valor
        if self.nota_fiscal and self.nota_fiscal.val_bruto > 0:
            self.percentual_participacao = (
                self.valor_bruto_medico / self.nota_fiscal.val_bruto
            ) * 100
        
        # Calcular impostos proporcionais
        self.calcular_impostos_proporcionais()
        
        super().save(*args, **kwargs)

    def calcular_impostos_proporcionais(self):
        """Calcula os impostos proporcionais baseados na participação do médico"""
        if not self.nota_fiscal:
            return
        
        # Calcular proporção baseada no valor bruto
        if self.nota_fiscal.val_bruto > 0:
            proporcao = self.valor_bruto_medico / self.nota_fiscal.val_bruto
        else:
            proporcao = 0
        
        # Aplicar proporção aos impostos da nota fiscal
        self.valor_iss_medico = self.nota_fiscal.val_ISS * proporcao
        self.valor_pis_medico = self.nota_fiscal.val_PIS * proporcao
        self.valor_cofins_medico = self.nota_fiscal.val_COFINS * proporcao
        self.valor_ir_medico = self.nota_fiscal.val_IR * proporcao
        self.valor_csll_medico = self.nota_fiscal.val_CSLL * proporcao
        
        # Calcular valor líquido
        total_impostos_medico = (
            self.valor_iss_medico + self.valor_pis_medico + 
            self.valor_cofins_medico + self.valor_ir_medico + 
            self.valor_csll_medico
        )
        self.valor_liquido_medico = self.valor_bruto_medico - total_impostos_medico

    def __str__(self):
        return f"{self.nota_fiscal.numero} - {self.medico.pessoa.name} - {self.percentual_participacao}%"

    @property
    def total_impostos_medico(self):
        """Retorna o total de impostos deste médico"""
        return (
            self.valor_iss_medico + self.valor_pis_medico + 
            self.valor_cofins_medico + self.valor_ir_medico + 
            self.valor_csll_medico
        )

    @property
    def percentual_impostos_medico(self):
        """Retorna o percentual de impostos sobre o valor bruto do médico"""
        if self.valor_bruto_medico > 0:
            return (self.total_impostos_medico / self.valor_bruto_medico) * 100
        return 0
        if self.percentual_participacao < 0 or self.percentual_participacao > 100:
            raise ValidationError({
                'percentual_participacao': 'Percentual deve estar entre 0% e 100%'
            })
        
        # Validar valor bruto
        if self.valor_bruto_medico < 0:
            raise ValidationError({
                'valor_bruto_medico': 'Valor bruto não pode ser negativo'
            })
        
        # Validar se o médico pertence à mesma empresa da nota fiscal
        if (self.medico and self.nota_fiscal and 
            self.medico.empresa != self.nota_fiscal.empresa_destinataria):
            raise ValidationError({
                'medico': 'Médico deve pertencer à mesma empresa da nota fiscal'
            })
        
        # Validar se o valor não excede o valor total da nota fiscal
        if (self.nota_fiscal and 
            self.valor_bruto_medico > self.nota_fiscal.val_bruto):
            raise ValidationError({
                'valor_bruto_medico': 'Valor do médico não pode exceder o valor total da nota fiscal'
            })
        
        # NOTA: Não validamos coerência entre percentual e valor aqui porque
        # o percentual é sempre calculado automaticamente no método save()

    def save(self, *args, **kwargs):
        """Override do save para cálculos automáticos"""
        # REGRA PRINCIPAL: O valor_bruto_medico é a entrada, percentual_participacao é calculado
        # Sempre recalcular o percentual baseado no valor bruto informado
        if self.nota_fiscal and self.nota_fiscal.val_bruto > 0:
            self.percentual_participacao = (self.valor_bruto_medico / self.nota_fiscal.val_bruto) * 100
        
        # Recalcular impostos proporcionais
        self.calcular_impostos_proporcionais()
        
        # Validar antes de salvar
        self.full_clean()
        
        super().save(*args, **kwargs)
        
        # Após salvar, validar se o total dos rateios está correto
        self.validar_total_rateios()

    def calcular_impostos_proporcionais(self):
        """
        Calcula os impostos proporcionais baseado na participação do médico
        """
        if not self.nota_fiscal:
            return
        
        # Calcular impostos proporcionais baseado no percentual de participação
        fator_proporcional = self.percentual_participacao / 100
        
        self.valor_iss_medico = self.nota_fiscal.val_ISS * fator_proporcional
        self.valor_pis_medico = self.nota_fiscal.val_PIS * fator_proporcional
        self.valor_cofins_medico = self.nota_fiscal.val_COFINS * fator_proporcional
        self.valor_ir_medico = self.nota_fiscal.val_IR * fator_proporcional
        self.valor_csll_medico = self.nota_fiscal.val_CSLL * fator_proporcional
        
        # Calcular valor líquido
        total_impostos_medico = (
            self.valor_iss_medico + self.valor_pis_medico + 
            self.valor_cofins_medico + self.valor_ir_medico + self.valor_csll_medico
        )
        
        self.valor_liquido_medico = self.valor_bruto_medico - total_impostos_medico

    def validar_total_rateios(self):
        """
        Valida se o total dos rateios não excede 100% ou o valor total da nota fiscal
        """
        if not self.nota_fiscal:
            return
        
        # Buscar todos os rateios desta nota fiscal
        rateios = NotaFiscalRateioMedico.objects.filter(nota_fiscal=self.nota_fiscal)
        
        # Verificar total de percentuais
        total_percentual = sum(r.percentual_participacao for r in rateios)
        if total_percentual > 100.01:  # Tolerância de 0.01%
            raise ValidationError(
                f'Total dos percentuais de rateio ({total_percentual:.2f}%) '
                f'excede 100%. Ajuste os valores.'
            )
        
        # Verificar total de valores
        total_valor = sum(r.valor_bruto_medico for r in rateios)
        if total_valor > self.nota_fiscal.val_bruto + 0.01:  # Tolerância de 1 centavo
            raise ValidationError(
                f'Total dos valores de rateio (R$ {total_valor:.2f}) '
                f'excede o valor da nota fiscal (R$ {self.nota_fiscal.val_bruto:.2f})'
            )

    def atualizar_percentual_por_valor(self):
        """Atualiza o percentual baseado no valor bruto informado"""
        if self.nota_fiscal and self.nota_fiscal.val_bruto > 0:
            self.percentual_participacao = (self.valor_bruto_medico / self.nota_fiscal.val_bruto) * 100

    def atualizar_valor_por_percentual(self):
        """Atualiza o valor bruto baseado no percentual informado"""
        if self.nota_fiscal:
            self.valor_bruto_medico = self.nota_fiscal.val_bruto * (self.percentual_participacao / 100)

    def __str__(self):
        return (f"NF {self.nota_fiscal.numero}/{self.nota_fiscal.serie} - "
                f"{self.medico.pessoa.name} - {self.percentual_participacao:.2f}% "
                f"(R$ {self.valor_bruto_medico:.2f})")

    @property
    def total_impostos_medico(self):
        """Retorna o total de impostos do médico"""
        return (self.valor_iss_medico + self.valor_pis_medico + 
                self.valor_cofins_medico + self.valor_ir_medico + self.valor_csll_medico)

    @property
    def percentual_impostos_medico(self):
        """Retorna o percentual de impostos sobre o valor bruto do médico"""
        if self.valor_bruto_medico > 0:
            return (self.total_impostos_medico / self.valor_bruto_medico) * 100
        return 0

    @classmethod
    def criar_rateio_automatico(cls, nota_fiscal, medicos_lista, usuario=None):
        """
        Cria rateio automático igualitário entre os médicos informados
        
        Args:
            nota_fiscal: Instância da nota fiscal
            medicos_lista: Lista de instâncias de Socio (médicos)
            usuario: Usuário que está criando o rateio
            
        Returns:
            list: Lista dos rateios criados
        """
        if not medicos_lista:
            raise ValidationError("Lista de médicos não pode estar vazia")
        
        # Limpar rateios existentes
        cls.objects.filter(nota_fiscal=nota_fiscal).delete()
        
        # Calcular percentual igual para todos
        percentual_por_medico = 100 / len(medicos_lista)
        valor_por_medico = nota_fiscal.val_bruto / len(medicos_lista)
        
        rateios_criados = []
        for medico in medicos_lista:
            rateio = cls.objects.create(
                nota_fiscal=nota_fiscal,
                medico=medico,
                valor_bruto_medico=valor_por_medico,  # Valor é a entrada principal
                # percentual_participacao será calculado automaticamente no save()
                tipo_rateio='automatico',
                configurado_por=usuario,
                observacoes_rateio=f'Rateio automático igualitário entre {len(medicos_lista)} médicos'
            )
            rateios_criados.append(rateio)
        
        return rateios_criados

    @classmethod
    def criar_rateio_por_percentuais(cls, nota_fiscal, rateios_config, usuario=None):
        """
        Cria rateio baseado em percentuais específicos
        
        Args:
            nota_fiscal: Instância da nota fiscal
            rateios_config: Lista de dicts com 'medico' e 'percentual'
            usuario: Usuário que está criando o rateio
            
        Returns:
            list: Lista dos rateios criados
        """
        # Validar que o total dos percentuais não excede 100%
        total_percentual = sum(config['percentual'] for config in rateios_config)
        if total_percentual > 100:
            raise ValidationError(f'Total dos percentuais ({total_percentual}%) excede 100%')
        
        # Limpar rateios existentes
        cls.objects.filter(nota_fiscal=nota_fiscal).delete()
        
        rateios_criados = []
        for config in rateios_config:
            medico = config['medico']
            percentual = config['percentual']
            valor_bruto = nota_fiscal.val_bruto * (percentual / 100)
            
            rateio = cls.objects.create(
                nota_fiscal=nota_fiscal,
                medico=medico,
                valor_bruto_medico=valor_bruto,  # Valor calculado baseado no percentual desejado
                # percentual_participacao será calculado automaticamente no save()
                tipo_rateio='percentual',
                configurado_por=usuario,
                observacoes_rateio=config.get('observacoes', '')
            )
            rateios_criados.append(rateio)
        
        return rateios_criados

    @classmethod
    def criar_rateio_por_valores(cls, nota_fiscal, rateios_config, usuario=None):
        """
        Cria rateio baseado em valores específicos
        
        Args:
            nota_fiscal: Instância da nota fiscal
            rateios_config: Lista de dicts com 'medico' e 'valor'
            usuario: Usuário que está criando o rateio
            
        Returns:
            list: Lista dos rateios criados
        """
        # Validar que o total dos valores não excede o valor da nota fiscal
        total_valor = sum(config['valor'] for config in rateios_config)
        if total_valor > nota_fiscal.val_bruto:
            raise ValidationError(
                f'Total dos valores (R$ {total_valor:.2f}) excede o valor da '
                f'nota fiscal (R$ {nota_fiscal.val_bruto:.2f})'
            )
        
        # Limpar rateios existentes
        cls.objects.filter(nota_fiscal=nota_fiscal).delete()
        
        rateios_criados = []
        for config in rateios_config:
            medico = config['medico']
            valor = config['valor']
            # percentual será calculado automaticamente baseado no valor
            
            rateio = cls.objects.create(
                nota_fiscal=nota_fiscal,
                medico=medico,
                valor_bruto_medico=valor,  # Valor é a entrada principal
                # percentual_participacao será calculado automaticamente no save()
                tipo_rateio='valor_fixo',
                configurado_por=usuario,
                observacoes_rateio=config.get('observacoes', '')
            )
            rateios_criados.append(rateio)
        
        return rateios_criados
