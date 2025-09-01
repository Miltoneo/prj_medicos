"""
Serviço para lançamento automático de impostos na conta corrente
Com suporte a atualização de lançamentos quando houver recálculo
"""
from django.db import transaction
from django.utils import timezone
from datetime import date
from decimal import Decimal
import logging

from medicos.models.base import Empresa, Socio
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento

logger = logging.getLogger(__name__)


class LancamentoImpostosService:
    """
    Serviço para automatizar lançamentos de impostos na conta corrente
    com capacidade de atualização em caso de recálculo
    """
    
    def __init__(self):
        self.impostos_config = [
            ('PIS', 'Pagamento PIS', 'DARF'),
            ('COFINS', 'Pagamento COFINS', 'DARF'),
            ('IRPJ', 'Pagamento IRPJ', 'DARF'),
            ('CSLL', 'Pagamento CSLL', 'DARF'),
            ('ISSQN', 'Pagamento ISSQN', 'Guia Municipal')
        ]
    
    def processar_impostos_automaticamente(self, empresa, socio, mes, ano, valores_impostos, 
                                         atualizar_existentes=True):
        """
        Processa lançamentos de impostos com opção de atualizar existentes
        
        Args:
            empresa: Instância da empresa
            socio: Instância do sócio
            mes: Mês de competência (int)
            ano: Ano de competência (int)
            valores_impostos: Dict com valores dos impostos {'PIS': valor, 'COFINS': valor, ...}
            atualizar_existentes: Se True, atualiza lançamentos existentes
        
        Returns:
            Dict com resultado da operação
        """
        try:
            with transaction.atomic():
                # Calcular data de lançamento (dia 15 do mês seguinte)
                data_lancamento = self._calcular_data_lancamento(mes, ano)
                competencia_str = f"{mes:02d}/{ano}"
                
                logger.info(f"Processando impostos para {socio.pessoa.name} - Competência {competencia_str}")
                
                # Preparar recursos necessários
                instrumentos = self._obter_instrumentos_bancarios(empresa)
                descricoes = self._obter_descricoes_movimentacao(empresa)
                
                # Processar cada imposto
                lancamentos_resultado = self._processar_impostos_individualmente(
                    socio=socio,
                    valores_impostos=valores_impostos,
                    data_lancamento=data_lancamento,
                    competencia_str=competencia_str,
                    descricoes=descricoes,
                    instrumentos=instrumentos,
                    atualizar_existentes=atualizar_existentes
                )
                
                # Compilar resultado
                total_lancado = sum(
                    abs(r['valor']) for r in lancamentos_resultado 
                    if r['acao'] in ['criado', 'atualizado']
                )
                
                resultado = {
                    'success': True,
                    'lancamentos_criados': len([r for r in lancamentos_resultado if r['acao'] == 'criado']),
                    'lancamentos_atualizados': len([r for r in lancamentos_resultado if r['acao'] == 'atualizado']),
                    'lancamentos_removidos': len([r for r in lancamentos_resultado if r['acao'] == 'removido']),
                    'total_lancado': total_lancado,
                    'data_lancamento': data_lancamento,
                    'competencia': competencia_str,
                    'detalhes': lancamentos_resultado
                }
                
                logger.info(f"Impostos processados com sucesso: {resultado}")
                return resultado
        
        except Exception as e:
            logger.error(f"Erro ao processar impostos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _processar_impostos_individualmente(self, socio, valores_impostos, data_lancamento,
                                          competencia_str, descricoes, instrumentos,
                                          atualizar_existentes):
        """
        Processa cada imposto individualmente
        """
        resultado = []
        
        for imposto_nome in ['PIS', 'COFINS', 'IRPJ', 'CSLL', 'ISSQN']:
            valor = valores_impostos.get(imposto_nome, Decimal('0'))
            
            # Buscar lançamento existente
            lancamento_existente = self._buscar_lancamento_existente(
                socio, imposto_nome, data_lancamento, competencia_str, descricoes
            )
            
            if valor and valor > 0:
                # Há valor a ser lançado
                if lancamento_existente:
                    if atualizar_existentes:
                        # Atualizar lançamento existente
                        valor_anterior = abs(lancamento_existente.valor)
                        lancamento_existente.valor = -valor  # Negativo = saída
                        lancamento_existente.save()
                        
                        resultado.append({
                            'imposto': imposto_nome,
                            'acao': 'atualizado',
                            'valor': valor,
                            'valor_anterior': valor_anterior,
                            'lancamento_id': lancamento_existente.id
                        })
                    else:
                        # Manter existente
                        resultado.append({
                            'imposto': imposto_nome,
                            'acao': 'mantido',
                            'valor': abs(lancamento_existente.valor),
                            'lancamento_id': lancamento_existente.id
                        })
                else:
                    # Criar novo lançamento
                    novo_lancamento = self._criar_lancamento_imposto(
                        socio=socio,
                        imposto_nome=imposto_nome,
                        valor=valor,
                        data_lancamento=data_lancamento,
                        competencia_str=competencia_str,
                        descricoes=descricoes,
                        instrumentos=instrumentos
                    )
                    
                    resultado.append({
                        'imposto': imposto_nome,
                        'acao': 'criado',
                        'valor': valor,
                        'lancamento_id': novo_lancamento.id
                    })
            else:
                # Não há valor, remover se existir
                if lancamento_existente and atualizar_existentes:
                    valor_removido = abs(lancamento_existente.valor)
                    lancamento_existente.delete()
                    
                    resultado.append({
                        'imposto': imposto_nome,
                        'acao': 'removido',
                        'valor': valor_removido,
                        'motivo': 'valor_zero_ou_negativo'
                    })
        
        return resultado
    
    def _calcular_data_lancamento(self, mes, ano):
        """Calcula data de lançamento (dia 15 do mês seguinte)"""
        try:
            if mes == 12:
                return date(ano + 1, 1, 15)
            else:
                return date(ano, mes + 1, 15)
        except ValueError as e:
            # Fallback para último dia do mês seguinte se dia 15 não existir
            if mes == 12:
                return date(ano + 1, 1, 28)
            else:
                return date(ano, mes + 1, 28)
    
    def _obter_instrumentos_bancarios(self, empresa):
        """Obtém ou cria instrumentos bancários necessários"""
        darf, _ = MeioPagamento.objects.get_or_create(
            empresa=empresa,
            codigo="DARF",
            defaults={
                'nome': 'Documento de Arrecadação de Receitas Federais',
                'ativo': True
            }
        )
        
        guia_municipal, _ = MeioPagamento.objects.get_or_create(
            empresa=empresa,
            codigo="GUIA_MUNICIPAL",
            defaults={
                'nome': 'Guia de pagamento municipal (ISSQN)',
                'ativo': True
            }
        )
        
        return {'DARF': darf, 'Guia Municipal': guia_municipal}
    
    def _obter_descricoes_movimentacao(self, empresa):
        """Obtém ou cria descrições de movimentação para cada imposto"""
        descricoes = {}
        
        for codigo, descricao, _ in self.impostos_config:
            desc_obj, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
                empresa=empresa,
                codigo_contabil=f"IMPOSTO_{codigo}",
                defaults={
                    'descricao': descricao,
                    'observacoes': f'Lançamento automático de {descricao.lower()}'
                }
            )
            descricoes[codigo] = desc_obj
            
            if created:
                logger.info(f"Criada descrição de movimentação: {desc_obj.descricao}")
        
        return descricoes
    
    def _buscar_lancamento_existente(self, socio, imposto_nome, data_lancamento, 
                                    competencia_str, descricoes):
        """Busca lançamento existente para este imposto no período"""
        try:
            return MovimentacaoContaCorrente.objects.get(
                descricao_movimentacao=descricoes[imposto_nome],
                socio=socio,
                data_movimentacao__year=data_lancamento.year,
                data_movimentacao__month=data_lancamento.month,
                historico_complementar__icontains=competencia_str
            )
        except MovimentacaoContaCorrente.DoesNotExist:
            return None
        except MovimentacaoContaCorrente.MultipleObjectsReturned:
            # Se houver múltiplos, pegar o mais recente
            logger.warning(f"Múltiplos lançamentos encontrados para {imposto_nome} - {competencia_str}")
            return MovimentacaoContaCorrente.objects.filter(
                descricao_movimentacao=descricoes[imposto_nome],
                socio=socio,
                data_movimentacao__year=data_lancamento.year,
                data_movimentacao__month=data_lancamento.month,
                historico_complementar__icontains=competencia_str
            ).order_by('-id').first()
    
    def _criar_lancamento_imposto(self, socio, imposto_nome, valor, data_lancamento, 
                                  competencia_str, descricoes, instrumentos):
        """Cria um lançamento individual de imposto"""
        # Determinar instrumento baseado no tipo de imposto
        instrumento_nome = 'Guia Municipal' if imposto_nome == 'ISSQN' else 'DARF'
        
        # Criar histórico detalhado
        historico = f"Pagamento {imposto_nome} - Competência {competencia_str} - Lançamento automático"
        
        lancamento = MovimentacaoContaCorrente.objects.create(
            data_movimentacao=data_lancamento,
            descricao_movimentacao=descricoes[imposto_nome],
            socio=socio,
            valor=-valor,  # Valor negativo = saída de dinheiro
            historico_complementar=historico,
            instrumento_bancario=instrumentos[instrumento_nome],
            conciliado=False
        )
        
        logger.info(f"Criado lançamento {imposto_nome}: R$ {valor} para {socio.pessoa.name}")
        return lancamento
    
    def listar_lancamentos_impostos(self, socio, mes, ano):
        """
        Lista lançamentos de impostos existentes para um período
        """
        data_lancamento = self._calcular_data_lancamento(mes, ano)
        competencia_str = f"{mes:02d}/{ano}"
        
        # Buscar descrições de impostos
        descricoes_impostos = DescricaoMovimentacaoFinanceira.objects.filter(
            empresa=socio.empresa,
            codigo_contabil__startswith='IMPOSTO_'
        )
        
        lancamentos = MovimentacaoContaCorrente.objects.filter(
            socio=socio,
            descricao_movimentacao__in=descricoes_impostos,
            data_movimentacao__year=data_lancamento.year,
            data_movimentacao__month=data_lancamento.month,
            historico_complementar__icontains=competencia_str
        ).select_related('descricao_movimentacao', 'instrumento_bancario')
        
        return lancamentos
    
    def remover_lancamentos_impostos(self, socio, mes, ano):
        """
        Remove todos os lançamentos de impostos para um período
        """
        lancamentos = self.listar_lancamentos_impostos(socio, mes, ano)
        
        with transaction.atomic():
            count = lancamentos.count()
            total_removido = sum(abs(l.valor) for l in lancamentos)
            lancamentos.delete()
            
            logger.info(f"Removidos {count} lançamentos de impostos, total: R$ {total_removido}")
            
            return {
                'success': True,
                'lancamentos_removidos': count,
                'total_removido': total_removido
            }
