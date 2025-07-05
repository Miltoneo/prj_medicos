# Documentação: Aplicações Financeiras Simplificadas

## Visão Geral

O modelo de Aplicações Financeiras foi simplificado para focar apenas nos dados essenciais: **rendimentos mensais** e **IRRF**. Este modelo integra automaticamente com o sistema tributário da empresa, garantindo que os rendimentos sejam contabilizados nas apurações de impostos.

## Modelo AplicacaoFinanceira

### Campos Principais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `data` | DateField | Data de referência (mês/ano dos rendimentos) |
| `rendimentos` | DecimalField | Valor dos rendimentos no mês |
| `irrf` | DecimalField | Imposto de Renda Retido na Fonte |
| `fornecedor` | ForeignKey | Instituição financeira da aplicação |
| `descricao` | CharField | Descrição opcional da aplicação |

### Funcionalidades Automáticas

#### 1. Cálculo Automático de IRRF
- Para rendimentos **acima de R$ 1.000**: IRRF de 15% é aplicado automaticamente se não informado
- Para rendimentos **até R$ 1.000**: sem IRRF automático

#### 2. Propriedades Calculadas
- `rendimento_liquido`: Rendimento após dedução do IRRF
- `aliquota_efetiva`: Percentual efetivo de IRRF aplicado

#### 3. Validações
- Rendimentos devem ser maiores que zero
- IRRF não pode ser negativo
- IRRF não pode ser maior que os rendimentos

## Integração Financeira

### Geração de Lançamentos

O método `gerar_lancamentos_financeiros()` prepara as informações para criar lançamentos no sistema:

```python
aplicacao = AplicacaoFinanceira.objects.create(
    conta=conta,
    fornecedor=banco,
    data=date(2025, 1, 1),
    rendimentos=Decimal('2000.00'),
    irrf=Decimal('300.00')
)

info = aplicacao.gerar_lancamentos_financeiros()
# Retorna:
# {
#     'data': date(2025, 1, 1),
#     'fornecedor': 'Banco XYZ',
#     'rendimentos': Decimal('2000.00'),
#     'irrf': Decimal('300.00'),
#     'rendimento_liquido': Decimal('1700.00'),
#     'lancamentos': [
#         {
#             'tipo': 'credito',
#             'valor': Decimal('2000.00'),
#             'categoria': 'rendimento_aplicacao',
#             'observacoes': 'Rendimento aplicação financeira - Ref: 01/2025'
#         },
#         {
#             'tipo': 'debito',
#             'valor': Decimal('300.00'),
#             'categoria': 'irrf_aplicacao',
#             'observacoes': 'IRRF s/ rendimento aplicação - Ref: 01/2025'
#         }
#     ]
# }
```

### Categorias Automáticas

O sistema cria automaticamente as seguintes categorias:

#### Categoria: `rendimento_aplicacao`
- **Natureza**: Receita
- **Nome**: "Rendimento de Aplicação Financeira"
- **Tipo**: Crédito

#### Categoria: `irrf_aplicacao`
- **Natureza**: Despesa
- **Nome**: "IRRF sobre Aplicação Financeira"
- **Tipo**: Débito

## Integração Tributária

### Cálculo de IR Empresarial

O método `calcular_ir_devido_empresa()` fornece informações para apuração fiscal:

```python
ir_info = aplicacao.calcular_ir_devido_empresa()
# Retorna:
# {
#     'rendimento_bruto': Decimal('2000.00'),
#     'irrf_retido': Decimal('300.00'),
#     'rendimento_liquido': Decimal('1700.00'),
#     'base_calculo_irpj': Decimal('2000.00'),  # Rendimento bruto integra a base
#     'irrf_compensavel': Decimal('300.00'),    # IRRF pode ser compensado
#     'observacoes': 'Rendimento de aplicação financeira integra base de cálculo IRPJ/CSLL. IRRF é compensável.'
# }
```

### Regras Tributárias

