from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from django.conf import settings
from django.utils import timezone

@receiver(post_save, sender=NotaFiscal)
def criar_ou_atualizar_lancamentos_financeiros(sender, instance, created, **kwargs):
    """
    Cria ou atualiza lançamentos financeiros para cada sócio do rateio ao receber uma nota fiscal.
    Remove lançamentos se a nota for cancelada, excluída ou pendente.
    """
    # Só processa se a nota está recebida e tem rateio completo
    if instance.status_recebimento == 'RECEBIDA' and instance.rateio_completo:
        # Remove lançamentos antigos para evitar duplicidade
        Financeiro.objects.filter(nota_fiscal=instance).delete()
        # Busca ou cria a descrição padrão
        descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
            empresa=instance.empresa_destinataria,
            descricao='Credito de Nota Fiscal'
        )
        # Cria lançamentos para cada sócio do rateio
        for rateio in instance.rateios_medicos.all():
            Financeiro.objects.create(
                nota_fiscal=instance,
                socio=rateio.medico,
                descricao_movimentacao_financeira=descricao,
                data_movimentacao=instance.dtRecebimento or timezone.now().date(),
                valor=rateio.valor_bruto_medico,
                created_by=getattr(instance, 'updated_by', None)
            )
    else:
        # Se não recebida, remove lançamentos vinculados
        Financeiro.objects.filter(nota_fiscal=instance).delete()

@receiver(post_delete, sender=NotaFiscal)
def remover_lancamentos_financeiros(sender, instance, **kwargs):
    """
    Remove lançamentos financeiros ao excluir uma nota fiscal.
    """
    Financeiro.objects.filter(nota_fiscal=instance).delete()
