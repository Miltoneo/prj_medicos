# Importações de todos os modelos para manter compatibilidade
from .base import *
from .fiscal import *
from .despesas import *
from .financeiro import *
from .auditoria import *

from .relatorios import *
from .relatorios_apuracao_csll import *
from .relatorios_apuracao_irpj_mensal import *

# Definir __all__ para controlar as importações
__all__ = [
    # Modelos Base
    'CustomUser', 'Conta', 'Licenca', 'ContaMembership', 'SaaSBaseModel', 
    'Pessoa', 'Empresa', 'Socio', 'ContaScopedManager',
    
    # Modelos Fiscais
    'Aliquotas', 'NotaFiscal',
    # Modelos de Despesas
    
    # Modelos Financeiros
    'MeioPagamento', 'DescricaoMovimentacaoFinanceira', 'Financeiro',

    # Modelos de Apuração
    'ApuracaoCSLL', 'ApuracaoIRPJMensal',
    
    # Modelos de Auditoria
    'LogAuditoriaFinanceiro', 'ConfiguracaoSistemaManual', 'registrar_auditoria',
    
    # Constantes importantes
    'app_name', 'REGIME_TRIBUTACAO_COMPETENCIA', 'REGIME_TRIBUTACAO_CAIXA',
    'NFISCAL_ALIQUOTA_CONSULTAS', 'NFISCAL_ALIQUOTA_PLANTAO', 'NFISCAL_ALIQUOTA_OUTROS',
    'TIPO_MOVIMENTACAO_CONTA_CREDITO', 'TIPO_MOVIMENTACAO_CONTA_DEBITO',
    'DESC_MOVIMENTACAO_CREDITO_SALDO_MES_SEGUINTE', 'DESC_MOVIMENTACAO_DEBITO_IMPOSTO_PROVISIONADOS',
    'CODIGO_GRUPO_DESPESA_GERAL', 'CODIGO_GRUPO_DESPESA_FOLHA', 'CODIGO_GRUPO_DESPESA_SOCIO',
    'TIPO_DESPESA_COM_RATEIO', 'TIPO_DESPESA_SEM_RATEIO',
    'GRUPO_ITEM_COM_RATEIO', 'GRUPO_ITEM_SEM_RATEIO',
]
