from django.db import models

class NotaFiscalRateioMedico(models.Model):
    """
    Stub para NotaFiscalRateioMedico.
    Implemente os campos e métodos conforme necessário.
    """
    # Exemplo de campo mínimo
    valor_bruto_medico = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Rateio Médico: R$ {self.valor_bruto_medico:.2f}"
