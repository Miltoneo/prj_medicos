
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('medicos.signals_financeiro')


@receiver(post_save, sender=NotaFiscal)
def criar_ou_atualizar_lancamentos_financeiros(sender, instance, created, **kwargs):
    logger.warning(f"Signal NotaFiscal disparado: id={instance.id}, status_recebimento={getattr(instance, 'status_recebimento', None)}, rateio_completo={getattr(instance, 'rateio_completo', None)}")
    # Só processa se a nota está recebida e tem rateio completo
    if getattr(instance, 'status_recebimento', None) == 'recebido' and getattr(instance, 'rateio_completo', False):
        logger.warning(f"Criando lançamentos financeiros para NotaFiscal id={instance.id}")
        Financeiro.objects.filter(nota_fiscal=instance).delete()
        descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
            empresa=instance.empresa_destinataria,
            descricao='Credito de Nota Fiscal'
        )
        for rateio in instance.rateios_medicos.all():
            logger.warning(f"Criando lançamento para sócio {rateio.medico_id} valor={rateio.valor_liquido_medico}")
            Financeiro.objects.create(
                nota_fiscal=instance,
                socio=rateio.medico,
                descricao_movimentacao_financeira=descricao,
                data_movimentacao=instance.dtRecebimento or timezone.now().date(),
                valor=rateio.valor_liquido_medico,
                created_by=getattr(instance, 'updated_by', None)
            )
    else:
        logger.warning(f"Removendo lançamentos financeiros para NotaFiscal id={instance.id}")
        Financeiro.objects.filter(nota_fiscal=instance).delete()

@receiver(post_delete, sender=NotaFiscal)
def remover_lancamentos_financeiros(sender, instance, **kwargs):
    logger.warning(f"Removendo lançamentos financeiros (delete) para NotaFiscal id={instance.id}")
    Financeiro.objects.filter(nota_fiscal=instance).delete()
