# Diretiva de Regras de Negócio: Cadastro e Gestão de Alíquotas

## Contexto
O sistema deve permitir o cadastro, consulta e gestão de alíquotas fiscais (ex: INSS, IRRF, ISS, etc.) de forma padronizada e alinhada ao contexto multi-tenant.

## Regras de Negócio
- O fluxo de cadastro de alíquotas inicia por uma tela de lista, exibindo todas as alíquotas já cadastradas para a empresa ou contexto atual.
- O usuário pode visualizar, editar, excluir/inativar e cadastrar novas alíquotas, mantendo o histórico de alterações.
- Cada alíquota deve conter: nome, percentual, tipo, data de início e fim de vigência, e observações.
- O sistema deve preservar o histórico de alíquotas, permitindo múltiplas vigências e garantindo rastreabilidade das mudanças ao longo do tempo.
- Apenas alíquotas vigentes devem ser consideradas nos cálculos atuais, mas o histórico deve ser mantido para auditoria e consulta.
- A navegação e interface devem seguir o padrão dos demais cadastros, com menu lateral, filtros, tabela responsiva e ações claras.
- O cadastro de nova alíquota não apaga as anteriores, apenas adiciona uma nova vigência.
- O sistema deve evitar duplicidade e facilitar a busca por alíquotas específicas.

## Justificativa
Essa abordagem garante consistência visual e funcional, facilita a gestão fiscal, preserva o histórico de alterações e está alinhada com cenários em que regras fiscais mudam periodicamente.
