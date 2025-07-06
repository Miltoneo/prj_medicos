# Sistema de Rateio de Notas Fiscais entre Médicos

## Visão Geral

O sistema permite que uma nota fiscal de serviços médicos seja rateada entre um ou mais médicos/sócios, distribuindo proporcionalmente tanto o valor bruto quanto os impostos calculados.

## Como Funciona

### 1. **Processo de Rateio**

Quando uma nota fiscal precisa ser dividida entre médicos:

1. A contabilidade acessa a nota fiscal já emitida
2. Define quais médicos participarão do rateio
3. Especifica o percentual ou valor para cada médico
4. O sistema calcula automaticamente os impostos proporcionais
5. Gera o valor líquido individual para cada médico

### 2. **Tipos de Rateio Disponíveis**

#### **Rateio por Percentual**
- Contabilidade define percentuais específicos para cada médico
- Exemplo: Médico A = 60%, Médico B = 40%
- Sistema calcula valores automaticamente

#### **Rateio por Valor Fixo**
- Contabilidade define valores específicos para cada médico
- Exemplo: Médico A = R$ 3.000, Médico B = R$ 2.000
- Sistema calcula percentuais automaticamente

#### **Rateio Automático (Igualitário)**
- Sistema divide igualmente entre os médicos selecionados
- Exemplo: 3 médicos = 33,33% cada

### 3. **Cálculos Automáticos**

Para cada médico no rateio, o sistema calcula:

- **Valor Bruto Individual**: Baseado no percentual de participação
- **Impostos Proporcionais**: ISS, PIS, COFINS, IRPJ, CSLL proporcionais
- **Valor Líquido Individual**: Valor bruto - impostos proporcionais

## Exemplo Prático

### Nota Fiscal Original:
- **Valor Bruto**: R$ 10.000,00
- **ISS (2%)**: R$ 200,00
- **PIS (0,65%)**: R$ 65,00
- **COFINS (3%)**: R$ 300,00
- **IRPJ**: R$ 480,00
- **CSLL**: R$ 288,00
- **Total Impostos**: R$ 1.333,00
- **Valor Líquido**: R$ 8.667,00

### Rateio entre 2 Médicos:

#### **Médico A (60%)**:
- **Valor Bruto**: R$ 6.000,00
- **ISS**: R$ 120,00
- **PIS**: R$ 39,00
- **COFINS**: R$ 180,00
- **IRPJ**: R$ 288,00
- **CSLL**: R$ 172,80
- **Total Impostos**: R$ 799,80
- **Valor Líquido**: R$ 5.200,20

#### **Médico B (40%)**:
- **Valor Bruto**: R$ 4.000,00
- **ISS**: R$ 80,00
- **PIS**: R$ 26,00
- **COFINS**: R$ 120,00
- **IRPJ**: R$ 192,00
- **CSLL**: R$ 115,20
- **Total Impostos**: R$ 533,20
- **Valor Líquido**: R$ 3.466,80

## Validações do Sistema

### **Validações Automáticas:**

1. **Total não pode exceder 100%**: Soma dos percentuais ≤ 100%
2. **Valores não podem exceder NF**: Soma dos valores ≤ valor da nota fiscal
3. **Médicos da mesma empresa**: Todos devem pertencer à empresa emitente
4. **Consistência percentual/valor**: Percentual deve corresponder ao valor
5. **Unicidade**: Um médico não pode aparecer duas vezes na mesma NF

### **Controles de Integridade:**

- Recálculo automático quando nota fiscal é alterada
- Validação antes de salvar qualquer rateio
- Logs de auditoria para alterações
- Prevenção de exclusão de NF com rateios ativos

## Interface de Uso

### **Para Contabilidade:**

