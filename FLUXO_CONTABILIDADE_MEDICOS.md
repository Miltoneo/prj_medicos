# SISTEMA DE CONTABILIDADE PARA ASSOCIAÇÕES MÉDICAS

## FLUXO COMPLETO IMPLEMENTADO

### 1. **EMISSÃO DE NOTAS FISCAIS**
- **Destinatário**: Sempre emitida para o **CNPJ da empresa/associação médica**
- **Modelo**: `NotaFiscal` 
- **Campos principais**:
  - `empresa_destinataria`: Empresa/associação que recebe a NF
  - `tomador`: Nome do tomador dos serviços
  - `val_bruto`, `val_liquido`: Valores da nota
  - `tipo_aliquota`: CONSULTAS, PLANTÃO, OUTROS
  - `status`: pendente → lancada → rateada → paga

### 2. **LANÇAMENTO FINANCEIRO COM RATEIO**
- **Modelo**: `Financeiro`
- **Processo**: Durante o lançamento no financeiro é que ocorre o rateio entre médicos
- **Funcionalidade**: `Financeiro.criar_rateio_nota_fiscal()`
- **Resultado**: Cada médico recebe sua parte proporcional da receita

### 3. **GRUPOS E ITENS DE DESPESAS**
- **Grupos**: FOLHA, GERAL, SOCIO
- **Itens**: Cada grupo tem vários itens específicos
- **Exemplos**:
  - FOLHA: Salários, Encargos, Benefícios
  - GERAL: Aluguel, Energia, Telefone, Material
  - SOCIO: Despesas individuais de cada médico

### 4. **PERCENTUAIS MENSAIS POR ITEM**
- **Modelo**: `PercentualRateioMensal`
- **Granularidade**: Cada item de despesa tem percentuais específicos por mês
- **Flexibilidade**: Percentuais podem variar mensalmente
- **Validação**: Soma deve ser 100% para cada item/mês

### 5. **CONFIGURAÇÃO MENSAL**
- **Modelo**: `ConfiguracaoRateioMensal`
- **Status**: rascunho → em_configuracao → finalizada → aplicada
- **Funcionalidade**: Copiar percentuais do mês anterior como base

### 6. **RATEIO DE DESPESAS**
- **Modelo**: `Despesa`
- **Processo**: `criar_rateio_automatico()` usa percentuais mensais
- **Resultado**: `Despesa_socio_rateio` para cada médico
- **Financeiro**: `criar_lancamentos_financeiros()` para débitos

## FLUXO OPERACIONAL

### **RECEITAS (Notas Fiscais)**
1. NF emitida para CNPJ da associação
2. Lançamento no financeiro
3. Rateio automático entre médicos ativos
4. Cada médico recebe sua parte (crédito)

### **DESPESAS**
1. Cadastro da despesa por item
2. Sistema identifica se é FOLHA/GERAL (com rateio) ou SOCIO (sem rateio)
3. Para FOLHA/GERAL: busca percentuais mensais cadastrados
4. Cria rateios automáticos baseados nos percentuais
5. Gera lançamentos financeiros (débitos) para cada médico

### **GESTÃO MENSAL**
1. Início do mês: criar configuração mensal
2. Copiar percentuais do mês anterior (se desejado)
3. Ajustar percentuais conforme necessário
4. Validar que soma = 100% para cada item
5. Finalizar configuração
6. Sistema aplica automaticamente nos rateios

## VANTAGENS DO SISTEMA

✅ **Flexibilidade Total**: Cada item pode ter percentuais diferentes
✅ **Variação Mensal**: Percentuais podem mudar mês a mês
✅ **Automação**: Rateios calculados automaticamente
✅ **Auditoria**: Rastreabilidade completa de todos os rateios
✅ **Validação**: Garantia de que percentuais somam 100%
✅ **Multi-tenant**: Isolamento total entre contas/clientes

## MODELOS PRINCIPAIS

- `NotaFiscal`: NFs emitidas para associações
- `Financeiro`: Lançamentos financeiros com rateios
- `Despesa`: Despesas categorizadas por grupos/itens
- `PercentualRateioMensal`: Percentuais específicos por item/mês
- `Despesa_socio_rateio`: Rateios de despesas entre médicos
- `ConfiguracaoRateioMensal`: Controle das configurações mensais

## PRÓXIMOS PASSOS

1. **Migrações**: Criar migrações para os novos modelos
2. **Admin**: Configurar Django Admin para gestão dos dados
3. **Views**: Criar interfaces para configuração mensal
4. **Reports**: Relatórios de rateios e extratos por médico
5. **Integração**: APIs para sistemas externos de contabilidade
