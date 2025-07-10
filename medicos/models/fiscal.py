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
    
    # === IMPOSTOS MUNICIPAIS ===
    ISS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS (%)",
        help_text="Alíquota do ISS para prestação de serviços médicos em geral"
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
        help_text="Percentual da receita bruta para base de cálculo do IRPJ (32% para serviços médicos, conforme Lei 9.249/1995, art. 15, §1º, III, 'a')"
    )
    
    IRPJ_ALIQUOTA_OUTROS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=15.00,
        verbose_name="IRPJ - Alíquota Outros (%)",
        help_text="Alíquota normal do IRPJ para outros serviços (15% sobre a base de cálculo presumida, conforme Lei 9.249/1995, art. 3º)"
    )

    IRPJ_ALIQUOTA_CONSULTA = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="IRPJ - Alíquota Consulta (%)",
        help_text="Alíquota adicional do IRPJ para consultas. Não prevista na legislação federal padrão para serviços médicos."
    )

    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, default=20000.00,
        verbose_name="IRPJ - Valor Base para Adicional (R$)",
        help_text="Valor base a partir do qual incide o adicional de IRPJ. Usado para cálculo do adicional conforme legislação."
    )
    IRPJ_ADICIONAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=10.00,
        verbose_name="IRPJ - Adicional (%)",
        help_text="Percentual adicional de IRPJ aplicado sobre o valor que exceder a base definida."
    )

    CSLL_BASE_CAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=32.00,
        verbose_name="CSLL - Base de Cálculo (%)",
        help_text="Percentual da receita bruta para base de cálculo da CSLL (32% para serviços médicos, conforme Lei 9.249/1995, art. 20)"
    )
    
    CSLL_ALIQUOTA_OUTROS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=9.00,
        verbose_name="CSLL - Alíquota Outros (%)",
        help_text="Alíquota normal da CSLL para outros serviços (9% sobre a base de cálculo presumida, conforme Lei 7.689/1988, art. 3º, com redação da Lei 13.169/2015)"
    )
    
    CSLL_ALIQUOTA_CONSULTA = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=15.00,
        verbose_name="CSLL - Alíquota Consulta (%)",
        help_text="Alíquota adicional da CSLL para consultas. Não prevista na legislação federal padrão para serviços médicos."
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
            ('ISS', self.ISS, 0, 20),
            ('PIS', self.PIS, 0, 10),
            ('COFINS', self.COFINS, 0, 10),
            ('IRPJ_BASE_CAL', self.IRPJ_BASE_CAL, 0, 100),
            ('IRPJ_ALIQUOTA_OUTROS', self.IRPJ_ALIQUOTA_OUTROS, 0, 50),
            ('IRPJ_ALIQUOTA_CONSULTA', self.IRPJ_ALIQUOTA_CONSULTA, 0, 50),
            ('CSLL_BASE_CAL', self.CSLL_BASE_CAL, 0, 100),
            ('CSLL_ALIQUOTA_OUTROS', self.CSLL_ALIQUOTA_OUTROS, 0, 50),
            ('CSLL_ALIQUOTA_CONSULTA', self.CSLL_ALIQUOTA_CONSULTA, 0, 50),
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
        return f"Alíquotas - {self.conta.name} (ISS: {self.ISS}%)"
    
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
        
        # Usar apenas ISS único
        aliquota_iss = self.ISS
        descricao_servico = "Serviço Médico"
        
        # Cálculos básicos
        valor_iss = valor_bruto * (aliquota_iss / 100)
        valor_pis = valor_bruto * (self.PIS / 100)
        valor_cofins = valor_bruto * (self.COFINS / 100)
        
        # Base de cálculo para IR e CSLL
        base_calculo_ir = valor_bruto * (self.IRPJ_BASE_CAL / 100)
        base_calculo_csll = valor_bruto * (self.CSLL_BASE_CAL / 100)
        
        # IRPJ
        valor_ir_normal = base_calculo_ir * (self.IRPJ_ALIQUOTA_OUTROS / 100)
        valor_ir_adicional = 0
        if base_calculo_ir > self.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL:
            excesso = base_calculo_ir - self.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL
            valor_ir_adicional = excesso * (self.IRPJ_ADICIONAL / 100)
        
        valor_ir_total = valor_ir_normal + valor_ir_adicional
        
        # CSLL
        valor_csll = base_calculo_csll * (self.CSLL_ALIQUOTA_OUTROS / 100)
        
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
            models.Index(fields=['tipo_servico', 'dtEmissao']),  # Corrigido para tipo_servico
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

    cnpj_tomador = models.CharField(
        max_length=18,
        verbose_name="CNPJ do Tomador",
        help_text="Número do CNPJ do tomador do serviço (formato: 00.000.000/0000-00)",
        blank=True, null=True
    )
    
    # === TIPO DE SERVIÇO E ALÍQUOTAS ===
    TIPO_SERVICO_CONSULTAS = 1
    TIPO_SERVICO_OUTROS = 2
    TIPO_SERVICO_CHOICES = [
        (TIPO_SERVICO_CONSULTAS, 'Consultas Médicas'),
        (TIPO_SERVICO_OUTROS, 'Outros Serviços'),
    ]
    
    tipo_servico = models.IntegerField(
        choices=TIPO_SERVICO_CHOICES,
        default=TIPO_SERVICO_CONSULTAS,
        verbose_name="Tipo de Serviço",
        help_text="Tipo de serviço prestado (define a alíquota de IRPJ/CSLL)"
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
    
    aliquotas = models.ForeignKey(
        'Aliquotas',
        on_delete=models.PROTECT,
        related_name='notas_fiscais',
        verbose_name="Configuração de Alíquotas",
        help_text="Configuração de alíquotas utilizada no momento da emissão. Garante integridade histórica."
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
            'tipo_servico' in kwargs.get('update_fields', [])):
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
                    self.TIPO_SERVICO_CONSULTAS: 'consultas',
                    self.TIPO_SERVICO_OUTROS: 'outros',
                }
                tipo_servico = tipo_servico_map.get(self.tipo_servico, 'consultas')
                
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
                tipo_servico_map = {
                    self.TIPO_SERVICO_CONSULTAS: 'consultas',
                    self.TIPO_SERVICO_OUTROS: 'outros',
                }
                aliquota_iss = Aliquotas.obter_aliquota_ou_padrao(
                    conta, 
                    tipo_servico_map.get(self.tipo_servico, 'consultas'),
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

    def get_tipo_servico_display_extended(self):
        """Retorna descrição extendida do tipo de serviço"""
        descricoes = {
            self.TIPO_SERVICO_CONSULTAS: 'Consultas Médicas - Atendimento ambulatorial',
            self.TIPO_SERVICO_OUTROS: 'Outros Serviços - Vacinação, exames, procedimentos',
        }
        return descricoes.get(self.tipo_servico, self.get_tipo_servico_display())

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
