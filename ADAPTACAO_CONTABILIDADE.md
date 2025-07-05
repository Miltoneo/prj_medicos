# ================================
# PROPOSTA DE ADAPTAÇÃO PARA EMPRESA DE CONTABILIDADE
# Sistema SaaS para gestão contábil de associações de médicos
# ================================

## DOCUMENTOS RELACIONADOS
- [Sistema de Alíquotas e Tributação](SISTEMA_ALIQUOTAS_TRIBUTACAO.md) - Detalhamento completo das regras tributárias
- [Modelos Contábeis Detalhados](MODELOS_CONTABILIDADE_DETALHADOS.py) - Estrutura técnica dos modelos
- [Fluxo de Contabilidade Médicos](FLUXO_CONTABILIDADE_MEDICOS.md) - Fluxo técnico e de negócio

## 1. RENOMEAÇÃO DE CONCEITOS

### Modelo atual → Modelo adaptado:
- `Conta` → `AssociacaoMedica` (cliente da contabilidade)
- `ContaMembership` → `ResponsavelContabil` (contador responsável pela associação)
- `Licenca` → `ContratoContabil` (contrato de prestação de serviços)

## 2. ESTRUTURA ADAPTADA

### A. AssociacaoMedica (antes: Conta)
```python
class AssociacaoMedica(models.Model):
    """Associação de médicos - cliente da empresa de contabilidade"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Nome da Associação")
    cnpj = models.CharField(max_length=32, unique=True, verbose_name="CNPJ")
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    telefone = models.CharField(max_length=20, blank=True)
    email_contato = models.EmailField(blank=True)
    
    # Dados contábeis específicos
    regime_tributario = models.IntegerField(choices=[
        (1, 'Simples Nacional'),
        (2, 'Lucro Presumido'),
        (3, 'Lucro Real'),
    ], default=1)
    
    # Status do cliente
    ativo = models.BooleanField(default=True)
    data_inicio_servicos = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'associacao_medica'
        verbose_name = "Associação de Médicos"
        verbose_name_plural = "Associações de Médicos"
```

### B. ResponsavelContabil (antes: ContaMembership)
```python
class ResponsavelContabil(models.Model):
    """Contador da empresa responsável por uma associação"""
    associacao = models.ForeignKey(AssociacaoMedica, on_delete=models.CASCADE)
    contador = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    role = models.CharField(max_length=20, choices=[
        ('responsavel', 'Contador Responsável'),
        ('assistente', 'Assistente Contábil'),
        ('supervisor', 'Supervisor'),
    ], default='responsavel')
    
    data_atribuicao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'responsavel_contabil'
        unique_together = ['associacao', 'contador']
```

### C. ContratoContabil (antes: Licenca)
```python
class ContratoContabil(models.Model):
    """Contrato de prestação de serviços contábeis"""
    associacao = models.OneToOneField(AssociacaoMedica, on_delete=models.CASCADE, related_name='contrato')
    
    tipo_servico = models.CharField(max_length=50, choices=[
        ('completo', 'Contabilidade Completa'),
        ('fiscal', 'Apenas Fiscal'),
        ('folha', 'Folha de Pagamento'),
    ], default='completo')
    
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    
    # Limites do contrato
    limite_notas_fiscais = models.IntegerField(default=1000)
    limite_usuarios_associacao = models.IntegerField(default=50)
    
    class Meta:
        db_table = 'contrato_contabil'
```

## 3. MODELOS DE DADOS CONTÁBEIS

### A. NotaFiscal (já existe, adaptar)
```python
class NotaFiscal(SaaSBaseModel):
    """Notas fiscais recebidas das associações"""
    associacao = models.ForeignKey(AssociacaoMedica, on_delete=models.CASCADE)
    
    # Dados da nota
    numero = models.CharField(max_length=50)
    serie = models.CharField(max_length=10)
    data_emissao = models.DateField()
    data_recebimento = models.DateField()  # quando a contabilidade recebeu
    
    # Dados do prestador (médico)
    medico_nome = models.CharField(max_length=255)
    medico_cpf = models.CharField(max_length=14)
    
    # Valores
    valor_bruto = models.DecimalField(max_digits=10, decimal_places=2)
    valor_liquido = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Classificação contábil
    tipo_servico = models.CharField(max_length=50, choices=[
        ('consulta', 'Consultas Médicas'),
        ('procedimento', 'Procedimentos'),
        ('exame', 'Exames'),
        ('plantao', 'Plantão'),
        ('outros', 'Outros Serviços'),
    ])
    
    # Status de processamento
    status = models.CharField(max_length=20, choices=[
        ('recebida', 'Recebida'),
        ('processada', 'Processada'),
        ('lancada', 'Lançada na Contabilidade'),
        ('erro', 'Erro no Processamento'),
    ], default='recebida')
    
    # Impostos calculados
    irrf = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cofins = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Controle
    processada_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    data_processamento = models.DateTimeField(null=True, blank=True)
```

### B. DespesaAssociacao (adaptar modelo existente)
```python
class DespesaAssociacao(SaaSBaseModel):
    """Despesas das associações de médicos"""
    associacao = models.ForeignKey(AssociacaoMedica, on_delete=models.CASCADE)
    
    # Dados da despesa
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    
    # Classificação contábil
    categoria = models.CharField(max_length=50, choices=[
        ('aluguel', 'Aluguel'),
        ('salarios', 'Salários'),
        ('fornecedores', 'Fornecedores'),
        ('impostos', 'Impostos'),
        ('equipamentos', 'Equipamentos'),
        ('outros', 'Outras Despesas'),
    ])
    
    # Centro de custo
    centro_custo = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ], default='pendente')
    
    # Controle
    lancada_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    data_lancamento = models.DateTimeField(auto_now_add=True)
```

