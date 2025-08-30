
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.despesas import DespesaSocio
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

@receiver(post_save, sender=NotaFiscal)
def criar_ou_atualizar_lancamento_conta_corrente(sender, instance, created, **kwargs):
    """
    Signal disparado quando uma NotaFiscal é salva.
    Cria, atualiza ou remove lançamento na conta corrente baseado no status de recebimento.
    
    Regra: Toda nota fiscal recebida gera um lançamento de entrada na conta corrente.
    Mudanças na data, status ou meio de pagamento são refletidas automaticamente.
    """
    print(f"=== SIGNAL CONTA CORRENTE DISPARADO ===")
    print(f"Nota Fiscal: {instance.numero} (ID: {instance.id})")
    print(f"Status: {instance.status_recebimento}, Data Recebimento: {instance.dtRecebimento}")
    print(f"Rateio completo: {instance.rateio_completo if instance.tem_rateio else 'N/A (sem rateio)'}")
    
    logger.info(f"=== SIGNAL CONTA CORRENTE DISPARADO ===")
    logger.info(f"Nota Fiscal: {instance.numero} (ID: {instance.id})")
    logger.info(f"Status: {instance.status_recebimento}, Data Recebimento: {instance.dtRecebimento}")
    logger.info(f"Rateio completo: {instance.rateio_completo if instance.tem_rateio else 'N/A (sem rateio)'}")
    
    # Buscar lançamento existente na conta corrente
    lancamento_existente = MovimentacaoContaCorrente.objects.filter(nota_fiscal=instance).first()
    
    # VALIDAÇÃO: Nota deve estar recebida, ter data, meio de pagamento
    # E se tem rateio, o rateio deve estar completo (100%)
    condicoes_atendidas = (
        instance.status_recebimento == 'recebido' and 
        instance.dtRecebimento and 
        instance.meio_pagamento and
        (not instance.tem_rateio or instance.rateio_completo)  # Se tem rateio, deve estar completo
    )
    
    print(f"Condições para lançamento: recebido={instance.status_recebimento == 'recebido'}, "
          f"data={bool(instance.dtRecebimento)}, meio_pagamento={bool(instance.meio_pagamento)}, "
          f"rateio_ok={not instance.tem_rateio or instance.rateio_completo}")
    
    if condicoes_atendidas:
        # Criar ou atualizar lançamento na conta corrente
        
        # Garantir que existe uma descrição específica para crédito de nota fiscal
        descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
            empresa=instance.empresa_destinataria,
            descricao='Credito de Nota Fiscal',
            defaults={
                'created_by': getattr(instance, 'updated_by', None)
            }
        )
        
        # Determinar o sócio (se houver rateio, usar o primeiro sócio)
        socio = None
        if hasattr(instance, 'rateios_medicos') and instance.rateios_medicos.exists():
            socio = instance.rateios_medicos.first().medico
        
        # Dados do lançamento
        dados_lancamento = {
            'descricao_movimentacao': descricao,
            'socio': socio,
            'data_movimentacao': instance.dtRecebimento,
            'valor': instance.val_liquido,  # Valor positivo = entrada na conta
            'instrumento_bancario': instance.meio_pagamento,
            'numero_documento_bancario': instance.numero,
            'historico_complementar': f'Recebimento da Nota Fiscal nº {instance.numero}',
            'created_by': getattr(instance, 'updated_by', None)
        }
        
        if lancamento_existente:
            # Atualizar lançamento existente
            for campo, valor in dados_lancamento.items():
                setattr(lancamento_existente, campo, valor)
            lancamento_existente.save()
            print(f"✅ Lançamento conta corrente ATUALIZADO (ID: {lancamento_existente.id})")
            logger.info(f"✅ Lançamento conta corrente ATUALIZADO (ID: {lancamento_existente.id})")
        else:
            # Criar novo lançamento
            dados_lancamento['nota_fiscal'] = instance
            novo_lancamento = MovimentacaoContaCorrente.objects.create(**dados_lancamento)
            print(f"✅ Lançamento conta corrente CRIADO (ID: {novo_lancamento.id})")
            logger.info(f"✅ Lançamento conta corrente CRIADO (ID: {novo_lancamento.id})")
            
    else:
        # Remover lançamento se nota não está recebida ou não tem dados completos
        if lancamento_existente:
            lancamento_existente.delete()
            print(f"🗑️ Lançamento conta corrente REMOVIDO")
            logger.info(f"🗑️ Lançamento conta corrente REMOVIDO")
        else:
            print(f"ℹ️ Nenhum lançamento para remover")
            logger.info(f"ℹ️ Nenhum lançamento para remover")
    
    print(f"=== SIGNAL CONTA CORRENTE CONCLUÍDO ===")
    logger.info(f"=== SIGNAL CONTA CORRENTE CONCLUÍDO ===")


