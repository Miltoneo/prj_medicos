# Sistema de Alíquotas e Tributação - Associações Médicas

## Visão Geral

O sistema implementa um modelo completo de tributação para associações médicas, permitindo o cálculo automático de todos os impostos incidentes sobre as receitas (notas fiscais) de forma flexível e auditável.

## Modelo Alicotas

### Propósito
A tabela `Alicotas` centraliza todas as alíquotas de impostos e regras para cálculo automático da tributação das associações médicas. Cada conta (tenant) pode ter suas próprias configurações tributárias.

### Impostos Suportados

#### 1. ISS (Imposto Sobre Serviços)
- **Tipo**: Municipal
- **Incidência**: Direto sobre o valor bruto da nota fiscal
- **Faixa típica**: 2% a 5%
- **Observação**: Varia conforme o município e tipo de serviço

#### 2. PIS (Programa de Integração Social)
- **Tipo**: Federal
- **Incidência**: Direto sobre o valor bruto da nota fiscal
- **Alíquota padrão**: 0,65%
- **Base legal**: Contribuição para programas sociais

#### 3. COFINS (Contribuição para o Financiamento da Seguridade Social)
- **Tipo**: Federal
- **Incidência**: Direto sobre o valor bruto da nota fiscal
- **Alíquota padrão**: 3,00%
- **Base legal**: Contribuição para seguridade social

#### 4. IRPJ (Imposto de Renda Pessoa Jurídica)
- **Tipo**: Federal
- **Regime**: Lucro Presumido
- **Base de cálculo**: 32% da receita bruta (configurável)
- **Alíquota normal**: 15% sobre a base de cálculo
- **Adicional**: 10% sobre o excesso de R$ 20.000,00/mês (base de cálculo)
- **Cálculo**: Progressivo com limite para adicional

#### 5. CSLL (Contribuição Social sobre o Lucro Líquido)
- **Tipo**: Federal
- **Base de cálculo**: 32% da receita bruta (configurável)
- **Alíquota**: 9% para prestação de serviços
- **Observação**: Pode variar conforme atividade

## Estrutura de Campos

### Configurações Básicas
```python
conta = ForeignKey(Conta)  # Multi-tenant
ativa = BooleanField       # Controle de ativação
```

### Impostos Diretos
```python
ISS = DecimalField(5,2)     # Alíquota ISS (%)
PIS = DecimalField(5,2)     # Alíquota PIS (%)
COFINS = DecimalField(5,2)  # Alíquota COFINS (%)
```

### Configurações IRPJ
```python
IRPJ_BASE_CAL = DecimalField(5,2)                    # Base cálculo (% receita)
IRPJ_ALIC_1 = DecimalField(5,2)                     # Alíquota normal (15%)
IRPJ_ALIC_2 = DecimalField(5,2)                     # Alíquota total (25%)
IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL = DecimalField # Limite adicional (R$)
IRPJ_ADICIONAL = DecimalField(5,2)                  # Adicional (10%)
```

### Configurações CSLL
```python
CSLL_BASE_CAL = DecimalField(5,2)  # Base cálculo (% receita)
CSLL_ALIC_1 = DecimalField(5,2)    # Alíquota normal (9%)
CSLL_ALIC_2 = DecimalField(5,2)    # Alíquota alternativa
```

### Controle de Vigência
```python
data_vigencia_inicio = DateField    # Início vigência
data_vigencia_fim = DateField      # Fim vigência
observacoes = TextField            # Observações
```

## Funcionalidades Principais

### 1. Validação de Alíquotas
```python
def clean(self):
    # Valida ranges de alíquotas
    # Valida datas de vigência
    # Garante consistência dos dados
```

### 2. Verificação de Vigência
```python
@property
def eh_vigente(self):
    # Verifica se está ativa
    # Verifica período de vigência
    # Considera data atual
```

### 3. Cálculo de Impostos
```python
def calcular_impostos_nf(self, valor_bruto, tipo_servico):
    # Calcula todos os impostos
    # Aplica regras específicas (IRPJ adicional)
    # Retorna valores detalhados
```

### 4. Obtenção de Configuração Vigente
```python
@classmethod
def obter_alicota_vigente(cls, conta, data_referencia):
    # Busca configuração ativa
    # Considera período de vigência
    # Retorna configuração aplicável
```

## Exemplo de Cálculo

### Dados de Entrada
- **Valor Bruto**: R$ 10.000,00
- **ISS**: 3%
- **PIS**: 0,65%
- **COFINS**: 3%
- **IRPJ Base**: 32%
- **CSLL Base**: 32%

