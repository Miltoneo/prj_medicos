from django.db import models
from medicos.models.base import Empresa

class ApuracaoCSLL(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    competencia = models.CharField(max_length=7)  # formato MM/YYYY ou trimestre
    receita_consultas = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    receita_outros = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    receita_bruta = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    base_calculo = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    rendimentos_aplicacoes = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    base_calculo_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    imposto_devido = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    imposto_retido_nf = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    retencao_aplicacao_financeira = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    imposto_a_pagar = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('empresa', 'competencia')
        verbose_name = 'Apuração CSLL'
        verbose_name_plural = 'Apurações CSLL'
        indexes = [
            models.Index(fields=['empresa', 'competencia'], name='medicos_apuracaocsll_empresa_competencia_idx'),
        ]
