# Correções Aplicadas - Alíquotas CSLL

## Problema Identificado
A tabela "Apuração Trimestral - CSLL" não estava considerando as alíquotas específicas do CSLL configuradas no modelo Aliquotas, usando valores hardcoded.

## Correções Implementadas

### 1. View (medicos/views_relatorios.py)

**Antes**: Valores hardcoded
```python
imposto_devido_csll = base_calculo * Decimal('0.09')  # 9% CSLL hardcoded
base_consultas = receita_consultas * Decimal('0.32')  # 32% hardcoded
base_outros = receita_outros * Decimal('0.08')        # 8% hardcoded
```

**Depois**: Alíquotas dinâmicas
```python
csll_aliquota = aliquotas_empresa.CSLL_ALIQUOTA / Decimal('100')
imposto_devido_csll = base_calculo * csll_aliquota

csll_presuncao_consultas = aliquotas_empresa.CSLL_PRESUNCAO_CONSULTA / Decimal('100')
csll_presuncao_outros = aliquotas_empresa.CSLL_PRESUNCAO_OUTROS / Decimal('100')
base_consultas = receita_consultas * csll_presuncao_consultas
base_outros = receita_outros * csll_presuncao_outros
```

**Adicionado ao contexto**: Variável `aliquotas` para o template
```python
'aliquotas': aliquotas_empresa,
```

### 2. Template (medicos/templates/relatorios/apuracao_de_impostos.html)

**Descrições atualizadas** para mostrar alíquotas dinâmicas:
- `(+) Base sobre receita do tipo "consultas médicas" ({{ aliquotas.CSLL_PRESUNCAO_CONSULTA }}%)`
- `(+) Base sobre receita do tipo "outros serviços" ({{ aliquotas.CSLL_PRESUNCAO_OUTROS }}%)`
- `(=) Total Imposto Devido ({{ aliquotas.CSLL_ALIQUOTA }}%)`

**Adicionadas observações** consistentes com a tabela "CSLL - Trimestres":
```html
<small class="text-muted fst-italic mt-2">* Cálculo imposto: por data de emissão da nota (regime competência) / por data de recebimento (regime caixa)</small>
<br>
<small class="text-muted fst-italic">* Retenção do imposto: por data de recebimento da nota</small>
```

### 3. Consistência com tabela "CSLL - Trimestres"

A tabela "CSLL - Trimestres" já estava usando alíquotas dinâmicas corretamente:
```python
linhas_csll = [
    {'descricao': f'Base consultas ({aliquotas_empresa.CSLL_PRESUNCAO_CONSULTA}%)', ...},
    {'descricao': f'Base outros ({aliquotas_empresa.CSLL_PRESUNCAO_OUTROS}%)', ...},
    {'descricao': f'Imposto devido ({aliquotas_empresa.CSLL_ALIQUOTA}%)', ...},
]
```

## Campos Utilizados do Modelo Aliquotas

- `CSLL_ALIQUOTA`: Alíquota do CSLL (padrão 9%)
- `CSLL_PRESUNCAO_CONSULTA`: Presunção para consultas médicas (padrão 32%)
- `CSLL_PRESUNCAO_OUTROS`: Presunção para outros serviços (padrão 32%)

## Resultado

✅ Ambas as tabelas CSLL agora seguem a mesma abordagem
✅ Alíquotas são lidas dinamicamente da configuração fiscal
✅ Cálculos respeitam as configurações específicas de cada empresa
✅ Interface mostra as alíquotas aplicadas para transparência

**Fonte**: Correção aplicada conforme `.github/copilot-instructions.md`, seção 5 - Regras de análise global de impacto.
