# Sistema de Fluxo de Caixa Manual Individual dos Médicos

## Visão Geral

O sistema Django para associações médicas foi completamente adaptado para um controle de fluxo de caixa **100% MANUAL** e **AUDITÁVEL** por médico/sócio. Cada médico possui uma conta corrente onde são registradas EXCLUSIVAMENTE movimentações manuais controladas pela contabilidade, proporcionando total transparência e auditabilidade.

**IMPORTANTE**: As receitas de notas fiscais são tratadas separadamente no sistema contábil e NÃO fazem parte deste fluxo de caixa individual.

## Princípios do Sistema Manual

### ✅ Incluído no Fluxo Individual
- Adiantamentos de lucro (manuais)
- Pagamentos recebidos diretamente
- Despesas individuais autorizadas  
- Ajustes e estornos
- Transferências bancárias
- Outras movimentações manuais

### ❌ Excluído do Fluxo Individual
- Receitas de notas fiscais (sistema contábil separado)
- Rateio automático de NF (desabilitado)
- Qualquer lançamento automático

## Arquitetura do Sistema Manual

### 1. Modelo `Desc_movimentacao_financeiro`

**Objetivo**: Centralizar descrições padronizadas para movimentações MANUAIS APENAS.

**Principais recursos**:
- Categorização por tipo de movimentação manual
- Descrições criadas/aprovadas pela contabilidade
- Contador de frequência de uso
- Controle de auditoria (created_by, created_at)

**Categorias de movimentação manual**:
- `adiantamento`: Adiantamentos de Lucro
- `pagamento`: Pagamentos Recebidos
- `ajuste`: Ajustes e Estornos
- `transferencia`: Transferências Bancárias
- `despesa`: Despesas Individuais
- `taxa`: Taxas e Encargos
- `financeiro`: Operações Financeiras
- `saldo`: Saldos e Transportes
- `outros`: Outras Movimentações

**Exemplos de descrições manuais**:
```
ADIANTAMENTO DE LUCRO MENSAL
PAGAMENTO CARTÃO CRÉDITO
DESPESA MATERIAL MÉDICO INDIVIDUAL
ESTORNO PAGAMENTO A MAIOR
TRANSFERÊNCIA BANCÁRIA ENVIADA
TAXA ADMINISTRATIVA ASSOCIAÇÃO
SALDO MÊS ANTERIOR
```

### 2. Modelo `Financeiro`

**Objetivo**: Registrar EXCLUSIVAMENTE movimentações financeiras manuais por médico.

**Características do sistema manual**:
- **operacao_auto**: Sempre False (não editável)
- **processado_por**: Usuário responsável obrigatório
- **Documentação**: Obrigatória para auditoria
- **Validações**: Garantem natureza manual
- **Controle**: Status, processamento, transferências
- **Auditoria**: Datas de criação, processamento, conciliação

**Tipos de lançamento**:
- **Créditos**: Aumentam o saldo do médico
  - Rateio de notas fiscais
  - Recebimentos diversos
  - Estornos a favor
  - Rendimentos de aplicações

- **Débitos**: Diminuem o saldo do médico
  - Rateio de despesas
  - Adiantamentos de lucro
  - Impostos retidos
  - Transferências bancárias

### 3. Modelo `SaldoMensalMedico`

**Objetivo**: Manter resumo mensal dos saldos de cada médico para consultas rápidas.

**Informações consolidadas**:
- Saldo inicial, créditos, débitos, saldo final
- Detalhamento por tipo de receita (consultas, plantão, outros)
- Detalhamento por tipo de despesa (folha, geral, individual)
- Controle de transferências realizadas
- Status do fechamento mensal

## Fluxos Operacionais

### 1. Rateio de Nota Fiscal

Quando uma nota fiscal é recebida:

1. **Criação da NF**: Dados básicos + tipo de serviço (obrigatório)
2. **Cálculo automático de impostos**: Baseado nas alíquotas configuradas
3. **Definição do rateio**: Percentuais por médico (deve totalizar 100%)
4. **Criação dos lançamentos**: Um crédito para cada médico
5. **Marcação como rateada**: NF fica com status "rateada"

```python
# Exemplo de rateio
rateios = {
    medico1.id: Decimal('40.00'),  # 40%
    medico2.id: Decimal('35.00'),  # 35%
    medico3.id: Decimal('25.00'),  # 25%
}

lancamentos = Financeiro.criar_rateio_nota_fiscal(nota_fiscal, rateios, usuario)
```

### 2. Lançamentos de Despesas

Para despesas rateadas entre médicos:

1. **Criação da despesa**: Com item de despesa dos grupos FOLHA ou GERAL
2. **Configuração de percentuais**: Por médico e por mês
3. **Processamento do rateio**: Criação automática de débitos
4. **Lançamentos no financeiro**: Um débito para cada médico

