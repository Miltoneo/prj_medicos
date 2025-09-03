# Implementação da Tabela "Notas Fiscais Recebidas"

## Descrição
Implementação da tabela "Notas Fiscais Recebidas" no relatório de Apuração de Impostos, posicionada após a tabela "Notas Fiscais Emitidas".

## Arquivos Modificados

### 1. `medicos/views_relatorios.py`
- **Função Adicionada**: `calcular_notas_fiscais_recebidas()`
- **Localização**: Linhas 946-988 (antes da função de notas emitidas)
- **Contexto Adicionado**: `'notas_fiscais_recebidas': notas_fiscais_recebidas`
- **Critério de Filtro**: `dtRecebimento` (data de recebimento da nota fiscal)

#### Estrutura dos Dados Retornados:
```python
notas_fiscais_recebidas = {
    'receita_consultas': [12 valores mensais],
    'receita_outros': [12 valores mensais], 
    'receita_bruta_mensal': [12 valores mensais],
    'receita_bruta_trimestral': [4 valores trimestrais]
}
```

### 2. `medicos/templates/relatorios/apuracao_de_impostos.html`
- **Seção Adicionada**: "Notas Fiscais Recebidas"
- **Posicionamento**: Após a seção "Notas Fiscais Emitidas"
- **Estilo**: Bootstrap com tema warning (amarelo)
- **Estrutura**: Header duplo (T1-T4 trimestres, 1-12 meses)

#### Linhas da Tabela:
1. `(+) Total Receita consultas/Plantão` - Valores mensais
2. `(+) Total Receita outros` - Valores mensais  
3. `(=) Total receita bruta recebida` - Valores trimestrais (colspan=3)

## Diferenças entre Tabelas

### Notas Fiscais Recebidas vs Emitidas:
- **Recebidas**: Filtro por `dtRecebimento` (data de recebimento)
- **Emitidas**: Filtro por `dtEmissao` (data de emissão)
- **Cores**: Recebidas (warning/amarelo), Emitidas (primary/azul)
- **Ícones**: Recebidas (file-earmark-arrow-down), Emitidas (file-earmark-text)

## Regras de Negócio
- Considera apenas notas fiscais com `dtRecebimento` não nulo
- Separa receitas por tipo de serviço (`TIPO_SERVICO_CONSULTAS` vs outros)
- Calcula totais trimestrais automaticamente (T1: meses 1-3, T2: meses 4-6, etc.)
- Valores formatados com 2 casas decimais

## Observações Técnicas
- Utiliza mesma estrutura da tabela de notas emitidas para consistência
- Implementação responsiva com `table-responsive`
- Estilo consistente com o padrão Bootstrap do sistema
- Nota explicativa sobre critério temporal utilizado

**Fonte**: Implementação baseada na estrutura anexada pelo usuário e padrões existentes no arquivo `medicos/views_relatorios.py`, linhas 947-992.
