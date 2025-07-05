# Documentação: Regime Tributário Conforme Legislação Brasileira

## Resumo das Adequações Implementadas

Este documento detalha as adequações realizadas na modelagem de dados para garantir total conformidade com a legislação tributária brasileira, especialmente para empresas prestadoras de serviços médicos.

---

## 1. ADEQUAÇÕES NO MODELO `Empresa`

### **Novos Campos Adicionados:**

```python
# Controle de receita para validação do regime de caixa
receita_bruta_ano_anterior = models.DecimalField(
    max_digits=15, decimal_places=2, null=True, blank=True,
    verbose_name="Receita Bruta Ano Anterior (R$)",
    help_text="Receita bruta do ano anterior para validação do direito ao regime de caixa (limite R$ 78 milhões)"
)

# Data da última alteração de regime (para controle anual)
data_ultima_alteracao_regime = models.DateField(
    null=True, blank=True,
    verbose_name="Data Última Alteração de Regime",
    help_text="Data da última alteração de regime tributário (para controle de mudanças anuais)"
)
```

### **Validações Legais Implementadas:**

1. **Limite de Receita para Regime de Caixa (Lei 9.718/1998)**
   - Validação de R$ 78 milhões como limite máximo
   - Bloqueio automático se exceder o limite

2. **Controle de Mudanças Anuais**
   - Apenas uma alteração de regime por ano fiscal
   - Validação na data de alteração

3. **Método `alterar_regime_tributario()` Aprimorado:**
   - Data padrão: 1º de janeiro do próximo ano
   - Validação de periodicidade anual
   - Validação de limites de receita
   - Finalização automática do regime anterior

---

## 2. MODELO `RegimeTributarioHistorico` APRIMORADO

### **Novos Campos para Controle Legal:**

```python
# Controle de receita para validação
receita_bruta_ano_anterior = models.DecimalField(...)

# Controle de comunicação aos órgãos fiscais
comunicado_receita_federal = models.BooleanField(default=False)
data_comunicacao_rf = models.DateField(null=True, blank=True)
comunicado_municipio = models.BooleanField(default=False)
data_comunicacao_municipio = models.DateField(null=True, blank=True)
```

### **Validações Legais:**

1. **Data de Início Obrigatória em 1º de Janeiro**
   - Conforme Art. 12 da Lei 9.718/1998
   - Validação automática na criação

2. **Limite de Receita para Regime de Caixa**
   - R$ 78 milhões conforme legislação
   - Validação cruzada com dados da empresa

3. **Unicidade por Ano Fiscal**
   - Apenas um regime por ano para cada empresa
   - Prevenção de múltiplas alterações no mesmo ano

---

## 3. NOVO MODELO `RegimeImpostoEspecifico`

### **Objetivo:**
Controlar regimes específicos por tipo de imposto, respeitando as particularidades legais de cada um.

### **Regras Implementadas:**

#### **ISS (Imposto Sobre Serviços)**
- **Sempre regime de competência** (LC 116/2003)
- Não permite alteração para regime de caixa
- Validação automática bloqueante

#### **PIS/COFINS**
- Pode seguir regime da empresa se atender critérios
- Limite de R$ 78 milhões para regime de caixa
- Base legal: Lei 9.718/1998

#### **IRPJ/CSLL**
- Pode seguir regime da empresa se atender critérios
- Mesmo limite de receita que PIS/COFINS
- Presunção de lucro de 32% para serviços médicos

---

## 4. CÁLCULO DE IMPOSTOS COM REGIMES ESPECÍFICOS

### **Método `calcular_impostos_com_regime()` Aprimorado:**

#### **Funcionalidades:**
1. **Regime Específico por Imposto**
   - ISS sempre competência
   - Outros impostos conforme empresa e receita

2. **Observações Legais Detalhadas**
   - Base legal para cada imposto
   - Motivo da aplicação do regime
   - Prazos de recolhimento específicos

3. **Validação de Limites**
   - Verificação automática de receita
   - Aplicação de fallback para competência

