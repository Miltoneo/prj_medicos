# Regras de Documentação e Negócio (migradas de praticas_e_padroes.md)

## Modelagem de Dados
- Respeitar constraints de unique_together definidas no código.
- Manter validações em métodos `clean()` conforme implementado.
- Preservar índices de performance existentes.
- Não alterar relacionamentos sem análise completa de impacto.
- Documentar decisões de design baseadas no código atual.
- Toda análise de modelagem solicitada deve considerar TODOS os modelos definidos em hardcode Django.
- Incluir obrigatoriamente modelos de todos os arquivos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`.
- Analisar relacionamentos entre todos os modelos, não apenas subconjuntos.
- Validar constraints e dependencies em toda a base de modelos.
- Nunca fazer análise parcial ignorando modelos existentes no código.

## Validações e Compliance
- Manter validações tributárias conforme legislação brasileira.
- Preservar regras de negócio implementadas nos modelos.
- Respeitar constraints de integridade de dados.
- Manter logs de auditoria em todas as operações críticas.
- Validar percentuais de rateio (soma = 100%).

## Documentação e Organização
- Manter documentação centralizada em `docs/` com subpastas temáticas.
- Não criar novo arquivo de documentação se já existir arquivo que trate do mesmo assunto.
- Utilize e atualize sempre o arquivo existente para manter a rastreabilidade e evitar duplicidade de informações.

## Data de Competência Compartilhada
- Todos os cenários do sistema devem compartilhar a data de competência (mês/ano) selecionada pelo usuário. Esta data deve ser persistida na sessão do usuário e utilizada como padrão em todos os menus, páginas e funcionalidades que dependam de competência temporal.
- Ao alterar manualmente a competência, o novo valor deve ser salvo na sessão e mantido ao navegar entre diferentes cenários.
- O valor inicial deve ser o mês/ano atual, salvo na sessão na primeira navegação.
- Views e templates devem acessar `request.session['mes_ano']` para garantir sincronização.
- Essa regra garante consistência de contexto temporal para o usuário em todo o sistema.

## Regra: Comportamento da Data de Competência
- A data de competência (mês/ano) é compartilhada por todos os cenários e módulos do sistema.
- Ao acessar o sistema pela primeira vez, a data de competência é inicializada com o mês/ano atual e salva na sessão do usuário.
- O campo de competência é exibido no cabeçalho dos cenários principais.
- Quando o usuário altera manualmente a data de competência, o novo valor é salvo na sessão e mantido ao navegar entre diferentes cenários.
- Todas as views e templates que dependem de contexto temporal acessam `request.session['mes_ano']` para garantir sincronização.
- O valor permanece persistente durante toda a navegação do usuário, garantindo que filtros, cálculos e exibições estejam sempre alinhados com a competência selecionada.
- Essa abordagem garante consistência e contexto temporal único para o usuário em todo o sistema.
# Documentação Específica do Aplicativo prj_medicos

Este documento reúne todas as regras de negócio, fluxos funcionais, detalhes de cadastro, seleção de empresa, gestão de alíquotas, convites de usuários, rotas pendentes, modelagem de dados e exemplos específicos do sistema.

---

## 1. Regras de Negócio

### Cadastro de Usuário
- Todo usuário deve estar vinculado a pelo menos uma Conta (multi-tenant).
- Usuários sem vínculo não têm acesso ao sistema.
- O vínculo é feito via model `ContaMembership`.

### Validação de Licença
- O acesso do usuário à Conta depende da validade da licença (`Licenca.is_valida()`).
- Usuários de contas com licença expirada são redirecionados para a tela de licença expirada.

### Constraints de Modelos
- Respeitar `unique_together` e demais constraints definidas nos models.
- Validações adicionais devem ser implementadas no método `clean()` dos models.

### Abordagem SaaS Multi-Tenant
- O sistema segue arquitetura SaaS multi-tenant, onde cada usuário deve estar vinculado a uma ou mais contas (model `Conta`).
- O isolamento de dados entre tenants é garantido por constraints e validações no código.
- Toda autenticação, autorização e acesso a dados considera o contexto da conta ativa do usuário.
- Usuários sem vínculo com conta não têm acesso ao sistema.

### Registro e Criação de Conta
- O usuário poderá se registrar no sistema e criar sua própria Conta (tenant) de forma autônoma.
- O processo de registro deve criar automaticamente o vínculo entre o usuário e a nova Conta.
- Usuários registrados sem Conta não terão acesso ao sistema até concluírem o processo de criação/vinculação.

### Confirmação de Registro por E-mail
- Após o registro, o usuário recebe um e-mail com um link de ativação.
- O acesso ao sistema só é liberado após a confirmação do e-mail.
- O link de ativação expira após determinado tempo (ex: 48h).
- Caso o link expire, o usuário pode solicitar novo e-mail de ativação.
- Implementação baseada em token seguro e view dedicada para ativação.

---

## 2. Fluxos Funcionais e Detalhes de Cadastro

### Seleção de Empresa no Dashboard
- O usuário pode escolher a empresa ativa no dashboard, persistida na sessão.
- Contexto global para todas operações, garantindo isolamento multi-tenant.

### Cadastro e Gestão de Alíquotas
- Cadastro, consulta e gestão de alíquotas fiscais (INSS, IRRF, ISS, etc.)
- Histórico de vigências, rastreabilidade, interface padronizada.
- Apenas alíquotas vigentes são consideradas nos cálculos atuais, mas o histórico é mantido para auditoria.

### Cadastro de Empresas Médicas
- Cadastro realizado por administradores.
- Validação de CNPJ, vinculação como tenant, logs de auditoria.
- Templates de lista com paginação e botão "Novo".

### Convite e Cadastro de Usuários
- Convite automático por e-mail ao criar usuário.
- Link único de ativação, expiração, logs de convites.

### Rotas e Funcionalidades Pendentes
- Templates devem indicar rotas/funcionalidades pendentes com `href="#"` ou botão desabilitado.

---

## 3. Modelagem de Dados

### Diagrama ER Completo

```mermaid
---
title: Diagrama ER Completo - prj_medicos (Nomes Fieis aos Modelos Django)
---
erDiagram
    Conta ||--o{ Licenca : "licencas"
    Conta ||--o{ ContaMembership : "memberships"
    Conta ||--o{ Empresa : "empresas"
    Conta ||--o{ GrupoDespesa : "grupos_despesa"
    Conta ||--o{ ItemDespesa : "itens_despesa"
    Conta ||--o{ Despesa : "despesas"
    Conta ||--o{ ItemDespesaRateioMensal : "rateios_mensais"
    Conta ||--o{ MeioPagamento : "meios_pagamento"
    Conta ||--o{ DescricaoMovimentacaoFinanceira : "descricoes_movimentacao"
    Conta ||--o{ ConfiguracaoSistemaManual : "configuracoes"
    Conta ||--o{ LogAuditoriaFinanceiro : "logs_auditoria"
    Conta ||--o{ Aliquotas : "aliquotas"
    Conta ||--o{ AplicacaoFinanceira : "aplicacoes_financeiras"
    Conta ||--o{ Financeiro : "lancamentos_financeiros"
    Empresa ||--o{ Socio : "socios"
    Empresa ||--o{ NotaFiscal : "notas_fiscais"
    Empresa ||--o{ RegimeTributarioHistorico : "regimes_tributarios"
    Empresa ||--o{ AplicacaoFinanceira : "aplicacoes_financeiras"
    Socio ||--o{ ItemDespesaRateioMensal : "rateios"
    Socio ||--o{ Despesa : "despesas"
    Socio ||--o{ NotaFiscalRateioMedico : "rateio_nf"
    Socio ||--o{ Financeiro : "lancamentos_financeiros"
    GrupoDespesa ||--o{ ItemDespesa : "itens"
    ItemDespesa ||--o{ ItemDespesaRateioMensal : "rateios"
    ItemDespesa ||--o{ Despesa : "despesas"
    Aliquotas ||--o{ NotaFiscal : "aplica_em"
    NotaFiscal ||--o{ NotaFiscalRateioMedico : "rateia_em"
    MeioPagamento ||--o{ NotaFiscal : "usado_em"
    ConfiguracaoSistemaManual ||--o{ LogAuditoriaFinanceiro : "logs"
    DescricaoMovimentacaoFinanceira ||--o{ Financeiro : "lancamentos"
    AplicacaoFinanceira ||--o{ Financeiro : "movimentacoes"
```

---

Este documento deve ser revisado e atualizado sempre que novas regras de negócio ou fluxos específicos forem implementados no projeto.
