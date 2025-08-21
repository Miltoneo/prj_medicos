# Atualização do Relatório Mensal do Sócio - Campo OUTROS

## Problema Identificado

O campo "OUTROS" não estava sendo exibido corretamente no quadro de Receitas devido a uma **inconsistência entre variáveis** no builder e template.

### Causa Raiz do Problema - INCONSISTÊNCIA DE VARIÁVEIS

**Problema principal:** Existiam **duas variáveis diferentes** calculando o total de "outros":

1. **`total_outros_socio`** - acumulava `rateio.valor_outros_medico` durante o loop das notas
2. **`total_nf_outros`** - somava os valores `outros` da lista final de notas fiscais

**Inconsistência no template:**
- **Quadro de Receitas** usava: `{{ relatorio.total_outros }}` (variável `total_outros_socio` = 0,00)
- **Tabela de Notas Fiscais** usava: `{{ relatorio.total_nf_outros }}` (variável `total_nf_outros` = 63,58)

Isso explica por que a tabela mostrava o valor correto (63,58) mas o quadro de receitas mostrava 0,00.

### Causa Secundária - Propriedade `valor_outros_medico`

Também foi corrigido um bug na propriedade `valor_outros_medico` do modelo `NotaFiscalRateioMedico` (linha 1308):

```python
# ANTES (problemático)
if not self.nota_fiscal or not self.nota_fiscal.val_outros or not self.nota_fiscal.val_bruto:
    return 0

# DEPOIS (corrigido)  
if not self.nota_fiscal or self.nota_fiscal.val_outros is None or not self.nota_fiscal.val_bruto:
    return 0
```

## Modificações Realizadas

### 1. Correção no Modelo (`medicos/models/fiscal.py`)

**Linha ~1308 - Propriedade `valor_outros_medico` corrigida:**
A mudança de `not self.nota_fiscal.val_outros` para `self.nota_fiscal.val_outros is None` garante que apenas valores `None` sejam considerados inválidos.

### 2. Builder (`medicos/relatorios/builders.py`)

**Unificação das variáveis:**
- Mantidas ambas variáveis por compatibilidade
- **Template alterado para usar `total_nf_outros`** (consistente com tabela)
- **Cálculo de `impostos_total` alterado** para usar `total_nf_outros`

```python
# ANTES
impostos_total = total_iss_socio + total_pis_socio + total_cofins_socio + total_irpj_socio + total_csll_socio + total_outros_socio + valor_adicional_socio

# DEPOIS  
impostos_total = total_iss_socio + total_pis_socio + total_cofins_socio + total_irpj_socio + total_csll_socio + total_nf_outros + valor_adicional_socio
```

### 3. Template (`medicos/templates/relatorios/relatorio_mensal_socio.html`)

**Unificação da variável no quadro de Receitas:**
```html
<!-- ANTES -->
<tr><td>6</td><td>OUTROS</td><td>{{ relatorio.total_outros|default:0|floatformat:2 }}</td></tr>

<!-- DEPOIS -->
<tr><td>6</td><td>OUTROS</td><td>{{ relatorio.total_nf_outros|default:0|floatformat:2 }}</td></tr>
```

## Cálculo da Receita Líquida Corrigido

A receita líquida agora considera corretamente o campo "OUTROS" na fórmula:
```python
impostos_total = total_iss_socio + total_pis_socio + total_cofins_socio + total_irpj_socio + total_csll_socio + total_outros_socio + valor_adicional_socio
receita_liquida = receita_bruta_recebida - impostos_total
```

## Estrutura Final do Quadro de Receitas

```
RECEITA BRUTA RECEBIDA* (=)    [valor]
1  serviços de consultas e plantões    [valor]
2  Serviços de vacinação, exames, procedimentos    [valor]

IMPOSTOS* (-)    [valor total]
1  PIS    [valor]
2  COFINS    [valor]
3  IRPJ    [valor]
4  CSLL    [valor]
5  ISSQN    [valor]
6  OUTROS    [valor]  ← CORRIGIDO
RECEITA LÍQUIDA (=)    [valor corrigido]
```

## Impacto das Mudanças

- **PRINCIPAL**: O campo "OUTROS" agora exibe valores corretos quando existem
- A RECEITA LÍQUIDA está matematicamente correta incluindo todas as deduções
- Correção beneficia todos os relatórios que usam a propriedade `valor_outros_medico`
- Mantida compatibilidade total com estrutura existente

## Arquivos Modificados

1. `medicos/models/fiscal.py` - Propriedade `valor_outros_medico` (PRINCIPAL)
2. `medicos/relatorios/builders.py` - Função `montar_relatorio_mensal_socio()`
3. `medicos/templates/relatorios/relatorio_mensal_socio.html` - Seção de Receitas

## Validação

Para validar as mudanças:
1. Acesse: http://localhost:8000/medicos/relatorio-mensal-socio/4/?mes_ano=2025-07&socio_id=7
2. Verifique que a linha "OUTROS" mostra valores corretos (incluindo 0,00 quando aplicável)
3. Confirme que a RECEITA LÍQUIDA reflete a dedução correta do campo "OUTROS"

**Fonte:** 
- `.github/copilot-instructions.md`, seção "Propagação obrigatória de revisões"
- `medicos/models/fiscal.py`, propriedade `valor_outros_medico` (linha 1301-1316)