1. **Criar Rateio**:
   ```python
   # Por percentuais
   NotaFiscalRateioMedico.criar_rateio_por_percentuais(
       nota_fiscal=nf,
       rateios_config=[
           {'medico': medico_a, 'percentual': 60},
           {'medico': medico_b, 'percentual': 40}
       ],
       usuario=usuario_logado
   )
   
   # Por valores
   NotaFiscalRateioMedico.criar_rateio_por_valores(
       nota_fiscal=nf,
       rateios_config=[
           {'medico': medico_a, 'valor': 6000.00},
           {'medico': medico_b, 'valor': 4000.00}
       ],
       usuario=usuario_logado
   )
   
   # Automático (igualitário)
   NotaFiscalRateioMedico.criar_rateio_automatico(
       nota_fiscal=nf,
       medicos_lista=[medico_a, medico_b, medico_c],
       usuario=usuario_logado
   )
   ```

2. **Consultar Rateio**:
   ```python
   # Resumo da nota fiscal
   resumo = nf.obter_rateio_resumo()
   
   # Verificações rápidas
   if nf.tem_rateio:
       print(f"Rateada entre {nf.total_medicos_rateio} médicos")
       print(f"Total rateado: {nf.percentual_total_rateado}%")
       print(f"Valor pendente: R$ {nf.valor_pendente_rateio:.2f}")
   ```

## Relatórios Disponíveis

### **Resumo por Médico**
```python
resumo = NotaFiscal.obter_resumo_por_medico(
    medico=medico_especifico,
    periodo_inicio=datetime.date(2024, 1, 1),
    periodo_fim=datetime.date(2024, 12, 31)
)
```

**Retorna:**
- Total de notas fiscais por médico
- Valor bruto total recebido
- Valor líquido total
- Total de impostos pagos
- Valor médio por nota
- Percentual médio de participação

### **Resumo por Nota Fiscal**
```python
resumo = nf.obter_rateio_resumo()
```

**Retorna:**
- Lista de médicos participantes
- Percentuais e valores por médico
- Status do rateio (completo/incompleto)
- Valores pendentes de rateio

## Benefícios do Sistema

### **Para a Contabilidade:**
- ✅ Controle total sobre distribuição de receitas
- ✅ Cálculos automáticos e precisos
- ✅ Relatórios detalhados por médico
- ✅ Auditoria completa de alterações
- ✅ Prevenção de erros manuais

### **Para os Médicos:**
- ✅ Transparência na distribuição
- ✅ Relatórios individualizados
- ✅ Cálculo correto de impostos
- ✅ Histórico completo de participações

### **Para o Sistema:**
- ✅ Integridade referencial mantida
- ✅ Validações automáticas
- ✅ Performance otimizada
- ✅ Flexibilidade para diferentes cenários

## Casos de Uso Comuns

### **1. Plantão Compartilhado**
- Vários médicos trabalharam no mesmo plantão
- Rateio baseado em horas trabalhadas
- Exemplo: 3 médicos, 8h cada = rateio igualitário

### **2. Procedimento em Equipe**
- Cirurgia com médico principal e auxiliares
- Rateio baseado no papel de cada um
- Exemplo: Principal 70%, Auxiliar 30%

### **3. Consultas Compartilhadas**
- Clínica com vários médicos
- Rateio baseado no número de atendimentos
- Exemplo: Baseado em relatório de produtividade

### **4. Especialidades Diferentes**
- Nota fiscal mista (consulta + exame)
- Rateio por especialidade
- Exemplo: Clínico 60%, Radiologista 40%

## Integração com Módulo Financeiro

O rateio de notas fiscais se integra naturalmente com o módulo financeiro:

- **Lançamentos por Médico**: Cada rateio pode gerar lançamento individual
- **Controle de Recebidos**: Tracking por médico dos valores recebidos
- **Relatórios Consolidados**: Visão unificada de receitas por médico
- **Fluxo de Caixa**: Acompanhamento individual e consolidado

## Considerações Técnicas

### **Performance:**
- Índices otimizados para consultas frequentes
- Queries eficientes para relatórios
- Cache de cálculos quando apropriado

### **Manutenibilidade:**
- Código limpo e bem documentado
- Validações centralizadas
- Testes automatizados para cenários críticos

### **Escalabilidade:**
- Suporte a qualquer número de médicos
- Rateios complexos e aninhados
- Histórico completo mantido

**O sistema de rateio de notas fiscais proporciona flexibilidade total para a contabilidade gerenciar a distribuição de receitas entre médicos, mantendo a precisão fiscal e a transparência necessárias.**
