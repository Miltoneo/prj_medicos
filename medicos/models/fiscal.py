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
    
    # Controle básico de receita para validação do regime de caixa
    receita_bruta_ano_anterior = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name="Receita Bruta Ano Anterior (R$)",
        help_text="Receita bruta do ano anterior (limite R$ 78 milhões para regime de caixa)"
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
        help_text="Observações sobre este período de regime tributário"
    )

    def clean(self):
        """Validações básicas do modelo"""
        # Validar datas
        if self.data_fim and self.data_inicio >= self.data_fim:
            raise ValidationError({
                'data_fim': 'Data fim deve ser posterior à data início'
            })
        
        # Validar limite de receita para regime de caixa
        if (self.regime_tributario == REGIME_TRIBUTACAO_CAIXA and 
            self.receita_bruta_ano_anterior and 
            self.receita_bruta_ano_anterior > 78000000.00):
            raise ValidationError({
                'receita_bruta_ano_anterior': 
                'Receita bruta excede o limite de R$ 78.000.000,00 para regime de caixa'
            })
        
        # Validar sobreposição de períodos
        if self.empresa_id:
            qs = RegimeTributarioHistorico.objects.filter(empresa=self.empresa)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            for regime in qs:
                if self._periodos_se_sobrepoe(regime):
                    raise ValidationError({
                        'data_inicio': 
                        f'Período sobrepõe com regime existente: {regime.data_inicio} - {regime.data_fim or "vigente"}'
                    })
    
    def _periodos_se_sobrepoe(self, outro_regime):
        """Verifica se dois períodos de regime se sobrepõem"""
        from datetime import date, timedelta
        
        # Se não há data fim, considera vigente por 100 anos
        data_futura = date.today() + timedelta(days=36500)
        
        inicio_self = self.data_inicio
        fim_self = self.data_fim or data_futura
        inicio_outro = outro_regime.data_inicio
        fim_outro = outro_regime.data_fim or data_futura
        
        # Períodos se sobrepõem se um não termina antes do outro começar
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
        """Obtém ou cria o regime tributário vigente para a empresa"""
        regime_atual = cls.obter_regime_vigente(empresa)
        
        if not regime_atual:
            regime_atual = cls.objects.create(
                empresa=empresa,
                regime_tributario=empresa.regime_tributario,
                data_inicio=timezone.now().date(),
                observacoes="Regime inicial criado automaticamente"
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
        # Permitir múltiplas configurações por empresa com vigências diferentes
        # A unicidade será garantida por validação personalizada
        indexes = [
            models.Index(fields=['empresa', 'ativa', 'data_vigencia_inicio']),
            models.Index(fields=['empresa', 'data_vigencia_inicio', 'data_vigencia_fim']),
        ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='aliquotas',
        null=False,
        verbose_name="Empresa",
        help_text="Empresa proprietária destas configurações tributárias"
    )
    
    # === IMPOSTOS MUNICIPAIS ===
    ISS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS (%)",
        help_text="Alíquota do ISS para prestação de serviços médicos em geral"
    )
    
    ISS_RETENCAO = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="ISS - Retenção (%)",
        help_text="Percentual de retenção de ISS aplicado pelo tomador de serviços (varia por município)"
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
    IRPJ_ALIQUOTA = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="IRPJ - Alíquota (%)",
        help_text="Alíquota normal do IRPJ (15% sobre a base de cálculo presumida, conforme Lei 9.249/1995, art. 3º)"
    )
    
    IRPJ_PRESUNCAO_OUTROS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="IRPJ - Presunção Outros Serviços (%)",
        help_text="Percentual da receita bruta presumido como lucro para outros serviços (32% conforme Lei 9.249/1995, art. 15, §1º, III, 'a')"
    )

    IRPJ_PRESUNCAO_CONSULTA = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="IRPJ - Presunção Consultas (%)",
        help_text="Percentual da receita bruta presumido como lucro para consultas médicas (32% conforme Lei 9.249/1995, art. 15, §1º, III, 'a')"
    )

    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = models.DecimalField(
        max_digits=10, decimal_places=2, null=False,
        verbose_name="IRPJ - Valor Base para Adicional (R$)",
        help_text="Valor base a partir do qual incide o adicional de IRPJ. Usado para cálculo do adicional conforme legislação."
    )
    IRPJ_ADICIONAL = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="IRPJ - Adicional (%)",
        help_text="Percentual adicional de IRPJ aplicado sobre o valor que exceder a base definida."
    )

    CSLL_ALIQUOTA = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="CSLL - Alíquota (%)",
        help_text="Alíquota da CSLL (9% sobre a base de cálculo presumida, conforme Lei 7.689/1988, art. 3º, com redação da Lei 13.169/2015)"
    )
    
    CSLL_PRESUNCAO_OUTROS = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="CSLL - Presunção Outros Serviços (%)",
        help_text="Percentual da receita bruta presumido como lucro para outros serviços (32% para serviços médicos, conforme Lei 9.249/1995, art. 20)"
    )
    
    CSLL_PRESUNCAO_CONSULTA = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=0,
        verbose_name="CSLL - Presunção Consultas (%)",
        help_text="Percentual da receita bruta presumido como lucro para consultas médicas (32% para serviços médicos, conforme Lei 9.249/1995, art. 20)"
    )
    
    # === RETENÇÃO NA FONTE ===
    IRPJ_RETENCAO_FONTE = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=1.5,
        verbose_name="IRPJ - Retenção na Fonte (%)",
        help_text="Alíquota de retenção de IRPJ na fonte aplicada pelo tomador de serviços (1,5% conforme IN RFB nº 1.234/2012)"
    )
    
    CSLL_RETENCAO_FONTE = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, default=1.0,
        verbose_name="CSLL - Retenção na Fonte (%)",
        help_text="Alíquota de retenção de CSLL na fonte aplicada pelo tomador de serviços (1,0% conforme IN RFB nº 1.234/2012)"
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
        """Validações simplificadas do modelo"""
        # Validar datas de vigência
        if (self.data_vigencia_inicio and self.data_vigencia_fim and 
            self.data_vigencia_inicio > self.data_vigencia_fim):
            raise ValidationError({
                'data_vigencia_fim': 'Data fim deve ser posterior à data início'
            })
        
        # REGRA: Só pode haver uma alíquota ativa por empresa
        if self.ativa:
            qs_ativas = Aliquotas.objects.filter(empresa=self.empresa, ativa=True)
            if self.pk:
                qs_ativas = qs_ativas.exclude(pk=self.pk)
            if qs_ativas.exists():
                raise ValidationError({
                    'ativa': 'Já existe uma alíquota ativa para esta empresa. Desative a configuração anterior antes de ativar uma nova.'
                })

    def __str__(self):
        return f"Alíquotas - {self.empresa.name} (ISS: {self.ISS}%)"
    
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
        
        # IRPJ e CSLL - Usar alíquotas de retenção na fonte para emissão de NF
        # Conforme IN RFB nº 1.234/2012: IRPJ 1,5% e CSLL 1,0% sobre valor bruto
        valor_ir_total = valor_bruto * (self.IRPJ_RETENCAO_FONTE / 100)
        valor_csll = valor_bruto * (self.CSLL_RETENCAO_FONTE / 100)
        
        # Base de cálculo para apuração (mantida para referência)
        base_calculo_ir = valor_bruto * (self.IRPJ_PRESUNCAO_OUTROS / 100)
        base_calculo_csll = valor_bruto * (self.CSLL_PRESUNCAO_OUTROS / 100)
        
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
            'aliquota_ir_retencao': self.IRPJ_RETENCAO_FONTE,
            'valor_csll': valor_csll,
            'aliquota_csll_retencao': self.CSLL_RETENCAO_FONTE,
            'total_impostos': total_impostos,
            'valor_liquido': valor_liquido,
            'base_calculo_ir': base_calculo_ir,
            'base_calculo_csll': base_calculo_csll,
            'regime_tributario': regime_info,
            'observacao': 'Impostos calculados com alíquotas de retenção na fonte (IR: 1,5%, CSLL: 1,0%)'
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
        """Gera observações legais simplificadas sobre os regimes aplicados"""
        return [
            "PRAZOS DE RECOLHIMENTO:",
            "• ISS: Conforme cronograma municipal",
            "• PIS/COFINS: Até o 25º dia do mês seguinte",
            "• IRPJ/CSLL: Conforme opção (mensal ou trimestral)"
        ]
    
    def _obter_info_regime_tributario(self, empresa):
        """Obtém informações sobre o regime tributário atual"""
        return {
            'codigo': empresa.regime_tributario,
            'nome': empresa.regime_tributario_nome,
            'observacoes': self._obter_observacoes_regime(empresa.regime_tributario)
        }
    
    def _obter_regime_vigente_na_data(self, empresa, data_referencia):
        """Obtém o regime tributário vigente para uma empresa em uma data específica"""
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
            return {
                'codigo': empresa.regime_tributario,
                'nome': empresa.regime_tributario_nome,
                'observacoes': self._obter_observacoes_regime(empresa.regime_tributario, data_referencia),
                'fonte': 'empresa_atual'
            }
    
    def _aplicar_regime_competencia(self, resultado_base, data_referencia=None):
        """Aplica regras específicas do regime de competência"""
        resultado_base['regime_observacoes'] = [
            "Regime de Competência:",
            "• Impostos devidos no mês da prestação do serviço",
            "• Recolhimento conforme cronograma legal"
        ]
        return resultado_base
    
    def _aplicar_regime_caixa(self, resultado_base, data_referencia=None):
        """Aplica regras específicas do regime de caixa"""
        resultado_base['regime_observacoes'] = [
            "Regime de Caixa:",
            "• Impostos devidos no mês do recebimento"
        ]
        resultado_base['permite_diferimento'] = True
        return resultado_base
    
    def _obter_observacoes_regime(self, regime, data_referencia=None):
        """Retorna observações específicas sobre o regime tributário"""
        if regime == REGIME_TRIBUTACAO_CAIXA:
            return ["Regime de Caixa aplicado"]
        else:
            return ["Regime de Competência aplicado"]
    
    @classmethod
    def obter_aliquota_vigente(cls, empresa, data_referencia=None):
        """Obtém a configuração de alíquotas vigente para uma empresa"""
        if data_referencia is None:
            data_referencia = timezone.now().date()
        return cls.objects.filter(
            empresa=empresa,
            ativa=True,
            data_vigencia_inicio__lte=data_referencia
        ).filter(
            models.Q(data_vigencia_fim__isnull=True) |
            models.Q(data_vigencia_fim__gte=data_referencia)
        ).first()
    
    @classmethod
    def calcular_impostos_para_empresa(cls, empresa, valor_bruto, tipo_servico='consultas', data_referencia=None):
        """Calcula impostos considerando a empresa e seu regime"""
        aliquotas = cls.obter_aliquota_vigente(empresa, data_referencia)
        
        return aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_bruto,
            tipo_servico=tipo_servico,
            empresa=empresa,
            data_referencia=data_referencia
        )


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
    
    val_outros = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor Outros (R$)",
        help_text="Outros valores a serem deduzidos do valor bruto"
    )
    
    val_liquido = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Valor Líquido (R$)",
        help_text="Valor líquido após dedução dos impostos e outros valores"
    )
    
    # === CONTROLE DE RECEBIMENTO ===
    STATUS_RECEBIMENTO_CHOICES = [
        ('pendente', 'Pendente'),
        ('recebido', 'Recebido'),
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
    from medicos.models.financeiro import MeioPagamento
    meio_pagamento = models.ForeignKey(
        MeioPagamento,
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
        """Validações simplificadas do modelo"""
        # Validar datas
        if self.dtVencimento and self.dtEmissao and self.dtVencimento < self.dtEmissao:
            raise ValidationError({
                'dtVencimento': 'Data de vencimento não pode ser anterior à data de emissão'
            })
        
        # Validar valores
        if self.val_bruto <= 0:
            raise ValidationError({
                'val_bruto': 'Valor bruto deve ser maior que zero'
            })
        
        # Validar valor líquido
        total_impostos = (self.val_ISS + self.val_PIS + self.val_COFINS + 
                         self.val_IR + self.val_CSLL)
        valor_liquido_calculado = self.val_bruto - total_impostos - self.val_outros
        if abs(self.val_liquido - valor_liquido_calculado) > 0.01:  # Tolerância de 1 centavo
            raise ValidationError({
                'val_liquido': f'Valor líquido deve ser R$ {valor_liquido_calculado:.2f} '
                              f'(valor bruto - impostos - outros valores)'
            })
        
        # Validar consistência do status de recebimento
        if self.status_recebimento == 'recebido' and not self.dtRecebimento:
            raise ValidationError({
                'status_recebimento': 'Status "Recebido" requer data de recebimento'
            })
        
        # Corrigir validação de unicidade para edição
        if self.pk:
            if NotaFiscal.objects.filter(
                numero=self.numero,
                serie=self.serie,
                empresa_destinataria=self.empresa_destinataria
            ).exclude(pk=self.pk).exists():
                raise ValidationError({
                    '__all__': 'Já existe uma nota fiscal com este número, série e empresa. Escolha outro número ou série.'
                })

    def save(self, *args, **kwargs):
        """Override do save para cálculos automáticos"""
        # Verificar se é importação de XML (não recalcular impostos)
        importacao_xml = kwargs.pop('importacao_xml', False)
        
        # Verificar se deve pular o recálculo (para preservar valores editados manualmente)
        pular_recalculo = kwargs.pop('pular_recalculo', False)
        
        # Verificar se realmente houve mudança nos campos que justifiquem recálculo
        deve_recalcular = False
        
        if not importacao_xml and not pular_recalculo:
            if not self.pk:
                # Nova nota - recalcular sempre
                deve_recalcular = True
            else:
                # Nota existente - verificar se campos relevantes mudaram
                if 'update_fields' in kwargs:
                    campos_relevantes = ['val_bruto', 'tipo_servico']
                    deve_recalcular = any(campo in kwargs.get('update_fields', []) for campo in campos_relevantes)
                else:
                    # Se não há update_fields, verificar se val_bruto ou tipo_servico mudaram
                    try:
                        nota_original = NotaFiscal.objects.get(pk=self.pk)
                        deve_recalcular = (
                            nota_original.val_bruto != self.val_bruto or
                            nota_original.tipo_servico != self.tipo_servico
                        )
                    except NotaFiscal.DoesNotExist:
                        # Se não conseguir obter a nota original, é uma nova nota
                        deve_recalcular = True
        
        if deve_recalcular:
            self.calcular_impostos()

        # Preencher aliquotas automaticamente se não estiver definido
        if not self.aliquotas:
            aliquota_vigente = Aliquotas.obter_aliquota_vigente(self.empresa_destinataria, self.dtEmissao)
            self.aliquotas = aliquota_vigente

        super().save(*args, **kwargs)

    def calcular_impostos(self):
        """Calcula todos os impostos baseado nas alíquotas configuradas"""
        aliquotas = Aliquotas.obter_aliquota_vigente(self.empresa_destinataria, self.dtEmissao)
        
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
        
        # Calcular valor líquido incluindo val_outros
        self.val_liquido = resultado['valor_liquido'] - self.val_outros

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
        elif self.status_recebimento == 'recebido':
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


class NotaFiscalRateioMedico(models.Model):
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    def save(self, *args, **kwargs):
        # Calculate all required fields before saving
        if self.nota_fiscal and self.valor_bruto_medico is not None:
            # CORREÇÃO: Usar valores já calculados da nota fiscal original
            # Em vez de recalcular, fazer rateio proporcional dos impostos da NF
            
            nota_fiscal = self.nota_fiscal
            valor_bruto_total = nota_fiscal.val_bruto
            
            if valor_bruto_total > 0:
                # Calcular proporção do rateio
                proporcao = self.valor_bruto_medico / valor_bruto_total
                
                # Ratear os impostos proporcionalmente baseado nos valores da NF original
                self.valor_iss_medico = (nota_fiscal.val_ISS or 0) * proporcao
                self.valor_pis_medico = (nota_fiscal.val_PIS or 0) * proporcao
                self.valor_cofins_medico = (nota_fiscal.val_COFINS or 0) * proporcao
                self.valor_ir_medico = (nota_fiscal.val_IR or 0) * proporcao
                self.valor_csll_medico = (nota_fiscal.val_CSLL or 0) * proporcao
                
                # Calcular valor líquido
                total_impostos_medico = (
                    self.valor_iss_medico + self.valor_pis_medico + 
                    self.valor_cofins_medico + self.valor_ir_medico + 
                    self.valor_csll_medico
                )
                self.valor_liquido_medico = self.valor_bruto_medico - total_impostos_medico
            else:
                # Se valor bruto zero, zerar todos os impostos
                self.valor_iss_medico = 0
                self.valor_pis_medico = 0
                self.valor_cofins_medico = 0
                self.valor_ir_medico = 0
                self.valor_csll_medico = 0
                self.valor_liquido_medico = 0
        
        # Set data_rateio if not provided
        if not self.data_rateio:
            from django.utils import timezone
            self.data_rateio = timezone.now()
        super().save(*args, **kwargs)
    """
    Rateio de Nota Fiscal para Médicos
    
    Este modelo representa o rateio de uma nota fiscal entre diferentes médicos,
    permitindo a distribuição proporcional dos valores e impostos.
    
    Cada rateio é associado a uma nota fiscal específica e a um médico,
    com campos para controle do percentual e valores rateados.
    """
    
    class Meta:
        db_table = 'nota_fiscal_rateio_medico'
        verbose_name = "Rateio de Nota Fiscal para Médico"
        verbose_name_plural = "Rateios de Nota Fiscal para Médicos"
        indexes = [
            models.Index(fields=['nota_fiscal', 'medico']),
            models.Index(fields=['medico', 'percentual_participacao']),
        ]
        ordering = ['medico__pessoa__name', 'nota_fiscal']  # Ordenação alfabética por nome do médico

    nota_fiscal = models.ForeignKey(
        'NotaFiscal',
        on_delete=models.CASCADE,
        related_name='rateios_medicos',
        verbose_name="Nota Fiscal",
        help_text="Nota fiscal associada a este rateio"
    )
    
    medico = models.ForeignKey(
        'Socio',
        on_delete=models.CASCADE,
        verbose_name="Médico",
        help_text="Médico ao qual este rateio se aplica"
    )
    
    percentual_participacao = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Percentual de Participação",
        help_text="Percentual do valor total da nota fiscal que este médico irá receber"
    )
    
    valor_bruto_medico = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Valor Bruto para Médico (R$)",
        help_text="Valor bruto da nota fiscal rateado para este médico"
    )
    
    valor_iss_medico = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor ISS para Médico (R$)",
        help_text="Valor do Imposto sobre Serviços (ISS) rateado para este médico"
    )
    
    valor_pis_medico = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor PIS para Médico (R$)",
        help_text="Valor da contribuição para o PIS rateado para este médico"
    )
    
    valor_cofins_medico = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor COFINS para Médico (R$)",
        help_text="Valor da contribuição para o COFINS rateado para este médico"
    )
    
    valor_ir_medico = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor IRPJ para Médico (R$)",
        help_text="Valor do Imposto de Renda Pessoa Jurídica rateado para este médico"
    )
    
    valor_csll_medico = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor CSLL para Médico (R$)",
        help_text="Valor da Contribuição Social sobre o Lucro Líquido rateado para este médico"
    )
    
    valor_liquido_medico = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Valor Líquido para Médico (R$)",
        help_text="Valor líquido após dedução dos impostos rateado para este médico"
    )
    
    tipo_rateio = models.CharField(
        max_length=50,
        verbose_name="Tipo de Rateio",
        help_text="Tipo de rateio aplicado (percentual, fixo, etc.)"
    )
    
    observacoes_rateio = models.TextField(
        blank=True, null=True,
        verbose_name="Observações sobre o Rateio",
        help_text="Observações adicionais sobre este rateio"
    )
    
    data_rateio = models.DateTimeField(
        verbose_name="Data do Rateio",
        help_text="Data em que o rateio foi realizado"
    )
    
    configurado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rateios_configurados',
        verbose_name="Configurado por"
    )

    def clean(self):
        # Validar que o total dos rateios não excede o valor bruto da nota fiscal
        total_rateado = NotaFiscalRateioMedico.objects.filter(
            nota_fiscal=self.nota_fiscal
        ).exclude(pk=self.pk).aggregate(
            total=models.Sum('valor_bruto_medico')
        )['total'] or 0
        if total_rateado + (self.valor_bruto_medico or 0) > self.nota_fiscal.val_bruto:
            raise ValidationError({
                'valor_bruto_medico': 'O total dos rateios não pode exceder o valor bruto da nota fiscal'
            })
        # Validar datas
        if self.data_rateio and self.data_rateio > timezone.now():
            raise ValidationError({
                'data_rateio': 'Data do rateio não pode ser futura'
            })

    def __str__(self):
        return f"Rateio NF {self.nota_fiscal.numero} - Médico {self.medico.pessoa.name}"