@receiver(pre_delete, sender=NotaFiscal)
def remover_lancamento_conta_corrente(sender, instance, **kwargs):
    """
    Signal disparado ANTES de uma NotaFiscal ser excluída.
    Remove automaticamente o lançamento na conta corrente associado.
    """
    logger.info(f"=== REMOVENDO LANÇAMENTO CONTA CORRENTE ===")
    logger.info(f"Nota Fiscal: {instance.numero} (ID: {instance.id})")
    
    # Buscar e remover lançamento na conta corrente
    lancamentos_cc = MovimentacaoContaCorrente.objects.filter(nota_fiscal=instance)
    count_lancamentos = lancamentos_cc.count()
    
    if count_lancamentos > 0:
        logger.info(f"Removendo {count_lancamentos} lançamento(s) na conta corrente")
        for lancamento in lancamentos_cc:
            logger.info(f"  - Lançamento ID: {lancamento.id}, Valor: R$ {lancamento.valor}, Data: {lancamento.data_movimentacao}")
        
        lancamentos_cc.delete()
        logger.info(f"✅ {count_lancamentos} lançamento(s) conta corrente removido(s)")
    else:
        logger.info("ℹ️ Nenhum lançamento na conta corrente para remover")
    
    logger.info(f"=== REMOÇÃO CONTA CORRENTE CONCLUÍDA ===")


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


# ===============================
# SIGNALS PARA DESPESAS DE SÓCIO
# ===============================

