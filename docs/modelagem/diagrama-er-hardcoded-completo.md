# Diagrama ER Completo - Projeto Django (hardcoded)

```mermaid
erDiagram
    Conta ||--o{ Licenca : "possui"
    Conta ||--o{ Empresa : "possui"
    Conta ||--o{ Pessoa : "possui"
    Conta ||--o{ Socio : "possui"
    Conta ||--o{ MeioPagamento : "possui"
    Conta ||--o{ CategoriaMovimentacao : "possui"
    Conta ||--o{ DescricaoMovimentacaoFinanceira : "possui"
    Conta ||--o{ GrupoDespesa : "possui"
    Conta ||--o{ ItemDespesa : "possui"
    Conta ||--o{ ItemDespesaRateioMensal : "possui"
    Conta ||--o{ Despesa : "possui"
    Conta ||--o{ TemplateRateioMensalDespesas : "possui"
    Conta ||--o{ ConfiguracaoSistemaManual : "possui"
    Conta ||--o{ LogAuditoriaFinanceiro : "possui"
    Conta ||--o{ Aliquotas : "possui"
    Conta ||--o{ ContaMembership : "possui"

    Empresa ||--o{ Socio : "tem"
    Empresa ||--o{ RegimeTributarioHistorico : "tem"
    Empresa ||--o{ NotaFiscal : "emite"

    Pessoa ||--o{ Socio : "é"

    Socio ||--o{ ItemDespesaRateioMensal : "participa"

    GrupoDespesa ||--o{ ItemDespesa : "contém"

    ItemDespesa ||--o{ ItemDespesaRateioMensal : "é rateado em"
    ItemDespesa ||--o{ Despesa : "classifica"

    TemplateRateioMensalDespesas ||--o{ Despesa : "aplica"

    CategoriaMovimentacao ||--o{ DescricaoMovimentacaoFinanceira : "classifica"

    NotaFiscal {
        int id
        int empresa_destinataria
        int tomador
        date dtEmissao
        decimal val_bruto
        ...
    }
    Empresa {
        int id
        int conta
        string name
        string cnpj
        int regime_tributario
        ...
    }
    Socio {
        int id
        int conta
        int empresa
        int pessoa
        ...
    }
    Pessoa {
        int id
        int conta
        int user
        string name
        ...
    }
    Conta {
        int id
        string name
        string cnpj
        ...
    }
    Licenca {
        int id
        int conta
        string plano
        ...
    }
    MeioPagamento {
        int id
        int conta
        string codigo
        ...
    }
    CategoriaMovimentacao {
        int id
        int conta
        string codigo
        ...
    }
    DescricaoMovimentacaoFinanceira {
        int id
        int conta
        int categoria_movimentacao
        ...
    }
    GrupoDespesa {
        int id
        int conta
        string codigo
        ...
    }
    ItemDespesa {
        int id
        int conta
        int grupo
        string codigo
        ...
    }
    ItemDespesaRateioMensal {
        int id
        int conta
        int item_despesa
        int socio
        date mes_referencia
        ...
    }
    Despesa {
        int id
        int conta
        int item
        int empresa
        int socio
        ...
    }
    TemplateRateioMensalDespesas {
        int id
        int conta
        date mes_referencia
        ...
    }
    ConfiguracaoSistemaManual {
        int id
        int conta
        ...
    }
    LogAuditoriaFinanceiro {
        int id
        int conta
        int usuario
        ...
    }
    Aliquotas {
        int id
        int conta
        ...
    }
    RegimeTributarioHistorico {
        int id
        int empresa
        int regime_tributario
        ...
    }
    ContaMembership {
        int id
        int conta
        int user
        string role
        ...
    }
```

> **Observação:**
> - O diagrama acima cobre todos os modelos hardcoded Django do projeto, seus relacionamentos e principais chaves.
> - Para visualizar, cole o bloco em um editor compatível com Mermaid (ex: VSCode com extensão Mermaid, ou https://mermaid.live/).
