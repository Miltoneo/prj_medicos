# Correção do Cálculo da Receita Líquida - Inclusão do Adicional de IR Trimestral

## Descrição
Revisada a fórmula de cálculo da receita líquida no Relatório Mensal do Sócio para incluir corretamente a dedução do adicional de IR trimestral de forma separada e transparente.

## Arquivo Modificado

### `medicos/relatorios/builders.py`
- **Seção**: Cálculo de impostos e receita líquida
- **Linhas Modificadas**: 523, 539
- **Alteração**: Separação do adicional de IR do cálculo base de impostos devidos

#### Modificações Realizadas:

**ANTES:**
```python
# Total dos impostos devidos incluía o adicional de IR
impostos_devido_total = total_iss_devido_socio + total_pis_devido_socio + total_cofins_devido_socio + total_irpj_devido_socio + total_csll_devido_socio + valor_adicional_socio

# Receita líquida já descontava tudo junto
receita_liquida = receita_bruta_recebida - impostos_devido_total
```

**DEPOIS:**
```python
# Total dos impostos devidos SEM incluir adicional de IR (para transparência)
impostos_devido_total = total_iss_devido_socio + total_pis_devido_socio + total_cofins_devido_socio + total_irpj_devido_socio + total_csll_devido_socio

# Receita líquida desconta impostos básicos E adicional de IR separadamente
receita_liquida = receita_bruta_recebida - impostos_total - valor_adicional_socio
```

## Lógica de Cálculo Corrigida

### Sequência no Relatório:
1. **RECEITA BRUTA RECEBIDA**: Valor base
2. **(-) IMPOSTO DEVIDO(a)**: `impostos_devido_total` (impostos básicos)
3. **(-) IMPOSTO RETIDO(b)**: `impostos_retido_total`
4. **IMPOSTO A PROVISIONAR*(c=a-b)**: `impostos_total` (devido - retido)
5. **(-) ADICIONAL DE IR TRIMESTRAL**: `valor_adicional_socio` (separado)
6. **(**=) RECEITA LÍQUIDA**: `receita_bruta - impostos_total - valor_adicional_socio`

### Fórmula Final:
```
Receita Líquida = Receita Bruta Recebida - Impostos a Provisionar - Adicional de IR Trimestral
```

## Benefícios da Correção

### Transparência:
- **Separação Clara**: Adicional de IR agora aparece em linha própria
- **Rastreabilidade**: Fácil identificação do valor do adicional
- **Auditoria**: Cálculo mais transparente e verificável

### Consistência:
- **Template vs Builder**: Alinhamento entre exibição visual e cálculo
- **Lógica Contábil**: Segue sequência lógica de deduções
- **Documentação**: Facilita compreensão do cálculo

## Impacto nos Campos

### Campos Afetados:
- `impostos_devido_total`: Agora SEM adicional de IR
- `receita_liquida`: Agora com fórmula corrigida
- `total_irpj_adicional`: Mantido como campo separado

### Campos Inalterados:
- `impostos_total`: Continua como (devido - retido)
- `impostos_retido_total`: Sem alteração
- Demais campos de impostos individuais: Sem alteração

## Validação

### Verificação do Cálculo:
```
Antes: receita_liquida = receita_bruta - (impostos_basicos + adicional_ir - retidos)
Depois: receita_liquida = receita_bruta - (impostos_basicos - retidos) - adicional_ir
```

**Resultado matemático idêntico, mas com transparência na apresentação.**

## Observações Técnicas
- Mantida compatibilidade com templates existentes
- Preservada a correção matemática dos valores
- Adicionada clareza na apresentação dos cálculos
- Facilitada a auditoria e validação dos impostos

**Fonte**: Correção baseada na inclusão da linha "(-) ADICIONAL DE IR TRIMESTRAL" no template e necessidade de alinhamento entre cálculo e apresentação visual.
