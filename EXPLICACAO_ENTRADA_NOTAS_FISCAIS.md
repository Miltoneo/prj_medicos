# Explicação: Entrada de Notas Fiscais no Sistema

## Modelo Responsável pela Entrada de Notas Fiscais

A entrada das notas fiscais no sistema ocorre através do modelo **`NotaFiscal`**, que é uma entidade central do sistema de gestão médica e financeira.

## Localização e Estrutura do Modelo

### Localização no Código
- **Modelo**: `NotaFiscal`
- **Módulo**: `medicos/models/fiscal.py` (importado via `__init__.py`)
- **Views**: `medicos/views_nota_fiscal.py`
- **Templates**: `medicos/templates/faturamento/`
- **Forms**: `medicos/forms.py`

### Referência no Diagrama ER
No diagrama ER fornecido, o modelo `NotaFiscal` **não está explicitamente representado** como uma entidade independente. Isso indica uma lacuna na documentação visual, pois o modelo existe e está sendo amplamente utilizado no código.

## Estrutura do Modelo NotaFiscal

### Campos Principais
```python
class NotaFiscal(models.Model):
    # Identificação
    numero = CharField(max_length=50)
    serie = CharField(max_length=10)
    
    # Relacionamentos
    conta = ForeignKey(Conta)
    fornecedor = ForeignKey(Empresa)  # Empresa/associação
    socio = ForeignKey(Socio)         # Médico responsável
    
    # Datas
    dtEmissao = DateField("Data de Emissão")
    dtRecebimento = DateField("Data de Recebimento")
    
    # Valores financeiros
    val_bruto = DecimalField("Valor Bruto")
    val_liquido = DecimalField("Valor Líquido")
    
    # Impostos detalhados
    val_ISS = DecimalField("ISS")
    val_PIS = DecimalField("PIS")
    val_COFINS = DecimalField("COFINS")
    val_IR = DecimalField("IRPJ")
    val_CSLL = DecimalField("CSLL")
    
    # Classificação por tipo de serviço
    tipo_aliquota = IntegerField(choices=[
        (NFISCAL_ALIQUOTA_CONSULTAS, "Consultas"),
        (NFISCAL_ALIQUOTA_PLANTAO, "Plantão"), 
        (NFISCAL_ALIQUOTA_OUTROS, "Outros Serviços")
    ])
    
    # Dados do tomador
    tomador = CharField("Tomador dos Serviços")
    desc_servico = TextField("Descrição dos Serviços")
    
    # Status e controle
    status = CharField("Status da NF")
    processada_por = ForeignKey(User)
    data_processamento = DateTimeField()
```

## Processo de Entrada de Notas Fiscais

### 1. **Interface de Entrada**
- **URL**: `/medicos/nf_incluir/`
- **View**: `nf_incluir()` em `views_nota_fiscal.py`
- **Template**: `faturamento/nf_editar.html`
- **Form**: `Edit_NotaFiscal_Form` em `forms.py`

### 2. **Métodos de Entrada**

#### A. **Entrada Manual**
```python
def nf_incluir(request):
    """Inclusão manual de nota fiscal"""
    if request.method == 'POST':
        form = Edit_NotaFiscal_Form(request.POST)
        if form.is_valid():
            nf = form.save(commit=False)
            nf.fornecedor = empresa
            nf.save()
```

#### B. **Importação via XML**
```python
def importar_xml(request, fornecedor):
    """Importação de nota fiscal via arquivo XML"""
    # Processa arquivo XML da NF-e
    # Extrai dados e cria instância NotaFiscal
```

### 3. **Cálculo Automático de Impostos**

O sistema possui integração com o modelo `Aliquotas` para cálculo automático:

```python
# Aplicação automática de impostos
aliquota = Aliquotas.objects.filter(conta=conta).first()
if aliquota:
    aliquota.aplicar_impostos_nota_fiscal(nota_fiscal)
    nota_fiscal.save()
```

## Integração com Outros Módulos

### 1. **Módulo Fiscal**
- **Alíquotas diferenciadas** por tipo de serviço
- **Cálculo automático** de ISS, PIS, COFINS, IRPJ, CSLL
- **Aplicação de regime tributário** específico

