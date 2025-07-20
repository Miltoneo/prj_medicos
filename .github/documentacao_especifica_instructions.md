# Instruções Específicas de Negócio e Modelagem – prj_medicos

> Para regras comportamentais, exemplos de resposta, rastreabilidade e busca detalhada, consulte exclusivamente `.github/copilot-instructions.md`.

Este arquivo foca apenas em regras de modelagem de dados, compliance, multi-tenant, fluxos de cadastro, organização e diagrama ER.

## 1. Modelagem de Dados
- Respeite constraints de `unique_together` e demais constraints definidas nos models.
- Mantenha validações em métodos `clean()` conforme implementado.
- Preserve índices de performance existentes.
- Não altere relacionamentos sem análise completa de impacto.
- Documente decisões de design baseadas no código atual.
- Toda análise de modelagem deve considerar TODOS os modelos definidos em: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`.
- Analise relacionamentos entre todos os modelos, não apenas subconjuntos.
- Valide constraints e dependências em toda a base de modelos.
- Nunca faça análise parcial ignorando modelos existentes no código.
- Fonte: docs/documentacao_especifica.md, linhas 3-15

## 2. Validações e Compliance
- Mantenha validações tributárias conforme legislação brasileira.
- Preserve regras de negócio implementadas nos modelos.
- Respeite constraints de integridade de dados.
- Mantenha logs de auditoria em todas as operações críticas.
- Valide percentuais de rateio (soma = 100%).
- Fonte: docs/documentacao_especifica.md, linhas 17-21

## 3. Documentação e Organização
- Mantenha documentação centralizada em `docs/` com subpastas temáticas.
- Não crie novo arquivo de documentação se já existir arquivo que trate do mesmo assunto.
- Utilize e atualize sempre o arquivo existente para manter rastreabilidade e evitar duplicidade de informações.
- Fonte: docs/documentacao_especifica.md, linhas 23-26

## 4. Data de Competência Compartilhada
- Todos os cenários do sistema devem compartilhar a data de competência (mês/ano) selecionada pelo usuário.
- Esta data deve ser persistida na sessão do usuário e utilizada como padrão em todos os menus, páginas e funcionalidades que dependam de competência temporal.
- Ao alterar manualmente a competência, o novo valor deve ser salvo na sessão e mantido ao navegar entre diferentes cenários.
- O valor inicial deve ser o mês/ano atual, salvo na sessão na primeira navegação.
- Views e templates devem acessar `request.session['mes_ano']` para garantir sincronização.
- Essa regra garante consistência de contexto temporal para o usuário em todo o sistema.
- Fonte: docs/documentacao_especifica.md, linhas 28-40

## 5. Regras de Negócio Essenciais
- Todo usuário deve estar vinculado a pelo menos uma Conta (multi-tenant).
- Usuários sem vínculo não têm acesso ao sistema.
- O vínculo é feito via model `ContaMembership`.
- O acesso do usuário à Conta depende da validade da licença (`Licenca.is_valida()`).
- Usuários de contas com licença expirada são redirecionados para a tela de licença expirada.
- Fonte: docs/documentacao_especifica.md, linhas 44-54

## 6. Abordagem SaaS Multi-Tenant
- O sistema segue arquitetura SaaS multi-tenant, onde cada usuário deve estar vinculado a uma ou mais contas (model `Conta`).
- O isolamento de dados entre tenants é garantido por constraints e validações no código.
- Toda autenticação, autorização e acesso a dados considera o contexto da conta ativa do usuário.
- Usuários sem vínculo com conta não têm acesso ao sistema.
- Fonte: docs/documentacao_especifica.md, linhas 56-62

## 7. Registro, Convite e Ativação de Usuários
- O usuário pode se registrar e criar sua própria Conta (tenant) de forma autônoma.
- O processo de registro deve criar automaticamente o vínculo entre o usuário e a nova Conta.
- Usuários registrados sem Conta não terão acesso ao sistema até concluírem o processo de criação/vinculação.
- Após o registro, o usuário recebe um e-mail com link de ativação (expira em 48h, pode ser reenviado).
- O acesso ao sistema só é liberado após a confirmação do e-mail.
- Fonte: docs/documentacao_especifica.md, linhas 64-77

## 8. Fluxos Funcionais e Cadastro
- O usuário pode escolher a empresa ativa no dashboard, persistida na sessão.
- Cadastro, consulta e gestão de alíquotas fiscais (INSS, IRRF, ISS, etc.) com histórico de vigências.
- Cadastro de empresas médicas realizado por administradores, com validação de CNPJ e logs de auditoria.
- Convite automático por e-mail ao criar usuário, com link único de ativação e logs de convites.
- Templates devem indicar rotas/funcionalidades pendentes com `href="#"` ou botão desabilitado.
- Fonte: docs/documentacao_especifica.md, linhas 79-104

## 9. Modelagem de Dados – Diagrama ER
- Consulte o diagrama ER completo no final do arquivo para visualizar todos os relacionamentos entre entidades principais do sistema.
- Fonte: docs/documentacao_especifica.md, linhas 106-153

---

Este arquivo foi gerado a partir de docs/documentacao_especifica.md para servir como referência rápida e operacional para agentes e desenvolvedores.