1. **Base de Cálculo**: Rendimento bruto integra a base de cálculo do IRPJ/CSLL
2. **IRRF Compensável**: O IRRF retido pode ser compensado/deduzido do imposto devido
3. **Periodicidade**: Controle mensal para acompanhar a evolução fiscal

## Relatórios Consolidados

### Integração Automática

O sistema integra automaticamente com os relatórios consolidados mensais:

```python
# No método gerar_relatorio_completo()
self.incluir_dados_aplicacoes_financeiras()
```

### Dados Incluídos nos Relatórios

- **Créditos Financeiros**: Total de rendimentos do período
- **Débitos Financeiros**: Total de IRRF do período
- **Observações**: Detalhes sobre movimentações de aplicações

Exemplo de observação gerada:
```
"Aplicações Financeiras - 3 movimentações: Rendimentos R$ 5.500,00, IRRF R$ 825,00, Rendimento Líquido R$ 4.675,00"
```

## Uso Prático

### Exemplo de Lançamento Mensal

```python
# Janeiro/2025 - CDB 12 meses
aplicacao_jan = AplicacaoFinanceira.objects.create(
    conta=conta_empresa,
    fornecedor=banco_xyz,
    data=date(2025, 1, 1),
    rendimentos=Decimal('3000.00'),
    irrf=Decimal('450.00'),
    descricao='CDB 12 meses - Taxa 12% a.a.'
)

# Obter informações para contabilização
info_lancamentos = aplicacao_jan.gerar_lancamentos_financeiros()

# Calcular impacto fiscal
ir_empresa = aplicacao_jan.calcular_ir_devido_empresa()
```

### Resumo Trimestral

```python
# Obter resumo do primeiro trimestre
resumo = AplicacaoFinanceira.obter_resumo_periodo(
    conta=conta_empresa,
    data_inicio=date(2025, 1, 1),
    data_fim=date(2025, 3, 31)
)

print(f"Rendimentos: R$ {resumo['total_rendimentos']:,.2f}")
print(f"IRRF: R$ {resumo['total_irrf']:,.2f}")
print(f"Líquido: R$ {resumo['rendimento_liquido']:,.2f}")
print(f"Aplicações: {resumo['count_aplicacoes']}")
```

## Formulários e Interface

### Campos do Formulário

O formulário `Rendimentos` foi atualizado para usar apenas os campos essenciais:

```python
class Meta:
    model = AplicacaoFinanceira
    fields = ('data', 'rendimentos', 'irrf', 'descricao')
```

### Tabela de Exibição

A tabela `Aplic_fincanceiras_table` exibe:
- Data de referência
- Valor dos rendimentos
- IRRF retido
- Link para edição

## Compatibilidade

### Alias para Código Legacy

Para manter compatibilidade com código existente:

```python
# Alias no final do modelo
Aplic_financeiras = AplicacaoFinanceira
```

### Migração de Dados

Se houver dados existentes no modelo antigo, será necessário criar uma migração para:

1. Transferir dados relevantes (data, rendimentos, irrf, fornecedor)
2. Atualizar referências no código
3. Ajustar formulários e views

## Benefícios da Simplificação

1. **Facilidade de Uso**: Apenas dados essenciais
2. **Integração Automática**: Com sistema tributário e relatórios
3. **Cálculos Automáticos**: IRRF e validações
4. **Conformidade Fiscal**: Atende requisitos de apuração de impostos
5. **Manutenibilidade**: Código mais simples e direto

## Considerações Fiscais

### Para Empresas do Lucro Real
- Rendimentos integram a receita financeira
- IRRF é compensável com IRPJ devido
- Controle mensal facilita apurações trimestrais

### Para Empresas do Lucro Presumido
- Rendimentos podem impactar no limite de receita
- IRRF é definitivo (não compensável)
- Controle mensal para acompanhamento

### Documentação Fiscal
- Manter comprovantes dos rendimentos
- Registrar retenções de IRRF
- Controlar datas de aplicação e vencimento