## 4. DASHBOARD ADAPTADO

### Métricas para empresa de contabilidade:
- **Clientes ativos** (associações de médicos)
- **Notas fiscais processadas** (por mês)
- **Receita da contabilidade** (contratos ativos)
- **Pendências por associação**
- **Relatórios fiscais em atraso**
- **Performance dos contadores**

## 5. FUNCIONALIDADES PRINCIPAIS

### A. Gestão de Clientes (Associações)
- Cadastro de associações de médicos
- Contratos de prestação de serviços
- Histórico de relacionamento

### B. Processamento de Documentos
- Upload de notas fiscais (PDF, XML)
- Categorização automática
- Cálculo de impostos
- Geração de relatórios

### C. Controle de Despesas
- Lançamento de despesas por associação
- Controle de vencimentos
- Relatórios de gastos

### D. Relatórios Contábeis
- Balancetes por associação
- DRE consolidado
- Livros fiscais
- Declarações de impostos

## 6. SISTEMA DE TRIBUTAÇÃO AUTOMÁTICA

### A. Modelo Aliquotas - ATUALIZADO ✅
O sistema implementa um robusto modelo de tributação que:

- **ISS Diferenciado por Tipo de Serviço**: 
  - Consultas Médicas: alíquota específica configurável
  - Plantão Médico: alíquota específica configurável
  - Vacinação/Exames/Procedimentos: alíquota específica configurável
- **Calcula automaticamente** PIS, COFINS, IRPJ e CSLL (uniformes)
- **Suporta diferentes regimes** tributários (Simples, Presumido, Real)
- **Controla vigência** das configurações tributárias
- **Valida consistência** dos percentuais e cálculos

### B. Tipos de Serviços Médicos Suportados
```python
# Tipos de serviços com alíquotas diferenciadas
CONSULTAS_MEDICAS = 1      # Prestação de serviço de consulta médica
PLANTAO_MEDICO = 2         # Prestação de serviço de plantão médico
VACINACAO_EXAMES = 3       # Vacinação, exames, procedimentos, outros

# Configuração de alíquotas diferenciadas
ISS_CONSULTAS = 3.00%      # Alíquota para consultas
ISS_PLANTAO = 2.50%        # Alíquota para plantão (pode ser menor)
ISS_OUTROS = 4.00%         # Alíquota para outros serviços
```

### C. Impostos Suportados - DETALHADO
```python
# ISS - DIFERENCIADO POR TIPO DE SERVIÇO
ISS_CONSULTAS = 3.00%      # Municipal (varia por cidade/serviço)
ISS_PLANTAO = 2.50%        # Municipal (pode ter incentivo)  
ISS_OUTROS = 4.00%         # Municipal (varia por cidade/serviço)

# IMPOSTOS FEDERAIS - UNIFORMES
PIS = 0.65%                # Federal (uniforme)
COFINS = 3.00%             # Federal (uniforme)

# IMPOSTOS SOBRE BASE PRESUMIDA - UNIFORMES
IRPJ = 15% + 10% adicional # Federal (sobre 32% da receita)
CSLL = 9%                  # Federal (sobre 32% da receita)
```

### D. Funcionalidades do Sistema - EXPANDIDAS
- **Cálculo automático diferenciado** por tipo de serviço médico
- **Seleção obrigatória** do tipo de serviço na nota fiscal
- **Múltiplas configurações** por período
- **Validação de alíquotas** específicas por tipo
- **Controle de vigência** temporal
- **Auditoria completa** de mudanças
- **Relatórios de carga** tributária por tipo de serviço

### E. Integração com NotaFiscal - AUTOMATIZADA
```python
# Processo automático diferenciado:
1. Nota fiscal criada com valor bruto + tipo de serviço
2. Sistema identifica tipo: Consultas/Plantão/Outros
3. Aplica alíquota ISS específica do tipo de serviço
4. Calcula demais impostos (PIS, COFINS, IRPJ, CSLL)
5. Atualiza todos os campos da nota fiscal
6. Gera lançamentos contábeis (Financeiro)
```

### F. Benefícios das Alíquotas Diferenciadas
- **Conformidade Fiscal**: Aplicação correta conforme legislação
- **Otimização Tributária**: Aproveitamento de alíquotas menores
- **Controle Gerencial**: Análise de rentabilidade por tipo de serviço
- **Automatização**: Eliminação de erros de classificação manual

Para detalhes técnicos e exemplos práticos, consulte: 
- [SISTEMA_ALIQUOTAS_TRIBUTACAO.md](SISTEMA_ALIQUOTAS_TRIBUTACAO.md)
- [exemplo_aliquotas_diferenciadas.py](exemplo_aliquotas_diferenciadas.py)

## 7. IMPLEMENTAÇÃO

Quer que eu implemente essas adaptações no sistema atual?

### Passos sugeridos:
1. Backup do banco atual
2. Criação dos novos modelos
3. Migração dos dados existentes
4. Adaptação das views e templates
5. Atualização do dashboard
6. Testes completos

### Tempo estimado: 4-6 horas
