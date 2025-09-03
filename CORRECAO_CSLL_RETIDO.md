# Correção da Diferença de CSLL Retido Entre Tabelas

## Problema Identificado
Havia uma diferença nos valores de **imposto retido CSLL** entre:
- **Tabela "CSLL - Trimestres"**: Usava valor real do campo `val_CSLL` das notas fiscais
- **Tabela "Apuração Trimestral - CSLL"**: Usava proporção calculada a partir do IRPJ retido

## Causa Raiz
As duas tabelas usavam métodos diferentes para calcular o CSLL retido:

### Antes (Inconsistente):
```python
# Tabela "CSLL - Trimestres" (apuracao_csll.py)
imposto_retido_nf = notas_recebidas.aggregate(total=Sum('val_CSLL'))['total']

# Tabela "Apuração Trimestral - CSLL" (views_relatorios.py)
imposto_retido_nf_irpj = linha_mes.get('imposto_retido_nf', 0)
proporcao_csll = csll_aliquota / irpj_aliquota  # Proporção estimada
imposto_retido_nf_csll = imposto_retido_nf_irpj * proporcao_csll  # ❌ ESTIMATIVA
```

### Depois (Consistente):
```python
# Ambas as tabelas agora usam o mesmo método
# Buscar CSLL retido real das notas fiscais por data de recebimento
notas_recebidas_mes = NotaFiscal.objects.filter(
    empresa_destinataria_id=empresa_id,
    dtRecebimento__year=ano,
    dtRecebimento__month=mes,
    dtRecebimento__isnull=False
)
imposto_retido_nf_csll = notas_recebidas_mes.aggregate(
    total=Sum('val_CSLL')
)['total'] or Decimal('0')  # ✅ VALOR REAL
```

## Correção Implementada

### Arquivo: `medicos/views_relatorios.py`
**Linha modificada**: ~880-890

**Antes**:
- Calculava proporção entre CSLL e IRPJ
- Aplicava proporção ao IRPJ retido para estimar CSLL retido
- Resultado: valores inconsistentes entre tabelas

**Depois**:
- Busca diretamente o valor real do campo `val_CSLL` das notas fiscais
- Usa a mesma lógica da tabela "CSLL - Trimestres"
- Critério: sempre por data de recebimento (independente do regime tributário)

## Vantagens da Correção

✅ **Consistência**: Ambas as tabelas mostram os mesmos valores
✅ **Precisão**: Usa valores reais das notas, não estimativas
✅ **Confiabilidade**: Elimina discrepâncias nos relatórios fiscais
✅ **Compliance**: Mantém conformidade com regras de retenção na fonte

## Impacto

- **Tabela "CSLL - Trimestres"**: Sem alteração (já estava correta)
- **Tabela "Apuração Trimestral - CSLL"**: Agora mostra valores reais de CSLL retido
- **Relatórios**: Maior confiabilidade e consistência entre diferentes visões dos dados
- **Auditoria**: Facilita reconciliação entre relatórios mensais e trimestrais

## Validação

Para validar a correção:
1. Execute ambos os relatórios para o mesmo período
2. Compare os valores de "Imposto retido NF" entre as tabelas
3. Os valores devem ser idênticos para os mesmos períodos

**Fonte**: Correção baseada em `medicos/relatorios/apuracao_csll.py`, linha 65; implementada em `medicos/views_relatorios.py`, conforme `.github/copilot-instructions.md`, seção 3.
