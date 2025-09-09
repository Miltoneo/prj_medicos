# REMOÇÃO DO ADICIONAL DE IR MENSAL

## Problema Identificado
O sistema calculava adicional de IR tanto mensalmente (R$ 20.000,00/mês) quanto trimestralmente (R$ 60.000,00/trimestre), causando inconsistências e cálculos duplos. Conforme a Lei 9.249/1995, Art. 3º, §1º, o adicional de IR deve ser calculado apenas **trimestralmente** com base no limite de R$ 60.000,00 por trimestre.

## Arquivos Modificados

### 1. `medicos/views_relatorios.py`

#### Remoções Realizadas:
- **Função removida**: `calcular_adicional_ir_mensal(empresa_id, ano)` (linhas 457-507)
- **Seção removida**: "Espelho do Adicional de IR Mensal" com `dados_adicional_mensal` e `linhas_espelho_adicional_mensal` (linhas 589-601)
- **Seção removida**: "Espelho do Adicional de IR Mensal (baseado nos dados da tabela IRPJ Mensal)" com `espelho_adicional_mensal` (linhas 642-685)
- **Contexto removido**: 
  - `'linhas_espelho_adicional_mensal': linhas_espelho_adicional_mensal,`
  - `'espelho_adicional_mensal': espelho_adicional_mensal,`

#### Justificativa:
O adicional de IR mensal criava confusão e cálculos incorretos. A lei estabelece apenas o cálculo trimestral.

### 2. `medicos/relatorios/apuracao_irpj_mensal.py`

#### Modificação Realizada:
```python
# ANTES - Cálculo complexo do adicional mensal (linhas 121-143)
adicional = Decimal('0')
limite_mensal_legal = Decimal('20000.00')
# ... cálculos complexos ...
if lucro_presumido_mensal > limite_mensal_legal:
    excesso_lucro_presumido = lucro_presumido_mensal - limite_mensal_legal
    adicional = excesso_lucro_presumido * (Decimal('10.00') / Decimal('100'))

# DEPOIS - Adicional sempre zero no mensal
adicional = Decimal('0')  # Sempre zero para relatórios mensais
```

#### Justificativa:
O builder mensal agora sempre retorna adicional = 0, pois o adicional só deve ser calculado trimestralmente.

### 3. `medicos/templates/relatorios/apuracao_de_impostos.html`

#### Modificação Realizada:
- **Removido**: Filtro condicional que destacava linhas do adicional mensal (linhas 400-410)
- **Simplificado**: Loop das linhas do IRPJ mensal sem tratamento especial para adicional

```django-html
<!-- ANTES - Com filtro especial para adicional -->
{% if linha.descricao == 'Valor base para adicional' or ... or linha.descricao == 'Total Adicional de IR' %}
  <tr>
    <td class="fw-medium fst-italic">{{ linha.descricao }}</td>
    <!-- ... -->
  </tr>
{% else %}
  <tr>
    <td class="fw-medium">{{ linha.descricao }}</td>
    <!-- ... -->
  </tr>
{% endif %}

<!-- DEPOIS - Tratamento uniforme -->
<tr>
  <td class="fw-medium">{{ linha.descricao }}</td>
  <!-- ... -->
</tr>
```

## Resultado Esperado

### Antes da Remoção:
- ❌ Adicional calculado mensalmente (R$ 20.000,00/mês)
- ❌ Adicional calculado trimestralmente (R$ 60.000,00/trimestre)
- ❌ Possível duplicação ou inconsistência de valores
- ❌ Espelhos mensais de adicional desnecessários

### Após a Remoção:
- ✅ Adicional calculado **APENAS** trimestralmente (R$ 60.000,00/trimestre)
- ✅ Relatórios mensais mostram adicional = R$ 0,00
- ✅ Cálculo correto conforme Lei 9.249/1995, Art. 3º, §1º
- ✅ Interface simplificada sem espelhos mensais

## Validação

### Tabelas Afetadas:
1. **IRPJ Mensal**: Agora mostra adicional = R$ 0,00 para todos os meses
2. **IRPJ Trimestral**: Mantém o cálculo correto do adicional trimestral
3. **Espelho Adicional Trimestral**: Continua funcionando normalmente

### Base Legal Atendida:
- Lei 9.249/1995, Art. 3º, §1º: "Sobre a parcela do lucro que exceder o valor de R$ 60.000,00 (sessenta mil reais), **por trimestre**, incidirá adicional de imposto à alíquota de 10% (dez por cento)."

## Benefícios da Remoção

1. **Conformidade Legal**: Sistema agora segue corretamente a legislação
2. **Simplicidade**: Menos código e menor complexidade
3. **Consistência**: Único ponto de cálculo do adicional (trimestral)
4. **Performance**: Menos consultas e cálculos desnecessários
5. **Manutenibilidade**: Código mais limpo e fácil de entender

---
**Data da remoção**: 09/09/2025  
**Arquivos modificados**: 3 arquivos  
**Linhas removidas**: ~75 linhas de código  
**Status**: ✅ Concluído
