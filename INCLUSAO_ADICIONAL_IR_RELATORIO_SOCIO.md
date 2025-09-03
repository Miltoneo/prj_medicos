# Inclusão da Linha "(-) ADICIONAL DE IR TRIMESTRAL" no Relatório Mensal do Sócio

## Descrição
Adicionada a linha "(-) ADICIONAL DE IR TRIMESTRAL" no quadro de Receitas do Relatório Mensal do Sócio, posicionada após a linha "IMPOSTO A PROVISIONAR*(c=a-b)".

## Arquivo Modificado

### `medicos/templates/relatorios/relatorio_mensal_socio.html`
- **Seção**: Quadro de Receitas
- **Localização**: Linha 197 (após "IMPOSTO A PROVISIONAR*(c=a-b)")
- **Nova Linha Adicionada**: "(-) ADICIONAL DE IR TRIMESTRAL"

#### Modificação Realizada:

**Linha Adicionada:**
```django
<thead>
  <tr class="table-warning">
    <th>(-) ADICIONAL DE IR TRIMESTRAL</th>
    <th style="font-family: 'Courier New', monospace !important; font-weight: 500 !important; text-align: right !important;">{{ relatorio.total_irpj_adicional|floatformat:2 }}</th>
  </tr>
</thead>
```

## Campo de Dados Utilizado

### Fonte: `medicos/relatorios/builders.py`
- **Campo**: `total_irpj_adicional`
- **Localização**: Linha 616
- **Cálculo**: Baseado em `valor_adicional_socio`
- **Definição**: `'total_irpj_adicional': valor_adicional_socio`

#### Lógica de Cálculo (linhas 229):
```python
valor_adicional_socio = valor_adicional_rateio * participacao_socio if valor_adicional_rateio > 0 else 0
```

## Estilo Visual

### Características:
- **Classe CSS**: `table-warning` (fundo amarelo claro)
- **Fonte**: Courier New (monospace) para valores numéricos
- **Alinhamento**: Direita para valores monetários
- **Formatação**: 2 casas decimais via `floatformat:2`

## Posicionamento no Relatório

### Sequência no Quadro de Receitas:
1. IMPOSTO DEVIDO*(a)
2. IMPOSTO RETIDO*(b)
3. IMPOSTO A PROVISIONAR*(c=a-b)
4. **(-) ADICIONAL DE IR TRIMESTRAL** ← **Nova linha**
5. (=) RECEITA LÍQUIDA

## Regras de Negócio

### Adicional de IR Trimestral:
- Calculado com base na participação do sócio na receita bruta da empresa
- Considera percentuais de presunção (32% consultas, 8% outros serviços)
- Aplicado apenas sobre valores que excedem o limite de isenção
- Valor deduzido da receita líquida do sócio

## Observações Técnicas
- Campo já existente no builder, apenas adicionada a exibição no template
- Mantido padrão visual consistente com outras linhas do relatório
- Formatação monetária padronizada com resto do sistema

**Fonte**: Campo `total_irpj_adicional` definido em `medicos/relatorios/builders.py`, linha 616, e cálculo do adicional baseado nas linhas 218-229 do mesmo arquivo.
