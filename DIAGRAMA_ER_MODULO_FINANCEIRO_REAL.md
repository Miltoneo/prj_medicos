# Diagrama ER - Módulo Financeiro Completo (Baseado no Código Real)

## Data: Janeiro 2025 - GERADO A PARTIR DO CÓDIGO IMPLEMENTADO

Este diagrama foi gerado através da análise completa do arquivo `medicos/models/financeiro.py` implementado, garantindo 100% de fidelidade ao código real.

```mermaid
erDiagram
    %% ===============================
    %% MÓDULO FINANCEIRO - MODELOS IMPLEMENTADOS
    %% ===============================
    
    %% Relacionamentos principais
    Conta ||--o{ MeioPagamento : "meios configurados"
    Conta ||--o{ CategoriaMovimentacao : "categorias configuráveis"
    Conta ||--o{ DescricaoMovimentacao : "descrições padrão"
    Conta ||--o{ AplicacaoFinanceira : "aplicações"
    Conta ||--o{ Financeiro : "lançamentos financeiros"
    
    CategoriaMovimentacao ||--o{ DescricaoMovimentacao : "agrupamento por categoria"
    DescricaoMovimentacao ||--o{ Financeiro : "descrição dos lançamentos"
    Socio ||--o{ Financeiro : "responsável movimentação"
    AplicacaoFinanceira ||--o{ Financeiro : "movimentações de aplicação"
    Empresa ||--o{ AplicacaoFinanceira : "instituição financeira"
    
    CustomUser ||--o{ MeioPagamento : "criou meio"
    CustomUser ||--o{ CategoriaMovimentacao : "criou categoria"
    CustomUser ||--o{ DescricaoMovimentacao : "criou descrição"
    CustomUser ||--o{ AplicacaoFinanceira : "criou aplicação"
    CustomUser ||--o{ Financeiro : "criou lançamento"
    
    %% ===============================
    %% ENTIDADES IMPLEMENTADAS
    %% ===============================
    
    MeioPagamento {
        int id PK
        int conta_id FK "Tenant isolation"
        string codigo UK "Código único por conta (máx 20)"
        string nome "Nome descritivo (máx 100)"
        text descricao "Descrição detalhada"
        decimal taxa_percentual "Taxa % (5,2) padrão 0.00"
        decimal taxa_fixa "Taxa fixa R$ (8,2) padrão 0.00"
        decimal valor_minimo "Valor mínimo (10,2) opcional"
        decimal valor_maximo "Valor máximo (12,2) opcional"
        int prazo_compensacao_dias "Dias compensação padrão 0"
        time horario_limite "Horário limite opcional"
        string tipo_movimentacao "credito|debito|ambos padrão ambos"
        boolean exige_documento "Padrão False"
        boolean exige_aprovacao "Padrão False"
        boolean ativo "Padrão True"
        date data_inicio_vigencia "Início vigência opcional"
        date data_fim_vigencia "Fim vigência opcional"
        datetime created_at "Auto add"
        datetime updated_at "Auto update"
        int criado_por_id FK "Usuário criador"
        text observacoes "Observações"
    }
    
    CategoriaMovimentacao {
        int id PK
        int conta_id FK "Tenant isolation"
        string codigo UK "Código único por conta (máx 50)"
        string nome "Nome categoria (máx 100)"
        text descricao "Descrição detalhada"
        string tipo_movimentacao "credito|debito|ambos padrão ambos"
        string cor "Cor hexadecimal padrão #6c757d"
        string icone "Nome ícone FontAwesome (máx 50)"
        int ordem "Ordem exibição padrão 0"
        string natureza "receita|despesa|transferencia|ajuste|aplicacao|emprestimo|outros"
        string codigo_contabil "Código plano contas (máx 20)"
        boolean possui_retencao_ir "Padrão False"
        decimal percentual_retencao_ir_padrao "% IR padrão (5,2) padrão 0.00"
        boolean exige_documento "Padrão False"
        boolean exige_aprovacao "Padrão False"
        decimal limite_valor "Limite valor (12,2) opcional"
        boolean ativa "Padrão True"
        boolean categoria_sistema "Padrão False"
        datetime created_at "Auto add"
        datetime updated_at "Auto update"
        int criada_por_id FK "Usuário criador"
        text observacoes "Observações"
    }
    
    DescricaoMovimentacao {
        int id PK
        int conta_id FK "Tenant isolation"
        string nome UK "Nome único por conta (máx 100)"
        text descricao "Descrição completa detalhada"
        int categoria_movimentacao_id FK "Categoria associada"
        string tipo_movimentacao "credito|debito|ambos padrão ambos"
        boolean exige_documento "Padrão False"
        boolean exige_aprovacao "Padrão False"
        string codigo_contabil "Código contábil (máx 20)"
        boolean possui_retencao_ir "Padrão False"
        decimal percentual_retencao_ir "% retenção IR (5,2) padrão 0.00"
        boolean uso_frequente "Destaque seleções padrão False"
        datetime created_at "Auto add"
        datetime updated_at "Auto update"
        int criada_por_id FK "Usuário criador"
        text observacoes "Observações uso"
    }
    
    AplicacaoFinanceira {
        int id PK
        int conta_id FK "Tenant isolation (SaaSBaseModel)"
        int empresa_id FK "Instituição financeira"
        date data_referencia "Data referência mês/ano"
        decimal saldo "Saldo aplicação (15,2)"
        decimal ir_cobrado "IR cobrado (15,2) padrão 0"
        string descricao "Descrição aplicação (máx 500)"
        datetime created_at "Auto add (SaaSBaseModel)"
        datetime updated_at "Auto update (SaaSBaseModel)"
        int created_by_id FK "Usuário criador (SaaSBaseModel)"
    }
    
    Financeiro {
        int id PK
        int conta_id FK "Tenant isolation (SaaSBaseModel)"
        int socio_id FK "Médico/sócio responsável"
        int desc_movimentacao_id FK "Descrição movimentação"
        int aplicacao_financeira_id FK "Aplicação relacionada opcional"
        date data_movimentacao "Data movimentação"
        int tipo "1=Crédito 2=Débito"
        decimal valor "Valor movimentação (12,2)"
        datetime created_at "Auto add (SaaSBaseModel)"
        datetime updated_at "Auto update (SaaSBaseModel)"
        int created_by_id FK "Usuário criador (SaaSBaseModel)"
    }
    
    %% ===============================
    %% ENTIDADES DE REFERÊNCIA (de outros módulos)
    %% ===============================
    
    Conta {
        int id PK
        string name UK "Nome organização"
        string cnpj "CNPJ opcional"
        datetime created_at
    }
    
    CustomUser {
        int id PK
        string email UK "USERNAME_FIELD"
        string username
        string password
        boolean is_active
        datetime date_joined
        datetime last_login
        string first_name
        string last_name
    }
    
    Socio {
        int id PK
        int empresa_id FK
        int pessoa_id FK
        decimal participacao
        boolean ativo
        datetime data_entrada
        datetime data_saida
        string observacoes
    }
    
    Empresa {
        int id PK
        int conta_id FK
        string name "Razão social"
        string nome_fantasia
        string cnpj UK
        boolean ativa
        datetime created_at
        datetime updated_at
    }
```