@receiver(post_save, sender=DespesaSocio)
def criar_ou_atualizar_debito_despesa_socio(sender, instance, created, **kwargs):
    """
    Signal disparado quando uma DespesaSocio é salva.
    Cria ou atualiza um lançamento de débito na conta corrente para a despesa do sócio.
    
    Regra: Toda despesa de sócio gera um lançamento de saída na conta corrente.
    Mudanças na data, valor ou item de despesa são refletidas automaticamente.
    """
    print(f"=== SIGNAL DESPESA SÓCIO DISPARADO ===")
    print(f"Despesa Sócio: ID {instance.id}, Sócio: {instance.socio}")
    print(f"Data: {instance.data}, Valor: R$ {instance.valor}")
    print(f"Item: {instance.item_despesa}")
    
    logger.info(f"=== SIGNAL DESPESA SÓCIO DISPARADO ===")
    logger.info(f"Despesa Sócio: ID {instance.id}, Sócio: {instance.socio}")
    logger.info(f"Data: {instance.data}, Valor: R$ {instance.valor}")
    logger.info(f"Item: {instance.item_despesa}")
    
    # Buscar lançamento existente na conta corrente
    from django.contrib.contenttypes.models import ContentType
    despesa_content_type = ContentType.objects.get_for_model(DespesaSocio)
    
    # Como MovimentacaoContaCorrente não tem um campo genérico para despesas,
    # vamos usar o histórico_complementar para identificar
    lancamento_existente = MovimentacaoContaCorrente.objects.filter(
        socio=instance.socio,
        historico_complementar__contains=f'Despesa Sócio ID: {instance.id}'
    ).first()
    
    # VALIDAÇÃO: Despesa deve ter todos os dados necessários
    condicoes_atendidas = (
        instance.data and 
        instance.valor and
        instance.valor > 0 and
        instance.socio and
        instance.item_despesa
    )
    
    print(f"Condições para lançamento: data={bool(instance.data)}, "
          f"valor={bool(instance.valor and instance.valor > 0)}, "
          f"socio={bool(instance.socio)}, item={bool(instance.item_despesa)}")
    
    if condicoes_atendidas:
        # Garantir que existe uma descrição específica para débito de despesa
        descricao, _ = DescricaoMovimentacaoFinanceira.objects.get_or_create(
            empresa=instance.socio.empresa,
            descricao='Débito - Despesa de Sócio',
            defaults={
                'created_by': getattr(instance, 'created_by', None)
            }
        )
        
        # Montar descrição detalhada conforme solicitado
        descricao_despesa = instance.item_despesa.descricao if instance.item_despesa else "Despesa"
        historico_detalhado = f"Débito - Despesa: {descricao_despesa} (Despesa Sócio ID: {instance.id})"
        
        # Dados do lançamento
        dados_lancamento = {
            'descricao_movimentacao': descricao,
            'socio': instance.socio,
            'data_movimentacao': instance.data,
            'valor': -abs(instance.valor),  # Valor negativo = saída da conta (débito para o sócio)
            'instrumento_bancario': None,  # Despesas não têm instrumento bancário específico
            'numero_documento_bancario': '',
            'historico_complementar': historico_detalhado,
            'created_by': getattr(instance, 'created_by', None)
        }
        
        if lancamento_existente:
            # Atualizar lançamento existente
            for campo, valor in dados_lancamento.items():
                setattr(lancamento_existente, campo, valor)
            lancamento_existente.save()
            print(f"✅ Lançamento conta corrente ATUALIZADO (ID: {lancamento_existente.id})")
            logger.info(f"✅ Lançamento conta corrente ATUALIZADO (ID: {lancamento_existente.id})")
        else:
            # Criar novo lançamento
            novo_lancamento = MovimentacaoContaCorrente.objects.create(**dados_lancamento)
            print(f"✅ Lançamento conta corrente CRIADO (ID: {novo_lancamento.id})")
            logger.info(f"✅ Lançamento conta corrente CRIADO (ID: {novo_lancamento.id})")
            
    else:
        # Remover lançamento se despesa não tem dados completos
        if lancamento_existente:
            lancamento_existente.delete()
            print(f"🗑️ Lançamento conta corrente REMOVIDO")
            logger.info(f"🗑️ Lançamento conta corrente REMOVIDO")
        else:
            print(f"ℹ️ Nenhum lançamento para remover")
            logger.info(f"ℹ️ Nenhum lançamento para remover")
    
    print(f"=== SIGNAL DESPESA SÓCIO CONCLUÍDO ===")
    logger.info(f"=== SIGNAL DESPESA SÓCIO CONCLUÍDO ===")


@receiver(pre_delete, sender=DespesaSocio)
def remover_debito_despesa_socio(sender, instance, **kwargs):
    """
    Signal disparado ANTES de uma DespesaSocio ser excluída.
    Remove automaticamente o lançamento na conta corrente associado.
    """
    logger.info(f"=== REMOVENDO LANÇAMENTO DESPESA SÓCIO ===")
    logger.info(f"Despesa Sócio: ID {instance.id}, Sócio: {instance.socio}")
    
    # Buscar e remover lançamento na conta corrente
    lancamentos_cc = MovimentacaoContaCorrente.objects.filter(
        socio=instance.socio,
        historico_complementar__contains=f'Despesa Sócio ID: {instance.id}'
    )
    count_lancamentos = lancamentos_cc.count()
    
    if count_lancamentos > 0:
        logger.info(f"Removendo {count_lancamentos} lançamento(s) na conta corrente")
        for lancamento in lancamentos_cc:
            logger.info(f"  - Lançamento ID: {lancamento.id}, Valor: R$ {lancamento.valor}, Data: {lancamento.data_movimentacao}")
        
        lancamentos_cc.delete()
        logger.info(f"✅ {count_lancamentos} lançamento(s) conta corrente removido(s)")
    else:
        logger.info("ℹ️ Nenhum lançamento na conta corrente para remover")
    
    logger.info(f"=== REMOÇÃO DESPESA SÓCIO CONCLUÍDA ===")