### 3. Lançamentos Manuais

Para movimentações não automáticas:

1. **Seleção da descrição**: Escolha de descrição padronizada
2. **Definição dos valores**: Valor e tipo (crédito/débito)
3. **Documentação**: Número do documento, forma de pagamento
4. **Processamento**: Mudança de status para "processado"

### 4. Transferências Bancárias

Para transferir valores para contas dos médicos:

1. **Identificação de créditos**: Busca lançamentos não transferidos
2. **Processamento**: Marcação como transferido
3. **Controle**: Registro da data e valor transferido
4. **Status**: Mudança para "transferido"

## Relatórios e Consultas

### 1. Extrato Individual

Movimentações detalhadas de um médico em período específico:

```python
extrato = Financeiro.obter_extrato_medico(medico, data_inicio, data_fim)
```

### 2. Saldo Mensal

Resumo consolidado por mês:

```python
saldo = SaldoMensalMedico.calcular_saldo_mensal(medico, mes_referencia)
```

### 3. Relatório de Saldos

Posição de todos os médicos em uma data:

```python
for medico in medicos:
    calculo = Financeiro.calcular_saldo_medico(medico, data_inicio, data_fim)
    print(f"{medico.pessoa.name}: R$ {calculo['saldo']}")
```

## Vantagens do Sistema

### 1. **Transparência Total**
- Cada médico vê exatamente suas movimentações
- Histórico completo de créditos e débitos
- Rastreabilidade de todas as operações

### 2. **Controle Gerencial**
- Saldos consolidados por mês
- Relatórios detalhados por período
- Estatísticas de uso das descrições

### 3. **Automação**
- Rateio automático de notas fiscais
- Cálculo automático de impostos
- Processamento automático de despesas

### 4. **Auditoria**
- Trilha completa de auditoria
- Controle de quem processou cada operação
- Datas de criação, processamento e conciliação

### 5. **Flexibilidade**
- Descrições customizáveis por conta
- Percentuais de rateio configuráveis
- Múltiplas formas de pagamento

## Segurança e Controles

### 1. **Validações**
- Somatório de percentuais de rateio = 100%
- Valores sempre positivos
- Relacionamentos consistentes entre entidades

### 2. **Status de Controle**
- Pendente → Processado → Conciliado → Transferido
- Impossibilidade de alterar lançamentos processados
- Controle de acesso por usuário

### 3. **Integridade**
- Foreign keys com CASCADE apropriado
- Unique constraints em campos críticos
- Validações customizadas nos modelos

## Integração com Sistema Contábil

### 1. **Notas Fiscais**
- Integração direta com modelo NotaFiscal
- Aplicação automática de alíquotas diferenciadas
- Controle de status (pendente → rateada)

### 2. **Despesas**
- Vinculação com sistema de despesas
- Rateio baseado em percentuais mensais
- Separação por grupos (FOLHA, GERAL, SOCIO)

### 3. **Tributação**
- Cálculo automático de impostos
- Retenções na fonte
- Relatórios tributários

## Exemplo de Uso Prático

```python
# 1. Criar descrições padrão
Desc_movimentacao_financeiro.criar_descricoes_padrao(conta)

# 2. Processar nota fiscal
nota_fiscal.calcular_impostos_automaticamente()
rateios = {medico1.id: 50.0, medico2.id: 50.0}
Financeiro.criar_rateio_nota_fiscal(nota_fiscal, rateios)

# 3. Lançamento manual de adiantamento
desc_adiantamento = Desc_movimentacao_financeiro.objects.get(
    conta=conta, descricao="ADIANTAMENTO DE LUCRO"
)
Financeiro.objects.create(
    conta=conta,
    socio=medico1,
    tipo=Financeiro.tipo_t.DEBITO,
    descricao=desc_adiantamento,
    valor=Decimal('2000.00'),
    status='processado'
)

# 4. Calcular saldo mensal
saldo = SaldoMensalMedico.calcular_saldo_mensal(medico1, date.today())
print(f"Saldo: {saldo.saldo_formatado}")

# 5. Transferir valores
creditos_pendentes = Financeiro.objects.filter(
    socio=medico1,
    tipo=Financeiro.tipo_t.CREDITO,
    transferencia_realizada=False
)
for credito in creditos_pendentes:
    credito.marcar_como_transferido()
```

## Próximos Passos

1. **Interface Administrativa**: Aprimorar Django Admin para facilitar operações
2. **Dashboard**: Criar painéis visuais para médicos e gestores
3. **Notificações**: Alertas para saldos, transferências pendentes
4. **Integração Bancária**: API para automatizar transferências
5. **Relatórios Avançados**: Gráficos e análises de performance

O sistema está pronto para produção e oferece uma base sólida para o controle financeiro individual dos médicos em associações médicas.
