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


class RegimeImpostoEspecifico(models.Model):
    """
    Controle específico de regime por tipo de imposto
    
    Este modelo permite configurar regimes diferentes para cada tipo de imposto,
    respeitando as particularidades legais de cada um:
    - ISS: Sempre regime de competência (LC 116/2003)
    - PIS/COFINS: Pode seguir regime da empresa se atender critérios
    - IRPJ/CSLL: Pode seguir regime da empresa se atender critérios
    """
    
    class Meta:
        db_table = 'regime_imposto_especifico'
        verbose_name = "Regime Específico por Imposto"
        verbose_name_plural = "Regimes Específicos por Imposto"
        unique_together = ['regime_historico', 'tipo_imposto']
        indexes = [
            models.Index(fields=['regime_historico', 'tipo_imposto']),
        ]

    # Tipos de impostos com regras específicas
    TIPO_IMPOSTO_CHOICES = [
        ('ISS', 'ISS - Imposto Sobre Serviços'),
        ('PIS', 'PIS - Programa de Integração Social'),
        ('COFINS', 'COFINS - Contribuição para Financiamento da Seguridade Social'),
        ('IRPJ', 'IRPJ - Imposto de Renda Pessoa Jurídica'),
        ('CSLL', 'CSLL - Contribuição Social sobre o Lucro Líquido'),
    ]
    
    regime_historico = models.ForeignKey(
        RegimeTributarioHistorico,
        on_delete=models.CASCADE,
        related_name='regimes_impostos',
        verbose_name="Regime Histórico"
    )
    
    tipo_imposto = models.CharField(
        max_length=10,
        choices=TIPO_IMPOSTO_CHOICES,
        verbose_name="Tipo de Imposto"
    )
    
    regime_aplicado = models.IntegerField(
        choices=RegimeTributarioHistorico.REGIME_CHOICES,
        verbose_name="Regime Aplicado",
        help_text="Regime efetivamente aplicado para este imposto específico"
    )
    
    observacoes_legais = models.TextField(
        blank=True,
        verbose_name="Observações Legais",
        help_text="Base legal e observações específicas para este imposto"
    )
    
    def clean(self):
        """Validações específicas por tipo de imposto"""
        # ISS sempre competência conforme LC 116/2003
        if (self.tipo_imposto == 'ISS' and 
            self.regime_aplicado != REGIME_TRIBUTACAO_COMPETENCIA):
            raise ValidationError({
                'regime_aplicado': 
                'ISS deve sempre seguir regime de competência conforme Lei Complementar 116/2003'
            })
        
        # Validar se empresa pode usar regime de caixa para outros impostos
        if (self.regime_aplicado == REGIME_TRIBUTACAO_CAIXA and 
            self.tipo_imposto in ['PIS', 'COFINS', 'IRPJ', 'CSLL']):
            
            empresa = self.regime_historico.empresa
            limite_receita = 78000000.00  # R$ 78 milhões
            
            receita_empresa = (empresa.receita_bruta_ano_anterior or 
                             self.regime_historico.receita_bruta_ano_anterior)
            
            if receita_empresa and receita_empresa > limite_receita:
                raise ValidationError({
                    'regime_aplicado': 
                    f'Empresa com receita de R$ {receita_empresa:,.2f} não pode usar '
                    f'regime de caixa para {self.tipo_imposto} (limite: R$ {limite_receita:,.2f})'
                })
    
    def save(self, *args, **kwargs):
        # Auto-preencher observações legais baseadas no tipo de imposto
        if not self.observacoes_legais:
            if self.tipo_imposto == 'ISS':
                self.observacoes_legais = (
                    "ISS sempre segue regime de competência conforme "
                    "Lei Complementar 116/2003, Art. 7º"
                )
            elif self.regime_aplicado == REGIME_TRIBUTACAO_CAIXA:
                self.observacoes_legais = (
                    f"Regime de caixa aplicado conforme Lei 9.718/1998, "
                    f"respeitando limite de receita bruta"
                )
            else:
                self.observacoes_legais = (
                    "Regime de competência aplicado conforme "
                    "Código Tributário Nacional, Art. 177"
                )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.regime_historico.empresa.name} - {self.tipo_imposto} - {self.get_regime_aplicado_display()}"
