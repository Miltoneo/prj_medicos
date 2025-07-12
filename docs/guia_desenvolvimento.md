# Diretriz para Views Django

Sempre utilize Class-Based Views (CBV) para implementar fluxos CRUD em módulos do sistema, exceto em casos justificados e documentados. CBVs garantem padronização, melhor reutilização de código, facilidade de manutenção e integração com recursos nativos do Django. Antes de criar uma view baseada em função (FBV), verifique se não há impedimentos técnicos ou de negócio e registre a justificativa no código e na documentação do projeto.


## Diretriz para Data de Competência Compartilhada

Todos os cenários do sistema devem compartilhar a data de competência (mês/ano) selecionada pelo usuário. Esta data deve ser persistida na sessão do usuário e utilizada como padrão em todos os menus, páginas e funcionalidades que dependam de competência temporal.

- O campo de competência deve ser exibido no cabeçalho dos cenários principais.
- Ao alterar manualmente a competência, o novo valor deve ser salvo na sessão e mantido ao navegar entre diferentes cenários.
- O valor inicial deve ser o mês/ano atual, salvo na sessão na primeira navegação.
- Views e templates devem acessar `request.session['mes_ano']` para garantir sincronização.
- Essa regra garante consistência de contexto temporal para o usuário em todo o sistema.
