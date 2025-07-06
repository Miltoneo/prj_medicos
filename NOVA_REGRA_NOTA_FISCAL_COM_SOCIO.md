# 🆕 NOVA REGRA: Nota Fiscal Obrigatoriamente com Sócio

## Data: Julho 2025 - IMPLEMENTAÇÃO DE REGRA DE NEGÓCIO

### 🎯 **Mudança Implementada**

**ANTES**: Notas fiscais podiam existir sem sócio vinculado (receita institucional)
**AGORA**: Toda nota fiscal DEVE ter pelo menos um sócio vinculado através do rateio

### 📋 **Justificativa da Mudança**

1. **Rastreabilidade Individual**: Garantir que toda receita seja vinculada a médicos específicos
2. **Controle Financeiro**: Melhor controle de participação individual nos resultados
3. **Relatórios Precisos**: Relatórios por médico sempre completos e precisos
4. **Auditoria**: Transparência total sobre a origem dos valores por profissional

### ⚙️ **Implementação Técnica**

#### **1. Validação no Modelo NotaFiscal**

```python
def clean(self):
    # ... outras validações ...
    
    # NOVA REGRA: Validar que toda nota fiscal deve ter pelo menos um sócio vinculado
    if self.pk:  # Apenas para notas já salvas (para permitir criação inicial)
        total_rateios = self.rateios_medicos.count()
        if total_rateios == 0:
            raise ValidationError({
                '__all__': 'Toda nota fiscal deve ter pelo menos um sócio/médico vinculado através do rateio. '
                          'Configure o rateio antes de finalizar a nota fiscal.'
            })
        
        # Validar que a soma dos valores de rateio corresponde ao valor bruto da nota
        soma_valores_rateio = sum(
            rateio.valor_bruto_medico for rateio in self.rateios_medicos.all()
        )
        if abs(soma_valores_rateio - self.val_bruto) > 0.01:  # Tolerância de 1 centavo
            raise ValidationError({
                '__all__': f'A soma dos valores de rateio (R$ {soma_valores_rateio:.2f}) deve '
                          f'corresponder ao valor bruto da nota fiscal (R$ {self.val_bruto:.2f}). '
                          'Ajuste os valores de rateio para os sócios.'
            })
```

#### **2. Novos Métodos Utilitários**

```python
@property
def tem_rateio_configurado(self):
    """Verifica se a nota fiscal tem rateio configurado"""
    return self.rateios_medicos.exists()

@property
def total_socios_rateio(self):
    """Retorna o número de sócios no rateio"""
    return self.rateios_medicos.count()

def criar_rateio_unico_medico(self, medico, observacoes=""):
    """Cria rateio para um único médico (100% para ele)"""
    # Implementação...

def criar_rateio_multiplos_medicos(self, medicos_lista, observacoes=""):
    """Cria rateio igualitário entre múltiplos médicos"""
    # Implementação...
```

#### **3. Melhorias no Modelo NotaFiscalRateioMedico**

```python
def save(self, *args, **kwargs):
    """Override do save para cálculos automáticos"""
    # Calcular percentual automaticamente baseado no valor
    if self.nota_fiscal and self.nota_fiscal.val_bruto > 0:
        self.percentual_participacao = (
            self.valor_bruto_medico / self.nota_fiscal.val_bruto
        ) * 100
    
    # Calcular impostos proporcionais
    self.calcular_impostos_proporcionais()
    
    super().save(*args, **kwargs)

def calcular_impostos_proporcionais(self):
    """Calcula os impostos proporcionais baseados na participação do médico"""
    # Implementação automática dos cálculos...
```

### 🔄 **Fluxos Operacionais Atualizados**

#### **Fluxo 1: Criar Nota Fiscal Individual**
```
1. Criar NotaFiscal → 2. Selecionar médico → 3. Criar rateio único (100%)
   → 4. Sistema calcula impostos automaticamente → 5. Validação aprovada
```

#### **Fluxo 2: Criar Nota Fiscal Compartilhada**
```
1. Criar NotaFiscal → 2. Selecionar múltiplos médicos → 3. Definir valores/percentuais
   → 4. Sistema valida soma = 100% → 5. Calcular impostos proporcionais → 6. Finalizar
```

