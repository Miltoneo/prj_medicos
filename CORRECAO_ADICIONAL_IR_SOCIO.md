# CORREÇÃO DO ADICIONAL DE IR TRIMESTRAL - RELATÓRIO MENSAL DO SÓCIO

## Problema Identificado
No "Relatório Mensal do Sócio", a linha `(-) ADICIONAL DE IR TRIMESTRAL` estava calculando incorretamente o adicional de IR. O sistema estava usando um valor base configurável (provavelmente R$ 20.000,00 mensal) em vez do limite trimestral correto de R$ 60.000,00.

### ❌ **Comportamento Anterior:**
- Usava `valor_base_adicional` da configuração da empresa (valor mensal)
- Calculava com base mensal em vez de trimestral
- Não respeitava o limite de R$ 60.000,00 por trimestre

### ✅ **Comportamento Correto:**
- Usa limite fixo de R$ 60.000,00 por trimestre conforme Lei 9.249/1995
- Calcula base trimestral (soma de 3 meses)
- Adicional = max(0, base_trimestral - 60.000) × 10%

## Arquivo Modificado

### `medicos/relatorios/builders.py` - Função `montar_relatorio_mensal_socio`

#### 1. **Correção do Cálculo da Base Trimestral** (linhas 167-240)
```python
# ANTES - Cálculo mensal incorreto
excedente_adicional = max(base_calculo_ir - valor_base_adicional, 0)

# DEPOIS - Cálculo trimestral correto
# Determinar o trimestre atual
trimestre = (competencia.month - 1) // 3 + 1
meses_trimestre = {
    1: [1, 2, 3],    # T1: Jan, Fev, Mar
    2: [4, 5, 6],    # T2: Abr, Mai, Jun  
    3: [7, 8, 9],    # T3: Jul, Ago, Set
    4: [10, 11, 12]  # T4: Out, Nov, Dez
}

# Calcular base trimestral (soma dos 3 meses do trimestre)
for mes in meses_trimestre[trimestre]:
    # ... soma receitas dos 3 meses ...

# Aplicar limite trimestral de R$ 60.000,00
limite_trimestral = 60000.00  # Lei 9.249/1995, Art. 3º, §1º
excedente_adicional_trimestre = max(base_calculo_ir_trimestre - limite_trimestral, 0)
```

#### 2. **Correção do Cálculo do Adicional da Empresa** (linhas 242-244)
```python
# ANTES - Usava alíquota configurável
adicional_ir_trimestral_empresa = excedente_adicional * aliquota_adicional

# DEPOIS - Usa alíquota fixa de 10%
aliquota_adicional_fixa = 0.10  # 10% fixo por lei
adicional_ir_trimestral_empresa = excedente_adicional_trimestre * aliquota_adicional_fixa
```

#### 3. **Correção da Participação do Sócio** (linhas 262-279)
```python
# ANTES - Usava participação mensal
participacao_socio = receita_bruta_socio_emitida / total_notas_bruto_empresa

# DEPOIS - Usa participação trimestral
total_receita_trimestre = total_consultas_trimestre + total_outros_trimestre

# Calcular receita trimestral do sócio
receita_bruta_socio_trimestre = 0
for mes in meses_trimestre[trimestre]:
    # ... soma receitas do sócio nos 3 meses ...

participacao_socio = receita_bruta_socio_trimestre / total_receita_trimestre
```

## Resultado da Correção

### Cenário de Teste:
**Empresa com base trimestral de R$ 80.000,00**

#### ❌ **Antes da Correção:**
```
Base mensal: R$ 26.667,00 (80.000 ÷ 3)
Limite usado: R$ 20.000,00 (mensal configurado)
Excedente: R$ 6.667,00
Adicional incorreto: R$ 6.667,00 × 10% = R$ 666,70 por mês
```

#### ✅ **Após a Correção:**
```
Base trimestral: R$ 80.000,00
Limite correto: R$ 60.000,00 (trimestral fixo)
Excedente: R$ 20.000,00
Adicional correto: R$ 20.000,00 × 10% = R$ 2.000,00 no trimestre
```

### Comportamento no Relatório do Sócio:
- **Meses 1, 2, 4, 5, 7, 8, 10, 11**: Adicional = R$ 0,00
- **Meses 3, 6, 9, 12**: Adicional = Valor proporcional do trimestre

## Validação

### ✅ **Regras Atendidas:**
1. **Base Legal**: Lei 9.249/1995, Art. 3º, §1º - limite de R$ 60.000,00 por trimestre
2. **Periodicidade**: Adicional calculado apenas trimestralmente
3. **Alíquota**: 10% fixo sobre o excedente
4. **Rateio**: Proporcional à participação do sócio na receita trimestral
5. **Exibição**: Apenas nos meses de fechamento (3, 6, 9, 12)

### 📊 **Template Já Correto:**
O template `relatorio_mensal_socio.html` já exibia "(-) ADICIONAL DE IR TRIMESTRAL", apenas o cálculo no builder estava incorreto.

## Arquivos de Teste
- `teste_adicional_ir_socio.py` - Script para validar a correção

## Impacto
- **Conformidade Legal**: Sistema agora calcula conforme legislação
- **Precisão**: Valores corretos para os sócios
- **Consistência**: Alinhado com o cálculo da tela de Apuração

---
**Data da correção**: 09/09/2025  
**Arquivo modificado**: `medicos/relatorios/builders.py`  
**Linhas alteradas**: ~70 linhas  
**Status**: ✅ Concluído
