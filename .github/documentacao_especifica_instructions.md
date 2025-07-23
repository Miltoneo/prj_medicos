## 11. Cenário de Apropriação de Despesas – Fluxo e Interfaces

### 12. Apuração de Impostos (ISS, PIS, COFINS, IRPJ, CSLL)

#### Legislação Tributária e Modelos Utilizados
Segundo a legislação tributária brasileira:
- **ISSQN:** A base de cálculo é o valor bruto dos serviços prestados, destacado em nota fiscal. Despesas não entram na base, exceto se houver previsão legal municipal específica. Modelos necessários: `NotaFiscal`, `Empresa`, `NotaFiscalRateioMedico`.
- **PIS/COFINS:** Incidem sobre a receita bruta de serviços, conforme notas fiscais emitidas. Não há dedução de despesas operacionais. Modelos necessários: `NotaFiscal`, `Empresa`, `NotaFiscalRateioMedico`.
- **IRPJ/CSLL:** Para lucro presumido, a base é um percentual da receita bruta das notas fiscais. Despesas não entram na base, exceto em lucro real. Modelos necessários: `NotaFiscal`, `Empresa`, `NotaFiscalRateioMedico`.

**Conclusão:**
A apuração dos impostos é feita sobre a receita bruta registrada nas notas fiscais. Os modelos de despesas (`Despesa`, `ItemDespesa`, `GrupoDespesa`) não são usados para cálculo direto dos impostos, mas podem ser relevantes para controle gerencial ou para ISS em casos específicos previstos em lei municipal.

**Fontes:**
- Lei Complementar 116/2003 (ISSQN)
- Lei 9.718/1998 (PIS/COFINS)
- Lei 9.430/1996 e IN RFB 1700/2017 (IRPJ/CSLL)
- `.github/documentacao_especifica_instructions.md`, seção "ISS"

### 1. Fluxo Geral
O cenário de despesas trata da apropriação mensal das despesas da empresa e dos sócios, sempre considerando o mês de competência ativo (`request.session['mes_ano']`). O usuário pode:
- Incluir, editar e excluir despesas da empresa (com ou sem rateio).
- Incluir, editar e excluir despesas de cada sócio (com ou sem rateio).

### 2. Interfaces
**a) Interface de Lista de Despesas do Mês de Competência**
- Exibe todas as despesas da empresa para o mês/ano corrente.
- Permite inclusão, edição e deleção de despesas.
- Ao acessar esta interface, o sistema verifica se existe lista de rateio para o mês/ano corrente; se não existir, copia automaticamente a lista do mês anterior (ver seção 10).
- Deve existir uma opção explícita para o usuário copiar manualmente as despesas do mês anterior, caso deseje.
- As despesas podem ser cadastradas como “com rateio” (apropriadas entre os sócios) ou “sem rateio” (apenas da empresa).

**b) Interface de Lista de Despesas dos Sócios**
- Exibe a lista de despesas apropriadas para cada sócio, já preenchida automaticamente com as despesas de rateio do mês corrente.
- Permite visualizar e editar os valores apropriados a cada sócio.
- Para cada item, devem ser exibidos: descrição da despesa, grupo, valor total, taxa de rateio (se aplicável), valor final, entre outros campos relevantes.
- Deve existir uma opção explícita para o usuário copiar manualmente as despesas do mês anterior para os sócios, caso deseje.

### 3. Referências
- .github/documentacao_especifica_instructions.md, seção 10 (automação e opção manual de cópia)
- .github/guia-desenvolvimento-instructions.md, seção 4 (contexto de competência e UI/UX)
- docs/README.md, linhas 1-25 (visão geral do fluxo de despesas)
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



Este arquivo foi gerado a partir de docs/documentacao_especifica.md para servir como referência rápida e operacional para agentes e desenvolvedores.

## 10. Automação da Lista de Rateio Mensal
- Sempre que o usuário acessar a funcionalidade de apropriação de despesas para um mês de competência, o sistema deve verificar se já existe uma lista de rateio cadastrada para aquele mês, empresa e conta.
- Caso não exista, a lista de rateio do mês anterior deve ser copiada automaticamente, respeitando todos os filtros de contexto (empresa_id, conta, mes_ano) e garantindo que não haja duplicidade de registros.
- O usuário só precisará acessar o cadastro de rateio para ajustes pontuais, tornando o processo mais eficiente e menos sujeito a esquecimentos.
- Esta automação deve ser validada para garantir integridade dos dados e rastreabilidade das operações.
- Fonte: .github/documentacao_especifica_instructions.md, seção 10.
