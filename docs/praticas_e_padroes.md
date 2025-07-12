# Práticas e Padrões de Desenvolvimento

Este documento reúne todas as diretrizes, práticas recomendadas e padrões que devem ser adotados para o desenvolvimento do sistema prj_medicos.

---

## 1. Código como Fonte da Verdade
- O código hardcoded é SEMPRE a referência absoluta para documentação.
- Nunca gerar documentação baseada em versões anteriores ou memória.
- Toda documentação deve ser regenerada a partir do código atual.
- Eliminar aliases legacy e padronizar nomenclaturas conforme código real.
- Validar sempre que documentação reflete exatamente o estado do código.

## 2. Arquitetura e Modularização
- Manter separação clara entre módulos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`.
- Respeitar isolamento multi-tenant através do modelo `Conta`.
- Preservar hierarquia de relacionamentos e constraints definidas no código.
- Não criar dependências circulares entre módulos.
- Manter modelos simples, focados e com responsabilidade única.

## 3. Nomenclatura e Padrões
- Modelos: PascalCase exato conforme definido no código.
- Campos: snake_case conforme implementação atual.
- Constantes: UPPER_SNAKE_CASE conforme padrões Django.
- Eliminar aliases de compatibilidade quando não utilizados.
- Manter consistência de nomes em todo o projeto.
- Atualizar referências em `admin.py`, `forms.py`, `views.py`, `tables.py` quando necessário.

## 4. Modelagem de Dados
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

## 5. Validações e Compliance
- Manter validações tributárias conforme legislação brasileira.
- Preservar regras de negócio implementadas nos modelos.
- Respeitar constraints de integridade de dados.
- Manter logs de auditoria em todas as operações críticas.
- Validar percentuais de rateio (soma = 100%).
## 6. Documentação e Organização
- Manter documentação centralizada em `docs/` com subpastas temáticas.
- Não criar novo arquivo de documentação se já existir arquivo que trate do mesmo assunto.
- Utilize e atualize sempre o arquivo existente para manter a rastreabilidade e evitar duplicidade de informações.

## 7. Desenvolvimento e Manutenção
- Testar todas as alterações em ambiente de desenvolvimento.
- Manter compatibilidade com Django 4.x.
- Preservar funcionalidades existentes ao fazer refatorações.
- Documentar breaking changes quando necessário.
- Manter requirements.txt atualizado.

- Otimizar queries com base em padrões de uso reais.
- Implementar paginação em listagens grandes.
## 9. Segurança e Auditoria
- Manter isolamento de dados por tenant (Conta).
- Preservar rastreamento de IP e user-agent.
- Implementar controles de acesso granulares.
- Implementar validações client-side quando apropriado.
- Manter responsividade para dispositivos móveis.
- Mudanças de layout e estilo devem ser aplicadas de forma centralizada, facilitando manutenção e evolução visual.
- A padronização deve priorizar clareza, legibilidade e responsividade.
- O menu deve destacar a página ativa e exibir informações do usuário autenticado quando aplicável.
- Melhorias de usabilidade e acessibilidade devem ser priorizadas em toda evolução do menu.

## 12. Melhores Práticas para Menus de Navegação
- Menus laterais (sidebar) são indicados para sistemas com múltiplas áreas, módulos ou funcionalidades agrupadas.
- O menu ativo deve ser destacado visualmente para orientar o usuário.
- Evitar menus excessivamente profundos ou complexos; priorizar clareza e rapidez de acesso.
- A escolha entre menu lateral ou topo deve considerar o perfil do usuário, quantidade de funcionalidades e contexto de uso.

## 14. Views Django
## 15. Data de Competência Compartilhada
- Todos os cenários do sistema devem compartilhar a data de competência (mês/ano) selecionada pelo usuário. Esta data deve ser persistida na sessão do usuário e utilizada como padrão em todos os menus, páginas e funcionalidades que dependam de competência temporal.
- Ao alterar manualmente a competência, o novo valor deve ser salvo na sessão e mantido ao navegar entre diferentes cenários.
- O valor inicial deve ser o mês/ano atual, salvo na sessão na primeira navegação.
- Views e templates devem acessar `request.session['mes_ano']` para garantir sincronização.
- Essa regra garante consistência de contexto temporal para o usuário em todo o sistema.

## 16. Revisão de Métodos de Validação
- Sempre revisar e, se necessário, remover ou ajustar validações duplicadas ou conflitantes tanto no formulário quanto no modelo.
- Garantir que a alteração foi testada na interface e no backend.
- Esta diretiva visa evitar retrabalho e garantir que as validações estejam centralizadas e alinhadas com as regras de negócio atuais do projeto.

## 17. Rotas e Funcionalidades Pendentes
- Sempre que uma funcionalidade, rota ou view ainda não estiver implementada, os templates devem:
  - Utilizar `href="#"` ou um botão desabilitado (`disabled`) para indicar que a ação está indisponível.
  - Nunca usar `{% url ... %}` para rotas que não existem, evitando erros de execução.
  - Opcionalmente, adicionar um comentário ou texto "em breve" para informar o usuário.
  - Comentar ou remover qualquer referência a rotas inexistentes no código.
- Objetivo: Evitar erros de navegação, garantir clareza para o usuário e facilitar a manutenção do sistema.

## 18. Templates de Listas
- Todos os templates de listas do projeto devem priorizar a seguinte implementação:
  1. Utilizar o recurso `{% render_table table %}` do django-tables2 para renderização automática das tabelas, aproveitando ordenação, paginação e responsividade.
  2. Integrar filtros visuais usando django-filter, exibindo o formulário de filtro acima da tabela, preferencialmente com o padrão `{{ filter.form.as_p }}` ou `as_crispy_field`.
  3. Garantir paginação nativa, seja pelo django-tables2 ou pelo próprio ListView, sempre exibindo controles de navegação de página.
  4. O layout deve ser responsivo, limpo e seguir o padrão visual do projeto (Bootstrap 5).
  5. O nome da empresa ou contexto principal deve ser exibido no topo da página.
- Essa diretriz garante padronização, usabilidade e manutenção facilitada em todas as listas do sistema.

## 19. Fluxo para Sidebar Cadastro
- O fluxo padrão para menus de cadastro no sidebar segue as etapas abaixo:
  1. Acesso ao menu: O usuário acessa o menu de cadastro desejado pelo sidebar.
  2. Listagem: É exibida uma página com a lista dos registros já cadastrados, com filtros e paginação.
  3. Novo cadastro: O usuário clica em "Novo" para abrir o formulário de cadastro.
  4. Formulário: O formulário apresenta os campos necessários. O usuário pode salvar ou cancelar.
  5. Salvar: Ao salvar, o registro é criado e o usuário retorna para a lista.
  6. Cancelar: Ao cancelar, o usuário retorna para a lista sem salvar alterações.
  7. Edição/Exclusão: Na lista, o usuário pode editar ou excluir registros existentes.
- Esse padrão garante navegação intuitiva, consistência visual e facilidade de uso em todos os cadastros do sistema.

## 20. Navegação - Barra de Menu Superior
- A barra de menu superior é um componente horizontal fixo no topo do sistema, responsável por centralizar a navegação principal do aplicativo. Ela deve:
  - Exibir o logotipo ou nome do sistema à esquerda, funcionando como link para a página inicial.
  - Exibir, à direita, a área do usuário autenticado (e-mail/nome) e o botão de login/logout, ambos com ícones.
  - Manter fundo escuro e texto claro, seguindo o padrão visual do tema escuro do sistema.
  - Ser responsiva, mantendo a disposição horizontal dos itens em telas grandes e adaptando para dispositivos móveis se necessário.

## 21. Seleção de Empresa no Dashboard
- A caixa de seleção de empresa no dashboard permite ao usuário escolher, entre as empresas disponíveis para sua conta, qual será a empresa “ativa” no contexto da navegação e das operações do sistema.
- O select exibe todas as empresas vinculadas à conta do usuário autenticado (ou às contas em que ele possui permissão via `ContaMembership`).
- Ao selecionar uma empresa e submeter o formulário, o sistema salva o `empresa_id` escolhido na sessão do usuário (`request.session['empresa_id']`).
- A empresa selecionada passa a ser usada como referência para todas as operações, filtros e visualizações do sistema, garantindo o isolamento multi-tenant.
- Sempre que o usuário acessar o dashboard, a empresa atualmente selecionada será destacada no select.
- Se o usuário não tiver selecionado nenhuma, a primeira empresa disponível será automaticamente definida como ativa.
- O sistema só exibe empresas para as quais o usuário tem permissão, evitando acesso indevido a dados de outras contas.

---

Este documento deve ser revisado e atualizado sempre que novas práticas ou padrões forem definidos para o projeto.