### 2. **Módulo Financeiro (Sistema Manual)**
- **⚠️ IMPORTANTE**: No sistema atual, as notas fiscais **NÃO geram automaticamente** lançamentos no fluxo de caixa individual
- Todos os lançamentos financeiros devem ser **feitos manualmente** pela contabilidade
- A nota fiscal serve apenas para **controle contábil** e **base de cálculo de impostos**

### 3. **Módulo de Rateio**
- NotaFiscal pode ser **rateada entre médicos** usando percentuais configurados
- Relacionamento com `PercentualRateioMensal` e `TemplateRateioMensalDespesas`

## Fluxo Completo de Entrada

### Passo 1: Criação da Nota Fiscal
```python
nota = NotaFiscal.objects.create(
    numero="001/2024",
    fornecedor=empresa,
    socio=medico,
    val_bruto=Decimal('10000.00'),
    tipo_aliquota=NFISCAL_ALIQUOTA_CONSULTAS,
    dtEmissao=date.today(),
    tomador="Hospital ABC"
)
```

### Passo 2: Cálculo Automático de Impostos
```python
aliquota = Aliquotas.obter_aliquota_vigente(conta)
resultado = aliquota.calcular_impostos_nf(
    valor_bruto=nota.val_bruto,
    tipo_servico='consultas'
)

# Atualiza campos da nota
nota.val_ISS = resultado['valor_iss']
nota.val_PIS = resultado['valor_pis']
nota.val_COFINS = resultado['valor_cofins']
nota.val_IR = resultado['valor_ir']
nota.val_CSLL = resultado['valor_csll']
nota.val_liquido = resultado['valor_liquido']
nota.save()
```

### Passo 3: Rateio (Opcional)
```python
# Criar rateio entre médicos
rateio = Despesa_socio_rateio.objects.create(
    despesa=nota,
    socio=medico,
    percentual=Decimal('40.00'),
    vl_rateio=nota.val_liquido * Decimal('0.40')
)
```

## Características Especiais

### 1. **Alíquotas Diferenciadas**
O sistema suporta **três tipos de alíquotas de ISS**:
- **Consultas**: Alíquota padrão para consultas médicas
- **Plantão**: Alíquota específica para plantões
- **Outros**: Procedimentos, exames, vacinação

### 2. **Cálculo de IRPJ Progressivo**
- **15%** sobre a base de cálculo normal
- **10% adicional** sobre o excesso de R$ 60.000,00

### 3. **Regime Tributário Inteligente**
- **ISS**: Sempre regime de competência (LC 116/2003)
- **PIS/COFINS/IRPJ/CSLL**: Podem seguir regime da empresa (competência/caixa)

## Relatórios e Consultas

### Views de Consulta
- **Lista de NFs**: `NFiscal_TableView`
- **Edição**: `nf_editar()`
- **Exclusão**: `nf_excluir()`

### Templates Principais
- `faturamento/faturamento.html` - Lista
- `faturamento/nf_editar.html` - Formulário
- `apuracao/apuracao_socio_mes.html` - Relatórios

## Considerações sobre o Diagrama ER

### Lacuna Identificada
O modelo `NotaFiscal` deveria estar representado no diagrama ER como uma entidade principal com os seguintes relacionamentos:

```mermaid
NotaFiscal {
    int id PK
    int conta_id FK
    int fornecedor_id FK
    int socio_id FK
    string numero UK
    date dtEmissao
    date dtRecebimento
    decimal val_bruto
    decimal val_liquido
    decimal val_ISS
    decimal val_PIS
    decimal val_COFINS
    decimal val_IR
    decimal val_CSLL
    int tipo_aliquota
    string tomador
    string status
}

%% Relacionamentos
Conta ||--o{ NotaFiscal : "tem notas fiscais"
Empresa ||--o{ NotaFiscal : "fornece serviços"
Socio ||--o{ NotaFiscal : "presta serviços"
```

## Conclusão

A entrada de notas fiscais é um processo central no sistema que:

1. **Ocorre principalmente** através do modelo `NotaFiscal`
2. **Integra-se** com o sistema de alíquotas para cálculo automático de impostos
3. **Suporta diferentes tipos** de serviços médicos com alíquotas diferenciadas
4. **Permite rateio** entre múltiplos médicos
5. **Não gera automaticamente** lançamentos financeiros (sistema manual)
6. **Deveria estar representado** no diagrama ER para completude da documentação

O modelo é fundamental para o controle contábil e fiscal das associações médicas, fornecendo a base para todos os cálculos tributários do sistema.
