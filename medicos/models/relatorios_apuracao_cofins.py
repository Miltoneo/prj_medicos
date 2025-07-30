from django.db import models
from medicos.models.base import Empresa

class ApuracaoCOFINS(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    competencia = models.CharField(max_length=7)  # formato MM/YYYY
    base_calculo = models.DecimalField(max_digits=18, decimal_places=2)
    aliquota = models.DecimalField(max_digits=5, decimal_places=2)
    imposto_devido = models.DecimalField(max_digits=18, decimal_places=2)
    imposto_retido_nf = models.DecimalField(max_digits=18, decimal_places=2)
    imposto_a_pagar = models.DecimalField(max_digits=18, decimal_places=2)
    credito_mes_anterior = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credito_mes_seguinte = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('empresa', 'competencia')
        verbose_name = "Apuração COFINS"
        verbose_name_plural = "Apurações COFINS"
        indexes = [
            models.Index(fields=['empresa', 'competencia']),
        ]