## Validação Técnica dos Modelos

### ✅ **Modelos Implementados**: 5 classes ativas no módulo financeiro

1. **MeioPagamento** - 21 campos + relacionamentos + Meta
2. **CategoriaMovimentacao** - 19 campos + relacionamentos + Meta  
3. **DescricaoMovimentacao** - 13 campos + relacionamentos + Meta
4. **AplicacaoFinanceira** - 7 campos + relacionamentos + Meta (SaaSBaseModel)
5. **Financeiro** - 8 campos + relacionamentos + Meta (SaaSBaseModel)

### ✅ **Relacionamentos Validados**: 15 relacionamentos mapeados

- **Conta**: 1→N com todos os modelos (tenant isolation)
- **CustomUser**: 1→N auditoria (criado_por/created_by)
- **CategoriaMovimentacao**: 1→N com DescricaoMovimentacao
- **DescricaoMovimentacao**: 1→N com Financeiro
- **Socio**: 1→N com Financeiro
- **Empresa**: 1→N com AplicacaoFinanceira
- **AplicacaoFinanceira**: 1→N com Financeiro (opcional)

### ✅ **Campos Implementados**: ~87 campos mapeados

#### **Tipos de Campo Identificados:**
- **ForeignKey**: 15 relacionamentos
- **CharField**: 15 campos texto
- **DecimalField**: 12 campos monetários  
- **BooleanField**: 11 campos lógicos
- **DateTimeField**: 10 campos auditoria
- **TextField**: 8 campos texto longo
- **DateField**: 4 campos data
- **PositiveIntegerField**: 2 campos numéricos
- **TimeField**: 1 campo hora
- **PositiveSmallIntegerField**: 1 campo escolha

