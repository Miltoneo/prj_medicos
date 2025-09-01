# Fluxo de Lançamento Automático de Impostos - Implementado

## Resumo da Implementação

Foi implementado um fluxo completo para lançamento automático dos impostos a pagar do "Espelho Cálculo de Impostos" na conta corrente do mês seguinte.

## Arquivos Criados/Modificados

### 1. `medicos/views_lancamento_impostos.py` (NOVO)
- **Função**: `lancar_impostos_conta_corrente()`
  - Cria lançamentos automáticos dos impostos na conta corrente
  - Valida empresa no contexto da sessão
  - Usa transação para garantir consistência
  - Impede duplicação de lançamentos
  
- **Função**: `preview_lancamentos_impostos()`
  - Mostra preview dos lançamentos que serão criados
  - Identifica lançamentos que já existem
  - Calcula total a ser lançado

### 2. `medicos/urls.py` (MODIFICADO)
Adicionadas as URLs:
```python
path('empresas/<int:empresa_id>/socio/<int:socio_id>/impostos/<int:mes>/<int:ano>/preview/', views_lancamento_impostos.preview_lancamentos_impostos, name='preview_lancamentos_impostos'),
path('empresas/<int:empresa_id>/socio/<int:socio_id>/impostos/<int:mes>/<int:ano>/lancar/', views_lancamento_impostos.lancar_impostos_conta_corrente, name='lancar_impostos_conta_corrente'),
```

### 3. `medicos/templates/relatorios/relatorio_mensal_socio.html` (MODIFICADO)
- Adicionado botão "Visualizar" e "Lançar Impostos" no quadro "Espelho Cálculo de Impostos"
- Implementado JavaScript para preview e lançamento
- Modal responsivo mostrando detalhes dos impostos a serem lançados

### 4. `medicos/views_relatorios.py` (MODIFICADO)
- Adicionados parâmetros `mes` e `ano` ao contexto do template
- Necessário para que o JavaScript saiba qual período processar

## Como Funciona

### 1. Interface do Usuário
No relatório mensal do sócio, após o quadro "Espelho Cálculo de Impostos", há dois botões:
- **Visualizar**: Mostra preview dos lançamentos sem criar
- **Lançar Impostos**: Cria os lançamentos efetivamente

### 2. Validações Implementadas
- ✅ Empresa deve estar no contexto da sessão
- ✅ Sócio deve existir e pertencer à empresa
- ✅ Verifica se já existem lançamentos para o período
- ✅ Só cria lançamentos para impostos com valor > 0

### 3. Dados dos Lançamentos Criados

**Para cada imposto com valor a pagar:**
- **Data**: Dia 15 do mês seguinte ao relatório
- **Sócio**: Mesmo sócio do relatório
- **Valor**: Negativo (saída de dinheiro)
- **Descrição**: Auto-criada (ex: "Pagamento PIS")
- **Histórico**: "Pagamento {IMPOSTO} - Competência {MM/AAAA}"
- **Instrumento**: DARF (PIS/COFINS/IRPJ/CSLL) ou Guia Municipal (ISSQN)

### 4. Exemplo de Lançamentos Criados

Para o exemplo do relatório:
```
LANÇAMENTOS CONTA CORRENTE - FEVEREIRO/2025
Data       | Descrição                           | Valor   | Instrumento
15/02/2025 | Pagamento PIS - Competência 01/2025 | -29,99  | DARF
15/02/2025 | Pagamento COFINS - Competência 01/2025 | -138,36 | DARF
15/02/2025 | Pagamento IRPJ - Competência 01/2025 | -665,90 | DARF
15/02/2025 | Pagamento CSLL - Competência 01/2025 | -386,07 | DARF
15/02/2025 | Pagamento ISSQN - Competência 01/2025 | -453,19 | Guia Municipal
TOTAL DÉBITOS: R$ 1.673,51
```

## Funcionalidades Avançadas

### 1. Preview Modal
- Lista todos os impostos a serem lançados
- Mostra quais já existem (badge amarelo)
- Calcula total líquido a ser lançado
- Interface responsiva Bootstrap

### 2. Controle de Duplicação
- Verifica se já existe lançamento para o imposto no mês
- Busca por descrição + sócio + período + competência no histórico
- Pula impostos já lançados

### 3. Criação Automática de Cadastros
- Cria automaticamente descrições de movimentação para cada imposto
- Cria instrumentos bancários DARF e Guia Municipal se não existirem
- Usa códigos padronizados: `IMPOSTO_PIS`, `IMPOSTO_COFINS`, etc.

## Integração com Sistema Existente

### 1. Dados Origem
- Usa exatamente os mesmos valores do "Espelho Cálculo de Impostos"
- Respeita o regime tributário da empresa (competência/caixa)
- Considera apenas a parte do sócio (não da empresa toda)

### 2. Destino dos Lançamentos
- Tabela: `MovimentacaoContaCorrente`
- Visível na tela: "Lançamentos Bancários" (Conta Corrente)
- Impacta automaticamente o saldo da conta corrente

### 3. Campos Obrigatórios Atendidos
- ✅ `data_movimentacao`: 15 do mês seguinte
- ✅ `descricao_movimentacao`: Criada automaticamente
- ✅ `socio`: Mesmo do relatório
- ✅ `valor`: Negativo (débito bancário)
- ✅ `historico_complementar`: Com referência à competência

## Benefícios da Implementação

1. **Automatização**: Elimina lançamento manual imposto por imposto
2. **Consistência**: Usa exatamente os valores calculados no relatório
3. **Rastreabilidade**: Histórico completo com competência de origem
4. **Segurança**: Validações contra duplicação e contexto inválido
5. **Usabilidade**: Interface intuitiva com preview antes de confirmar
6. **Integração**: Funciona perfeitamente com o sistema existente

## Como Usar

1. Acesse o "Relatório Mensal do Sócio"
2. Selecione um sócio e período
3. No quadro "Espelho Cálculo de Impostos", clique em:
   - **"Visualizar"** para ver preview dos lançamentos
   - **"Lançar Impostos"** para criar os lançamentos
4. Confirme no modal ou aguarde mensagem de sucesso
5. Opcionalmente, vá para "Lançamentos Bancários" para verificar

**Fonte**: Implementação baseada nas regras documentadas em `.github/copilot-instructions.md` e modelos do sistema existente.