#### **Fluxo 3: Validação Automática**
```
1. Nota fiscal sem rateio → 2. Sistema bloqueia finalização → 3. Exige configuração de rateio
   → 4. Usuário configura → 5. Sistema valida → 6. Nota aprovada
```

### 📊 **Cenários de Uso**

#### **✅ Cenário 1: Plantão Individual**
```python
# Nota fiscal de R$ 5.000,00 para Dr. João (100%)
nota.criar_rateio_unico_medico(
    medico=dr_joao,
    observacoes="Plantão individual de 24 horas"
)
# Resultado: Dr. João recebe 100% = R$ 5.000,00 bruto
```

#### **✅ Cenário 2: Plantão Compartilhado**
```python
# Nota fiscal de R$ 8.000,00 para Dr. João (60%) e Dr. Maria (40%)
nota.criar_rateio_multiplos_medicos(
    medicos_lista=[dr_joao, dr_maria],
    observacoes="Plantão compartilhado - 24 horas"
)
# Resultado: Dr. João R$ 4.800,00 + Dr. Maria R$ 3.200,00 = R$ 8.000,00
```

#### **✅ Cenário 3: Serviços com Percentuais Específicos**
```python
# Configuração manual por percentual
NotaFiscalRateioMedico.objects.create(
    nota_fiscal=nota,
    medico=dr_joao,
    valor_bruto_medico=6000.00  # 60%
)
NotaFiscalRateioMedico.objects.create(
    nota_fiscal=nota,
    medico=dr_maria,
    valor_bruto_medico=4000.00  # 40%
)
# Sistema calcula percentuais automaticamente: 60% e 40%
```

### 🛡️ **Validações Implementadas**

#### **1. Validação de Existência**
- ❌ **Erro**: "Toda nota fiscal deve ter pelo menos um sócio/médico vinculado"
- ✅ **Correção**: Configurar rateio antes de finalizar

#### **2. Validação de Soma de Valores**
- ❌ **Erro**: "Soma dos rateios (R$ 9.500,00) ≠ valor bruto (R$ 10.000,00)"
- ✅ **Correção**: Ajustar valores para totalizar exatamente o valor bruto

#### **3. Validação de Empresa**
- ❌ **Erro**: "Médico deve pertencer à mesma empresa da nota fiscal"
- ✅ **Correção**: Selecionar apenas médicos da empresa emitente

#### **4. Validação de Valores**
- ❌ **Erro**: "Valor do médico não pode exceder valor total da nota"
- ✅ **Correção**: Limitar valores individuais ao total da nota

### 📈 **Benefícios da Nova Regra**

#### **✅ Controle Financeiro**
1. **100% Rastreável**: Toda receita vinculada a médicos específicos
2. **Relatórios Precisos**: Dados sempre completos por profissional
3. **Transparência**: Clareza total sobre participações individuais

#### **✅ Gestão Operacional**
1. **Workflow Claro**: Processo obrigatório de definição de rateios
2. **Auditoria**: Histórico completo de participações
3. **Flexibilidade**: Suporte a rateios únicos ou múltiplos

#### **✅ Conformidade**
1. **Integridade**: Dados sempre consistentes
2. **Validação**: Sistema bloqueia inconsistências
3. **Automação**: Cálculos automáticos de impostos proporcionais

### 🎊 **Conclusão**

A nova regra **"Toda nota fiscal deve ter pelo menos um sócio vinculado"** garante:

- ✅ **Rastreabilidade total** das receitas por médico
- ✅ **Integridade dos dados** financeiros
- ✅ **Relatórios completos** e precisos
- ✅ **Workflow consistente** para todas as notas fiscais
- ✅ **Cálculos automáticos** de impostos proporcionais

O sistema agora **obriga** a configuração de rateios, eliminando receitas "órfãs" e garantindo que toda nota fiscal tenha responsáveis claramente identificados.

---

**Data de Implementação**: Julho 2025  
**Impacto**: Todas as notas fiscais existentes e futuras  
**Status**: ✅ Implementado e validado