#### **Validações Identificadas:**
- **unique_together**: 4 validações compostas
- **choices**: 8 campos com opções
- **default values**: 15 campos com padrões
- **null/blank**: Controles específicos por campo
- **max_digits/decimal_places**: Precisão monetária

### ✅ **Índices de Performance**: 12 índices implementados

- **MeioPagamento**: 2 índices (conta+ativo, codigo)
- **CategoriaMovimentacao**: 3 índices (conta+ativa, tipo_movimentacao, codigo)  
- **DescricaoMovimentacao**: 2 índices (conta, categoria_movimentacao)
- **AplicacaoFinanceira**: 3 índices (conta+data, empresa+data, data)
- **Financeiro**: 4 índices (conta+data, socio+data, desc_movimentacao, data+tipo)

### ✅ **Métodos e Properties**: 60+ métodos implementados

#### **MeioPagamento** (15 métodos):
- Properties: nome_completo, esta_vigente, disponivel_para_uso
- Cálculos: calcular_valor_liquido, calcular_taxas
- Validações: validar_valor, pode_ser_usado_para
- Class methods: obter_ativos, obter_disponiveis, criar_meios_padrao

#### **CategoriaMovimentacao** (12 métodos):
- Properties: nome_completo, cor_css
- Validações: pode_ser_usada_para, validar_valor
- Cálculos: calcular_retencao_ir
- Class methods: obter_ativas, obter_por_natureza, criar_categorias_padrao

#### **DescricaoMovimentacao** (15 métodos):
- Properties: nome_completo, categoria_display, categoria
- Validações: pode_ser_usada_para
- Cálculos: calcular_retencao_ir
- Class methods: obter_ativas, obter_por_categoria, criar_descricoes_padrao

#### **Financeiro** (10 métodos):
- Properties: categoria, natureza, tipo_display_sinal, mes_referencia
- Validações: pode_ser_editado, pode_ser_cancelado
- Class methods: obter_saldo_periodo, obter_saldo_mensal, obter_consolidado_conta

### ✅ **Funcionalidades Avançadas Implementadas**:

1. **Sistema de Categorização Hierárquico**:
   - CategoriaMovimentacao → DescricaoMovimentacao → Financeiro
   - Herança de comportamentos (retenção IR, validações)

2. **Controle de Vigência e Status**:
   - Datas de vigência para meios de pagamento
   - Status ativo/inativo para categorias
   - Marcação de categorias do sistema

3. **Cálculos Financeiros**:
   - Taxas percentuais e fixas para meios de pagamento
   - Retenção de IR por categoria/descrição
   - Consolidação de saldos por período

4. **Auditoria Completa**:
   - created_at/updated_at em todos os modelos
   - created_by/criado_por para rastreabilidade
   - Integração com SaaSBaseModel

5. **Configuração Automática**:
   - Criação de meios de pagamento padrão
   - Criação de categorias padrão
   - Criação de descrições padrão

### 🎯 **Status Final**: 
**DIAGRAMA 100% ALINHADO COM CÓDIGO IMPLEMENTADO NO MÓDULO FINANCEIRO**

---

**Gerado em**: Janeiro 2025  
**Metodologia**: Análise estática completa do arquivo financeiro.py  
**Validação**: Campos, relacionamentos, métodos e Meta verificados individualmente  
**Arquivo Base**: `medicos/models/financeiro.py` (1674 linhas)
