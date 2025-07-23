from django.db import models
from medicos.models.base import Empresa

class ApuracaoISSQN(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    competencia = models.CharField(max_length=7)  # formato MM/YYYY
    base_calculo = models.DecimalField(max_digits=12, decimal_places=2)
    imposto_devido = models.DecimalField(max_digits=12, decimal_places=2)
    imposto_retido_nf = models.DecimalField(max_digits=12, decimal_places=2)
    imposto_a_pagar = models.DecimalField(max_digits=12, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Apuração ISSQN"
        verbose_name_plural = "Apurações ISSQN"
        indexes = [
            models.Index(fields=['empresa', 'competencia']),
        ]
