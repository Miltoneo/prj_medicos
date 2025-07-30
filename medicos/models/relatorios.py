"""
Modelos relacionados a relatórios consolidados

"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Conta
from medicos.models.base import Empresa, Socio

# Este módulo agora serve apenas como placeholder para futuros modelos de relatórios
# que sejam realmente necessários e não redundantes com o sistema principal.

class RelatorioMensalSocio(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    competencia = models.DateField()  # Ex: 2025-07-01
    data_geracao = models.DateTimeField(auto_now_add=True)

    # Totais e agregados
    total_despesas_sem_rateio = models.DecimalField(max_digits=15, decimal_places=2)
    total_despesas_com_rateio = models.DecimalField(max_digits=15, decimal_places=2)
    despesas_total = models.DecimalField(max_digits=15, decimal_places=2)
    despesa_sem_rateio = models.DecimalField(max_digits=15, decimal_places=2)
    despesa_com_rateio = models.DecimalField(max_digits=15, decimal_places=2)
    despesa_geral = models.DecimalField(max_digits=15, decimal_places=2)

    receita_bruta_recebida = models.DecimalField(max_digits=15, decimal_places=2)
    receita_liquida = models.DecimalField(max_digits=15, decimal_places=2)
    impostos_total = models.DecimalField(max_digits=15, decimal_places=2)
    total_iss = models.DecimalField(max_digits=15, decimal_places=2)
    total_pis = models.DecimalField(max_digits=15, decimal_places=2)
    total_cofins = models.DecimalField(max_digits=15, decimal_places=2)
    total_irpj = models.DecimalField(max_digits=15, decimal_places=2)
    total_irpj_adicional = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="IRPJ - Adicional", help_text="Valor total do adicional de IRPJ apurado no mês.")
    total_csll = models.DecimalField(max_digits=15, decimal_places=2)
    total_notas_bruto = models.DecimalField(max_digits=15, decimal_places=2)
    total_notas_liquido = models.DecimalField(max_digits=15, decimal_places=2)
    total_notas_emitidas_mes = models.PositiveIntegerField()

    saldo_apurado = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_movimentacao_financeira = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_a_transferir = models.DecimalField(max_digits=15, decimal_places=2)

    # Listas detalhadas (JSON)
    lista_despesas_sem_rateio = models.JSONField(default=list)
    lista_despesas_com_rateio = models.JSONField(default=list)
    lista_notas_fiscais = models.JSONField(default=list)
    lista_movimentacoes_financeiras = models.JSONField(default=list)
    debug_ir_adicional = models.JSONField(default=list, blank=True, null=True, help_text="Espelho detalhado do cálculo do IR adicional por nota fiscal.")

    class Meta:
        unique_together = ('empresa', 'socio', 'competencia')
        verbose_name = "Relatório Mensal de Sócio"
        verbose_name_plural = "Relatórios Mensais de Sócio"
