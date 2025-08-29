
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('medicos.signals_financeiro')


# @receiver(post_save, sender=NotaFiscal)
# def criar_ou_atualizar_lancamentos_financeiros(sender, instance, created, **kwargs):
#     """
#     SIGNAL DESABILITADO: Fluxo automático de inserção de nota fiscal na movimentação financeira foi desfeito.
#     Este signal criava automaticamente lançamentos financeiros quando uma nota fiscal era marcada como recebida
#     e tinha rateio completo. Para reativar, descomente este código.
#     """
#     logger.warning(f"Signal NotaFiscal disparado: id={instance.id}, status_recebimento={getattr(instance, 'status_recebimento', None)}, rateio_completo={getattr(instance, 'rateio_completo', None)}")
#     # Só processa se a nota está recebida e tem rateio completo
#     if getattr(instance, 'status_recebimento', None) == 'recebido' and getattr(instance, 'rateio_completo', False):
#         logger.warning(f"Criando lançamentos financeiros para NotaFiscal id={instance.id}")
#         Financeiro.objects.filter(nota_fiscal=instance).delete()
#         descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
#             empresa=instance.empresa_destinataria,
#             descricao='Credito de Nota Fiscal'
#         )
#         for rateio in instance.rateios_medicos.all():
#             logger.warning(f"Criando lançamento para sócio {rateio.medico_id} valor={rateio.valor_liquido_medico}")
#             Financeiro.objects.create(
#                 nota_fiscal=instance,
#                 socio=rateio.medico,
#                 descricao_movimentacao_financeira=descricao,
#                 data_movimentacao=instance.dtRecebimento or timezone.now().date(),
#                 valor=rateio.valor_liquido_medico,
#                 created_by=getattr(instance, 'updated_by', None)
#             )
#     else:
#         logger.warning(f"Removendo lançamentos financeiros para NotaFiscal id={instance.id}")
#         Financeiro.objects.filter(nota_fiscal=instance).delete()

@receiver(pre_delete, sender=NotaFiscal)
def remover_lancamentos_financeiros(sender, instance, **kwargs):
    """
    Signal disparado ANTES de uma NotaFiscal ser excluída.
    Remove automaticamente todas as movimentações financeiras associadas.
    
    Usamos pre_delete para garantir que a referência nota_fiscal ainda existe
    quando buscarmos as movimentações para removê-las.
    """
    logger.info(f"=== SIGNAL PRE_DELETE DISPARADO ===")
    logger.info(f"Preparando exclusão da Nota Fiscal: {instance.numero} (ID: {instance.id})")
    
    # Buscar movimentações ANTES da exclusão (referência ainda existe)
    movimentacoes = Financeiro.objects.filter(nota_fiscal=instance)
    count_movimentacoes = movimentacoes.count()
    
    if count_movimentacoes > 0:
        logger.info(f"Removendo {count_movimentacoes} movimentação(ões) financeira(s)")
        
        # Listar as movimentações que serão removidas para auditoria
        for mov in movimentacoes:
            logger.info(f"  - Movimentação ID: {mov.id}, Sócio: {mov.socio.pessoa.name}, Valor: R$ {mov.valor}")
        
        # Remover as movimentações COMPLETAMENTE da tabela
        movimentacoes.delete()
        logger.info(f"✅ {count_movimentacoes} movimentação(ões) removida(s) COMPLETAMENTE da tabela")
    else:
        logger.info("ℹ️  Nenhuma movimentação financeira associada para remover")
    
    logger.info(f"=== PROPAGAÇÃO DE EXCLUSÃO CONCLUÍDA ===")


def limpar_movimentacoes_orfas():
    """
    Função utilitária para limpar movimentações financeiras órfãs 
    (que perderam a referência da nota fiscal após exclusões anteriores).
    
    Esta função deve ser executada manualmente para corrigir dados históricos.
    """
    logger.info("=== INICIANDO LIMPEZA DE MOVIMENTAÇÕES ÓRFÃS ===")
    
    # Buscar movimentações que eram de notas fiscais mas perderam a referência
    movimentacoes_orfas = Financeiro.objects.filter(
        nota_fiscal__isnull=True,
        descricao_movimentacao_financeira__descricao='Credito de Nota Fiscal'
    )
    
    count_orfas = movimentacoes_orfas.count()
    
    if count_orfas > 0:
        logger.info(f"Encontradas {count_orfas} movimentação(ões) órfã(s) para limpeza")
        
        # Listar as movimentações órfãs que serão removidas
        for mov in movimentacoes_orfas:
            logger.info(f"  - Movimentação órfã ID: {mov.id}, Sócio: {mov.socio.pessoa.name}, Valor: R$ {mov.valor}, Data: {mov.data_movimentacao}")
        
        # Remover as movimentações órfãs
        movimentacoes_orfas.delete()
        logger.info(f"✅ {count_orfas} movimentação(ões) órfã(s) removida(s) com sucesso")
    else:
        logger.info("ℹ️  Nenhuma movimentação órfã encontrada")
    
    logger.info("=== LIMPEZA DE MOVIMENTAÇÕES ÓRFÃS CONCLUÍDA ===")
    return count_orfas
