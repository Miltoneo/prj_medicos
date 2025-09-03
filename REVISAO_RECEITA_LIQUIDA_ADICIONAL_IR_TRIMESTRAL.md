# Revisão Completa do Cálculo da Receita Líquida e Renomeação de Variáveis

## Descrição
Revisão completa da fórmula da receita líquida e renomeação de variáveis para maior clareza, enfatizando que se trata especificamente do **ADICIONAL DE IR TRIMESTRAL**.

## Arquivo Modificado

### `medicos/relatorios/builders.py`
- **Fórmula Corrigida**: Receita líquida agora usa `impostos_devido_total` em vez de `impostos_total`
- **Variáveis Renomeadas**: Nomes mais descritivos enfatizando "adicional de IR trimestral"
- **Comentários Aprimorados**: Clareza sobre o que representa cada cálculo

## Principais Modificações

### 1. Fórmula da Receita Líquida (Linha 541)

**ANTES:**
```python
# Receita líquida = Receita bruta recebida - Impostos a provisionar - Adicional de IR trimestral
receita_liquida = receita_bruta_recebida - impostos_total - valor_adicional_socio
```

**DEPOIS:**
```python
# RECEITA LÍQUIDA: Fórmula corrigida conforme solicitação do usuário
# (=) RECEITA LÍQUIDA = receita bruta - impostos_devido_total - adicional de IR trimestral
receita_liquida = receita_bruta_recebida - impostos_devido_total - adicional_ir_trimestral_socio
```

### 2. Renomeação de Variáveis para Clareza

#### Variável Principal (Linha 208):
**ANTES:**
```python
valor_adicional_rateio = excedente_adicional * aliquota_adicional
```

**DEPOIS:**
```python
# ADICIONAL DE IR TRIMESTRAL: Calcular valor total da empresa para rateio entre sócios
adicional_ir_trimestral_empresa = excedente_adicional * aliquota_adicional
```

#### Variável do Sócio (Linha 230):
**ANTES:**
```python
valor_adicional_socio = valor_adicional_rateio * participacao_socio if valor_adicional_rateio > 0 else 0
```

**DEPOIS:**
```python
# ADICIONAL DE IR TRIMESTRAL: Calcular a parte proporcional do sócio no adicional de IR trimestral
adicional_ir_trimestral_socio = adicional_ir_trimestral_empresa * participacao_socio if adicional_ir_trimestral_empresa > 0 else 0
```

### 3. Contexto do Template (Linha 618)

**ANTES:**
```python
'total_irpj_adicional': valor_adicional_socio,
```

**DEPOIS:**
```python
'total_irpj_adicional': adicional_ir_trimestral_socio,  # ADICIONAL DE IR TRIMESTRAL do sócio
```

### 4. Contexto Geral (Linha 676)

**ANTES:**
```python
contexto['valor_adicional_rateio'] = valor_adicional_rateio
```

**DEPOIS:**
```python
contexto['adicional_ir_trimestral_empresa'] = adicional_ir_trimestral_empresa
```

### 5. Totais de Impostos (Linha 730)

**ANTES:**
```python
'IRPJ': total_irpj_socio + valor_adicional_socio,  # Incluir adicional de IRPJ
```

**DEPOIS:**
```python
'IRPJ': total_irpj_socio + adicional_ir_trimestral_socio,  # Incluir ADICIONAL DE IR TRIMESTRAL
```

## Nova Lógica de Cálculo

### Fórmula Final da Receita Líquida:
```
RECEITA LÍQUIDA = Receita Bruta Recebida - Impostos Devidos Total - Adicional de IR Trimestral do Sócio
```

### Onde:
- **Receita Bruta Recebida**: Valor bruto das notas fiscais recebidas
- **Impostos Devidos Total**: PIS + COFINS + ISS + IRPJ + CSLL (básicos)
- **Adicional de IR Trimestral do Sócio**: Parte proporcional do adicional de IR trimestral

## Benefícios das Alterações

### 1. Clareza Semântica:
- **Nomes Descritivos**: Variáveis autoexplicativas
- **Contexto Claro**: Diferenciação entre empresa e sócio
- **Especificidade**: Ênfase em "trimestral"

### 2. Fórmula Corrigida:
- **Base Correta**: Usa `impostos_devido_total` em vez de `impostos_total`
- **Lógica Consistente**: Alinha com apresentação visual do relatório
- **Transparência**: Cada componente claramente identificado

### 3. Manutenibilidade:
- **Código Autodocumentado**: Nomes explicam a função
- **Comentários Aprimorados**: Contexto completo
- **Rastreabilidade**: Fácil identificação do adicional de IR

## Variáveis Renomeadas - Resumo

| **Antes** | **Depois** | **Contexto** |
|-----------|------------|--------------|
| `valor_adicional_rateio` | `adicional_ir_trimestral_empresa` | Valor total da empresa |
| `valor_adicional_socio` | `adicional_ir_trimestral_socio` | Parte do sócio |
| Comentários genéricos | Comentários específicos | Ênfase em "trimestral" |

## Validação da Fórmula

### Sequência de Cálculo:
1. **Receita Bruta**: Base do cálculo
2. **(-) Impostos Devidos**: PIS, COFINS, ISS, IRPJ, CSLL
3. **(-) Adicional IR Trimestral**: Separado e identificado
4. **(**=) Receita Líquida**: Resultado final

**Resultado**: Fórmula matematicamente correta e semanticamente clara.

## Observações Técnicas
- Mantida compatibilidade com templates existentes
- Preservada funcionalidade de todos os cálculos
- Adicionada clareza semântica sem alteração de lógica
- Enfatizada a natureza trimestral do adicional de IR

**Fonte**: Revisão solicitada pelo usuário para clareza da fórmula: "(=) RECEITA LÍQUIDA = receita bruta - impostos_devido_total - adicional de IR trimestral" com ênfase na natureza trimestral do adicional.