### Cálculos
```
Impostos Diretos:
- ISS: R$ 10.000 × 3% = R$ 300,00
- PIS: R$ 10.000 × 0,65% = R$ 65,00
- COFINS: R$ 10.000 × 3% = R$ 300,00

Bases de Cálculo:
- Base IRPJ: R$ 10.000 × 32% = R$ 3.200,00
- Base CSLL: R$ 10.000 × 32% = R$ 3.200,00

IRPJ:
- Normal: R$ 3.200 × 15% = R$ 480,00
- Adicional: R$ 0 (base < R$ 20.000)
- Total IRPJ: R$ 480,00

CSLL:
- CSLL: R$ 3.200 × 9% = R$ 288,00

Total de Impostos: R$ 1.433,00
Valor Líquido: R$ 8.567,00
```

## Integração com NotaFiscal

### Aplicação Automática
```python
def aplicar_impostos_nota_fiscal(self, nota_fiscal):
    calculo = self.calcular_impostos_nf(nota_fiscal.val_bruto)
    
    # Atualiza campos da nota fiscal
    nota_fiscal.val_liquido = calculo['valor_liquido']
    nota_fiscal.val_ISS = calculo['valor_iss']
    nota_fiscal.val_PIS = calculo['valor_pis']
    nota_fiscal.val_COFINS = calculo['valor_cofins']
    nota_fiscal.val_IR = calculo['valor_ir']
    nota_fiscal.val_CSLL = calculo['valor_csll']
```

### Fluxo de Uso
1. **Criação da Nota Fiscal**: Informar apenas valor bruto
2. **Busca de Alíquotas**: Sistema localiza configuração vigente
3. **Cálculo Automático**: Aplica todas as regras tributárias
4. **Atualização**: Preenche todos os campos de impostos
5. **Validação**: Verifica consistência dos cálculos

## Configurações por Regime Tributário

### Lucro Presumido (Padrão)
```python
IRPJ_BASE_CAL = 32.00    # 32% da receita bruta
CSLL_BASE_CAL = 32.00    # 32% da receita bruta
IRPJ_ALIC_1 = 15.00      # 15% normal
IRPJ_ADICIONAL = 10.00   # 10% adicional
CSLL_ALIC_1 = 9.00       # 9% para serviços
```

### Simples Nacional (Futuro)
```python
# Será implementado conforme necessidade
# Alíquotas unificadas por faixa de receita
```

## Auditoria e Controle

### Controle de Versões
- **created_at/updated_at**: Timestamps automáticos
- **created_by**: Usuário que criou a configuração
- **observacoes**: Justificativas e observações

### Vigência
- **data_vigencia_inicio**: Quando a configuração entra em vigor
- **data_vigencia_fim**: Quando expira (opcional)
- **ativa**: Flag para ativar/desativar

### Validações
- **Ranges de alíquotas**: Impede valores impossíveis
- **Datas de vigência**: Garante consistência temporal
- **Configuração única**: Uma configuração ativa por vez

## Relatórios e Consultas

### Análise de Carga Tributária
```python
resultado = alicota.calcular_impostos_nf(10000)
print(f"Carga tributária efetiva: {resultado['total_impostos']/resultado['valor_bruto']*100:.2f}%")
```

### Comparação de Cenários
```python
# Comparar diferentes configurações
# Simular impacto de mudanças
# Análise de sensibilidade
```

## Considerações Técnicas

### Performance
- **Índices**: conta + ativa + vigência
- **Cache**: Configurações vigentes
- **Lazy Loading**: Cálculos sob demanda

### Manutenibilidade
- **Documentação inline**: Cada campo documentado
- **Validações robustas**: Previne dados inconsistentes
- **Testes unitários**: Cobertura dos cálculos

### Escalabilidade
- **Multi-tenant**: Uma configuração por conta
- **Versionamento**: Histórico de mudanças
- **Flexibilidade**: Novos impostos facilmente adicionáveis

## Próximos Passos

1. **Implementar UI**: Interface para gestão de alíquotas
2. **Relatórios**: Dashboards de carga tributária
3. **Integração**: APIs para sistemas contábeis
4. **Automação**: Cálculos em tempo real
5. **Compliance**: Adequação a mudanças legais

---

Este sistema garante cálculos tributários precisos, auditáveis e flexíveis, atendendo às necessidades específicas das associações médicas e permitindo adaptação a diferentes cenários tributários.
