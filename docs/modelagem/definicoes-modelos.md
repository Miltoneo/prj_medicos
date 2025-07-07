# Definição hardcoded do modelo NotaFiscalRateioMedico (atualizado)

NotaFiscalRateioMedico {
    int id PK
    int nota_fiscal_id FK
    int socio_id FK
    decimal percentual_participacao
    decimal valor_bruto
    decimal valor_iss
    decimal valor_pis
    decimal valor_cofins
    decimal valor_ir
    decimal valor_csll
    decimal valor_liquido
    string tipo_rateio
    text observacoes_rateio
    datetime data_rateio
    int configurado_por_id FK
    datetime updated_at
}