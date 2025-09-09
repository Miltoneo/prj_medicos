# CORREÇÃO APLICADA: ADICIONAL DE IR TRIMESTRAL

## Problema Identificado
A linha `(+) Adicional de IR (base >60000,00)` na tabela "Apuração Trimestral - IRPJ" estava calculando incorretamente o adicional de IR. O problema era que o sistema estava somando os adicionais mensais (baseados no limite de R$ 20.000,00 por mês) em vez de calcular o adicional com base na soma trimestral contra o limite trimestral de R$ 60.000,00.

## Causa Raiz
No arquivo `medicos/views_relatorios.py`, linhas 839-850, o cálculo dos totais trimestrais estava simplesmente somando os valores mensais para todos os campos, incluindo o `adicional_ir`. 

**Código problemático:**
```python
for key in totais_trimestrais.keys():
    total_trim = sum(dados_irpj_trimestral[key][inicio_idx:fim_idx])
    totais_trimestrais[key].append(total_trim)
```

Isso resultava em:
- **Erro**: Adicional trimestral = soma(adicional_jan + adicional_fev + adicional_mar)
- **Correto**: Adicional trimestral = max(0, (base_total_trimestral - 60000)) × 10%

## Solução Implementada

### 1. Correção do Cálculo do Adicional (linhas 839-863)
```python
for key in totais_trimestrais.keys():
    if key == 'adicional_ir':
        # CORREÇÃO: Adicional de IR deve ser recalculado com base trimestral
        # Não pode ser soma dos mensais pois o limite é trimestral (R$ 60.000,00)
        base_calculo_total_trim = sum(dados_irpj_trimestral['base_calculo_total'][inicio_idx:fim_idx])
        limite_trimestral = Decimal('60000.00')  # R$ 60.000,00/trimestre
        excedente_trim = max(Decimal('0'), base_calculo_total_trim - limite_trimestral)
        adicional_trim = excedente_trim * Decimal('0.10')  # 10%
        totais_trimestrais[key].append(adicional_trim)
```

### 2. Correção do Total Imposto Devido (linhas 844-849)
```python
elif key == 'total_imposto_devido':
    # CORREÇÃO: Total imposto devido deve ser recalculado considerando o adicional correto
    imposto_devido_15_trim = sum(dados_irpj_trimestral['imposto_devido_15'][inicio_idx:fim_idx])
    # Obter o adicional recalculado (último valor adicionado)
    adicional_recalculado = totais_trimestrais['adicional_ir'][-1] if totais_trimestrais['adicional_ir'] else Decimal('0')
    total_imposto_trim = imposto_devido_15_trim + adicional_recalculado
    totais_trimestrais[key].append(total_imposto_trim)
```

### 3. Correção do Imposto a Pagar (linhas 850-856)
```python
elif key == 'imposto_a_pagar':
    # CORREÇÃO: Imposto a pagar deve ser recalculado considerando o total correto
    total_imposto_recalculado = totais_trimestrais['total_imposto_devido'][-1] if totais_trimestrais['total_imposto_devido'] else Decimal('0')
    imposto_retido_trim = sum(dados_irpj_trimestral['imposto_retido_nf'][inicio_idx:fim_idx])
    retencao_aplicacao_trim = sum(dados_irpj_trimestral['retencao_aplicacao'][inicio_idx:fim_idx])
    imposto_a_pagar_trim = total_imposto_recalculado - imposto_retido_trim - retencao_aplicacao_trim
    totais_trimestrais[key].append(imposto_a_pagar_trim)
```

## Resultado Esperado

### Antes da Correção:
- T1: Base = R$ 50.000 → Adicional = R$ 500 (jan) + R$ 800 (fev) + R$ 200 (mar) = R$ 1.500 ❌

### Após a Correção:
- T1: Base = R$ 50.000 → Adicional = max(0, 50000 - 60000) × 10% = R$ 0,00 ✅
- T2: Base = R$ 80.000 → Adicional = max(0, 80000 - 60000) × 10% = R$ 2.000,00 ✅

## Arquivos Modificados
- `medicos/views_relatorios.py` - Linhas 839-863

## Base Legal
Lei 9.249/1995, Art. 3º, §1º - O adicional de IR de 10% incide sobre a parcela do lucro presumido trimestral que exceder R$ 60.000,00.

## Teste
Script de teste criado: `teste_adicional_ir_trimestral.py`

---
**Data da correção**: 09/09/2025  
**Fonte**: medicos/views_relatorios.py, linhas 839-863