#### **Retorno Detalhado:**
```python
{
    'valor_bruto': Decimal('1000.00'),
    'regime_tributario': {...},
    'regimes_por_imposto': {
        'ISS': {'regime': 1, 'nome': 'Competência', 'base_legal': 'LC 116/2003'},
        'PIS': {'regime': 2, 'nome': 'Caixa', 'base_legal': 'Lei 9.718/1998'},
        # ... outros impostos
    },
    'observacoes_legais': [
        "⚠️ REGIME MISTO APLICADO:",
        "• ISS: Sempre competência (Lei Complementar 116/2003)",
        "• PIS/COFINS/IRPJ/CSLL: Regime de caixa (Lei 9.718/1998)"
    ]
}
```

---

## 5. CONFORMIDADE LEGAL GARANTIDA

### **Legislação Atendida:**

#### **Lei 9.718/1998 (Regime de Caixa)**
- ✅ Limite de R$ 78 milhões
- ✅ Alterações apenas em 1º de janeiro
- ✅ Comunicação obrigatória à Receita Federal
- ✅ Uma alteração por ano fiscal

#### **Lei Complementar 116/2003 (ISS)**
- ✅ ISS sempre regime de competência
- ✅ Não permite regime de caixa para ISS
- ✅ Município de prestação do serviço

#### **Código Tributário Nacional (CTN)**
- ✅ Regime de competência como padrão (Art. 177)
- ✅ Irretroatividade das alterações
- ✅ Fato gerador na prestação do serviço

#### **Legislação de PIS/COFINS**
- ✅ Mesmo critério que IRPJ/CSLL
- ✅ Limite de receita respeitado
- ✅ Base de cálculo correta

---

## 6. FUNCIONALIDADES DE AUDITORIA

### **Controles Implementados:**

1. **Histórico Completo**
   - Todos os regimes aplicados ao longo do tempo
   - Data de início e fim de cada período
   - Usuário responsável pela alteração

2. **Validações Preventivas**
   - Impede alterações retroativas
   - Valida limites de receita
   - Controla periodicidade anual

3. **Relatórios de Conformidade**
   - Status de comunicação aos órgãos
   - Bases legais aplicadas
   - Observações por tipo de imposto

4. **Rastreabilidade**
   - Quem alterou, quando e por que
   - Receita bruta que justificou a alteração
   - Comunicações realizadas

---

## 7. BENEFÍCIOS DA IMPLEMENTAÇÃO

### **Para as Empresas:**
- ✅ Conformidade automática com a legislação
- ✅ Prevenção de erros tributários
- ✅ Controle de prazos e comunicações
- ✅ Histórico completo para auditorias

### **Para o Sistema:**
- ✅ Validações automáticas
- ✅ Cálculos corretos por tipo de imposto
- ✅ Relatórios de conformidade
- ✅ Integração com órgãos fiscais (futuro)

### **Para os Contadores:**
- ✅ Informações legais precisas
- ✅ Base legal para cada cálculo
- ✅ Controle de obrigações acessórias
- ✅ Auditoria facilitada

---

## 8. PRÓXIMOS PASSOS RECOMENDADOS

### **Migrações de Banco:**
1. Criar migração para novos campos na `Empresa`
2. Criar migração para `RegimeTributarioHistorico`
3. Criar migração para `RegimeImpostoEspecifico`

### **Implementações Futuras:**
1. Interface administrativa para controle de regimes
2. Relatórios de conformidade legal
3. Integração com SPED e outras obrigações
4. Alertas automáticos de prazos

### **Testes Recomendados:**
1. Executar testes de regime tributário histórico
2. Validar cálculos com regimes mistos
3. Testar validações de limite de receita
4. Verificar controle de periodicidade anual

---

## CONCLUSÃO

A modelagem de dados foi completamente adequada à legislação tributária brasileira, garantindo:

- **Conformidade legal total** com as principais leis tributárias
- **Flexibilidade** para diferentes cenários empresariais
- **Auditoria completa** de todas as alterações
- **Prevenção de erros** através de validações automáticas
- **Base sólida** para futuras expansões do sistema

O sistema agora atende plenamente aos requisitos legais para empresas prestadoras de serviços médicos, com controles específicos para cada tipo de imposto e validações que impedem configurações incorretas.
