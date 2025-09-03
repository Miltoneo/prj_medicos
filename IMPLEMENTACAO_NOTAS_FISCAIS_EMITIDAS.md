# Implementação da Tabela "Notas Fiscais Emitidas"

## 📊 **Estrutura Implementada**

### **1. 🎯 Layout Conforme Anexo**

**Template:** [`medicos/templates/relatorios/apuracao_de_impostos.html`](medicos/templates/relatorios/apuracao_de_impostos.html)

**Estrutura da tabela:**
```
|Descrição                           | T1        | T2        | T3        | T4        |
|                                    |1 |2 |3   |4 |5 |6   |7 |8 |9   |10|11|12 |
|(+) Total Receita consultas/Plantão |0.00|0.00|0.00|0.00|0.00|0.00|...|
|(+) Total Receita outros            |0.00|0.00|0.00|0.00|0.00|0.00|...|
|(=) Total receita bruta             |    0.00   |    0.00   |    0.00   |    0.00   |
```

### **2. 🧮 Lógica de Cálculo**

**View:** [`medicos/views_relatorios.py`](medicos/views_relatorios.py)

**Função implementada:**
```python
def calcular_notas_fiscais_emitidas():
    notas_emitidas = {
        'receita_consultas': [],      # 12 valores mensais
        'receita_outros': [],         # 12 valores mensais  
        'receita_bruta_mensal': [],   # 12 valores mensais
        'receita_bruta_trimestral': [] # 4 valores trimestrais
    }
```

**Fonte dos dados:**
- **Notas fiscais emitidas**: `NotaFiscal.objects.filter(empresa_destinataria_id, dtEmissao__year, dtEmissao__month)`
- **Critério temporal**: Por `dtEmissao` (data de emissão)
- **Separação por tipo**: `tipo_servico=TIPO_SERVICO_CONSULTAS` vs outros

### **3. 🎨 Design Visual**

**Características:**
- **Cor tema**: Azul primário (`table-primary`, `bg-primary`, `border-primary`)
- **Ícone**: `bi-file-earmark-text` (documento/nota fiscal)
- **Header duplo**: Trimestres (T1-T4) + meses (1-12)
- **Linha total**: Receita bruta com colspan=3 por trimestre e destaque

### **4. 📋 Conformidade com Anexo**

**Elementos implementados:**
✅ **3 linhas de dados**: Receita consultas, Receita outros, Total receita bruta
✅ **Header duplo**: Trimestres no topo, meses na segunda linha
✅ **Merge trimestral**: Linha "Total receita bruta" com colspan=3 por trimestre
✅ **12 colunas mensais**: Janeiro a dezembro numerados
✅ **Valores decimais**: Formatação com 2 casas decimais

### **5. 🔗 Posicionamento**

**Ordem das seções:**
1. ✅ **Notas Fiscais Emitidas** (nova)
2. ✅ **Impostos Retidos na Nota Fiscal** (existente)
3. ✅ **Apuração PIS** (existente)
4. ✅ Demais seções...

### **6. 📊 Funcionalidade de Negócio**

**Utilidade da tabela:**
- ✅ **Receitas mensais**: Visão detalhada mês a mês
- ✅ **Consolidação trimestral**: Totais por trimestre fiscal
- ✅ **Segregação por tipo**: Consultas/plantão vs outros serviços
- ✅ **Base para impostos**: Fonte para cálculo de impostos devidos
- ✅ **Análise temporal**: Comparação de performance mensal

**Observação incluída:**
```html
<small class="text-muted fst-italic">* Valores por data de emissão da nota fiscal</small>
```

### **7. 📈 Integração com o Sistema**

**Variável no contexto:**
- **`notas_fiscais_emitidas`**: Dictionary com arrays de dados mensais e trimestrais
- **Estrutura**: `{'receita_consultas': [...], 'receita_outros': [...], 'receita_bruta_trimestral': [...]}`
- **Cálculo em tempo real**: Agregação dinâmica das notas fiscais emitidas

## 🎯 **Resultado Final**

A tabela **"Notas Fiscais Emitidas"** foi implementada com:

✅ **Estrutura idêntica ao anexo**: 3 linhas, header duplo, merges trimestrais
✅ **Posicionamento correto**: Antes da tabela "Impostos Retidos na Nota Fiscal"  
✅ **Dados dinâmicos**: Calculados em tempo real das notas fiscais
✅ **Design consistente**: Segue padrão visual das demais tabelas
✅ **Funcionalidade completa**: Receitas mensais + totais trimestrais

**Fonte**: Implementação baseada no modelo `NotaFiscal` em `medicos/models/fiscal.py`, campos `val_bruto` e `tipo_servico`, conforme `.github/copilot-instructions.md`, seção 4.
