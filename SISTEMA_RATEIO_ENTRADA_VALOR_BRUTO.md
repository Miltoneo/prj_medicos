# Sistema de Rateio de Notas Fiscais - Entrada por Valor Bruto

## Resumo

O sistema de rateio de notas fiscais foi implementado e configurado para funcionar da seguinte forma:

**REGRA PRINCIPAL**: O valor bruto é a entrada, o percentual é calculado automaticamente.

## Lógica de Funcionamento

### Modelo NotaFiscalRateioMedico

#### Campos de Entrada vs. Campos Calculados

1. **Campo de ENTRADA**:
   - `valor_bruto_medico`: Valor em reais que cada médico deve receber da nota fiscal
   - Este é o campo que o usuário/contabilidade informa

2. **Campo CALCULADO AUTOMATICAMENTE**:
   - `percentual_participacao`: Percentual calculado automaticamente baseado no valor_bruto_medico
   - Fórmula: `(valor_bruto_medico / nota_fiscal.val_bruto) * 100`
   - Usado para relatórios e visualizações

### Fluxo de Funcionamento

```
1. Usuário informa valor_bruto_medico (ex: R$ 1.500,00)
2. Sistema calcula percentual_participacao automaticamente 
   (ex: 1500/3000 * 100 = 50%)
3. Sistema calcula impostos proporcionais baseado no percentual
4. Sistema calcula valor_liquido_medico
```

### Métodos de Criação de Rateio

#### 1. Rateio Automático Igualitário
```python
NotaFiscalRateioMedico.criar_rateio_automatico(nota_fiscal, [medico1, medico2], usuario)
# Divide o valor total igualmente entre os médicos
```

#### 2. Rateio por Valores Específicos
```python
rateios_config = [
    {'medico': medico1, 'valor': 1800.00},
    {'medico': medico2, 'valor': 1200.00},
]
NotaFiscalRateioMedico.criar_rateio_por_valores(nota_fiscal, rateios_config, usuario)
```

#### 3. Rateio por Percentuais (convertido para valores)
```python
rateios_config = [
    {'medico': medico1, 'percentual': 60},  # Será convertido para valor
    {'medico': medico2, 'percentual': 40},  # Será convertido para valor
]
NotaFiscalRateioMedico.criar_rateio_por_percentuais(nota_fiscal, rateios_config, usuario)
```

## Implementação Técnica

### Método save() Atualizado

```python
def save(self, *args, **kwargs):
    # REGRA PRINCIPAL: O valor_bruto_medico é a entrada, percentual_participacao é calculado
    if self.nota_fiscal and self.nota_fiscal.val_bruto > 0:
        self.percentual_participacao = (self.valor_bruto_medico / self.nota_fiscal.val_bruto) * 100
    
    # Recalcular impostos proporcionais
    self.calcular_impostos_proporcionais()
    
    # Validar e salvar
    self.full_clean()
    super().save(*args, **kwargs)
    self.validar_total_rateios()
```

### Validações Implementadas

1. **Valor não pode ser negativo**
2. **Valor do médico não pode exceder valor total da nota fiscal**
3. **Total dos valores de todos os médicos não pode exceder valor da nota fiscal**
4. **Médico deve pertencer à mesma empresa da nota fiscal**
5. **Percentual é sempre recalculado automaticamente** (sem validação manual)

### Interface de Entrada

Para implementar a interface/forms:

```python
class NotaFiscalRateioMedicoForm(forms.ModelForm):
    class Meta:
        model = NotaFiscalRateioMedico
        fields = ['medico', 'valor_bruto_medico', 'observacoes_rateio']
        # Não incluir percentual_participacao pois é calculado automaticamente
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_bruto_medico'].help_text = "Informe o valor em reais que este médico deve receber"
        # percentual_participacao será exibido como readonly/calculado
```

## Casos de Uso

### Caso 1: Nota Fiscal de R$ 3.000,00 para 2 médicos

**Entrada**:
- Médico A: R$ 1.800,00
- Médico B: R$ 1.200,00

**Resultado Automático**:
- Médico A: 60% (calculado)
- Médico B: 40% (calculado)

### Caso 2: Divisão Igualitária

**Entrada**: Nota de R$ 5.000,00 para 3 médicos
**Resultado**:
- Cada médico: R$ 1.666,67 (33,33%)

### Caso 3: Um médico recebe tudo

**Entrada**: R$ 2.500,00 para 1 médico
**Resultado**: 100% para o médico

## Vantagens desta Abordagem

1. **Simplicidade**: Usuário informa valores em reais (mais intuitivo)
2. **Flexibilidade**: Pode usar qualquer combinação de valores
3. **Automatização**: Percentuais sempre corretos para relatórios
4. **Consistência**: Não há discrepância entre valor e percentual
5. **Auditoria**: Campo de entrada é claro (valor bruto)

## Relatórios

Os relatórios podem usar tanto os valores quanto os percentuais:

- **Para controle financeiro**: usar `valor_bruto_medico`, `valor_liquido_medico`
- **Para análise de participação**: usar `percentual_participacao`
- **Para gráficos e dashboards**: usar `percentual_participacao`

## Integração com Sistema Financeiro

O rateio integra automaticamente com:

1. **Cálculo de impostos proporcionais** por médico
2. **Módulo financeiro** para controle de recebimentos
3. **Relatórios consolidados** mensais
4. **Auditoria** de configurações de rateio

## Próximos Passos

1. ✅ Modelo Django implementado e validado
2. ✅ Revisão completa do modelo fiscal.py
3. ✅ Garantia de que percentual_participacao é sempre calculado automaticamente
4. ✅ Implementação da regra: valor_bruto_medico é entrada, percentual é calculado
5. ✅ Atualização do diagrama ER completo e final
6. ⏳ Atualizar forms/interface para entrada por valor bruto
7. ⏳ Atualizar admin/interface para mostrar percentual como readonly
8. ⏳ Testar integração com módulo financeiro
9. ⏳ Implementar relatórios de rateio
10. ⏳ Criar testes automatizados

---

**Data**: Julho 2025  
**Status**: ✅ Modelo implementado, validado e revisado completamente  
**Diagrama ER**: ✅ Atualizado em DIAGRAMA_ER_FINAL_COMPLETO.md  
**Próxima etapa**: Interface de usuário
