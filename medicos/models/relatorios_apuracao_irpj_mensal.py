"""
Modelo para Apuração IRPJ Mensal - Pagamento por Estimativa
Fonte: Lei 9.430/1996, Art. 2º - Pagamento mensal por estimativa

Este modelo armazena os cálculos mensais do IRPJ conforme permitido pelo
Art. 2º da Lei 9.430/1996, que faculta às pessoas jurídicas o pagamento
mensal sobre base de cálculo estimada.
"""

from django.db import models
from medicos.models.base import Empresa
from decimal import Decimal

class ApuracaoIRPJMensal(models.Model):
    """
    Apuração mensal do IRPJ por estimativa.
    
    Conforme Lei 9.430/1996, Art. 2º: "A pessoa jurídica sujeita a tributação 
    com base no lucro real poderá optar pelo pagamento do imposto, em cada mês, 
    determinado sobre base de cálculo estimada..."
    """
    
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE,
        help_text="Empresa para a qual se refere a apuração mensal"
    )
    
    competencia = models.CharField(
        max_length=7,
        help_text="Competência no formato MM/AAAA (ex: 01/2024)"
    )
    
    # Receitas do mês
    receita_consultas = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Receita bruta de consultas no mês"
    )
    
    receita_outros = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Receita bruta de outros serviços no mês"
    )
    
    receita_bruta = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Receita bruta total do mês"
    )
    
    # Base de cálculo estimada
    base_calculo = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Base de cálculo estimada sobre receita bruta"
    )
    
    rendimentos_aplicacoes = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Rendimentos de aplicações financeiras no mês"
    )
    
    base_calculo_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Base de cálculo total (receita + rendimentos)"
    )
    
    # Impostos calculados
    imposto_devido = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="IRPJ devido no mês (15% sobre base de cálculo)"
    )
    
    adicional = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Adicional de IRPJ (10% sobre excesso do limite mensal)"
    )
    
    # Retenções e créditos
    imposto_retido_nf = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="IRPJ retido nas notas fiscais recebidas"
    )
    
    retencao_aplicacao_financeira = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="IR retido em aplicações financeiras"
    )
    
    # Resultado final
    imposto_a_pagar = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="IRPJ a pagar no mês (devido + adicional - retenções)"
    )
    
    # Controle
    data_calculo = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora do último cálculo"
    )
    
    class Meta:
        db_table = 'apuracao_irpj_mensal'
        unique_together = ('empresa', 'competencia')
        ordering = ['empresa', 'competencia']
        verbose_name = 'Apuração IRPJ Mensal'
        verbose_name_plural = 'Apurações IRPJ Mensais'
    
    def __str__(self):
        return f"IRPJ Mensal {self.empresa.name} - {self.competencia}"
    
    def save(self, *args, **kwargs):
        """
        Validações antes de salvar.
        """
        # Garantir que valores não sejam negativos
        campos_decimais = [
            'receita_consultas', 'receita_outros', 'receita_bruta',
            'base_calculo', 'rendimentos_aplicacoes', 'base_calculo_total',
            'imposto_devido', 'adicional', 'imposto_retido_nf',
            'retencao_aplicacao_financeira'
        ]
        
        for campo in campos_decimais:
            valor = getattr(self, campo)
            if valor < 0:
                setattr(self, campo, Decimal('0.00'))
        
        super().save(*args, **kwargs)
