# Inclusão de Alíquotas na Tabela "Apuração Trimestral - IRPJ"

## Descrição
Adicionadas as alíquotas de presunção nas descrições das linhas da tabela "Apuração Trimestral - IRPJ" para seguir o mesmo padrão da tabela "Apuração Trimestral - CSLL".

## Arquivo Modificado

### `medicos/templates/relatorios/apuracao_de_impostos.html`
- **Seção**: "Apuração Trimestral - IRPJ"
- **Linhas Modificadas**: 514 e 520
- **Alteração**: Incluídas alíquotas de presunção nas descrições

#### Modificações Realizadas:

**ANTES:**
```django
<td class="fw-medium">(+) Base sobre receita do tipo "consultas médicas"</td>
<td class="fw-medium">(+) Base sobre receita do tipo "outros serviços"</td>
```

**DEPOIS:**
```django
<td class="fw-medium">(+) Base sobre receita do tipo "consultas médicas" ({{ aliquotas.IRPJ_PRESUNCAO_CONSULTA }}%)</td>
<td class="fw-medium">(+) Base sobre receita do tipo "outros serviços" ({{ aliquotas.IRPJ_PRESUNCAO_OUTROS }}%)</td>
```

## Variáveis de Alíquotas Utilizadas

### Fonte: `medicos/models/fiscal.py`
- `IRPJ_PRESUNCAO_CONSULTA`: Alíquota de presunção para consultas médicas (32%)
- `IRPJ_PRESUNCAO_OUTROS`: Alíquota de presunção para outros serviços (8%)

## Padrão Seguido

### Referência: Tabela "Apuração Trimestral - CSLL"
A modificação seguiu exatamente o mesmo padrão já implementado na tabela CSLL:
```django
<td class="fw-medium">(+) Base sobre receita do tipo "consultas médicas" ({{ aliquotas.CSLL_PRESUNCAO_CONSULTA }}%)</td>
<td class="fw-medium">(+) Base sobre receita do tipo "outros serviços" ({{ aliquotas.CSLL_PRESUNCAO_OUTROS }}%)</td>
```

## Benefícios
- **Consistência Visual**: Padronização entre tabelas IRPJ e CSLL
- **Transparência**: Exibição clara das alíquotas utilizadas nos cálculos
- **Informação Completa**: Usuário visualiza tanto o resultado quanto a alíquota aplicada

## Observações Técnicas
- As alíquotas são obtidas dinamicamente do objeto `aliquotas` no contexto da view
- Mantida a estrutura responsiva e estilo Bootstrap existente
- Alteração puramente visual, sem impacto nos cálculos

**Fonte**: Modificação baseada no padrão existente na tabela CSLL, linhas 649 e 655 do mesmo arquivo.
