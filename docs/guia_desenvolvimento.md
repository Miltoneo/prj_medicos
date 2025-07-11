# Diretriz para Views Django

Sempre utilize Class-Based Views (CBV) para implementar fluxos CRUD em módulos do sistema, exceto em casos justificados e documentados. CBVs garantem padronização, melhor reutilização de código, facilidade de manutenção e integração com recursos nativos do Django. Antes de criar uma view baseada em função (FBV), verifique se não há impedimentos técnicos ou de negócio e registre a justificativa no código e na documentação do projeto.

## Diretriz para Links Quebrados em Templates

Sempre que existirem links quebrados (rotas, URLs ou views ainda não implementadas) nos templates, estes deverão ser temporariamente substituídos por `#`. Isso evita erros de navegação e garante que o layout seja exibido corretamente até que as rotas estejam disponíveis.

- Utilize `href="#"` para itens de menu, botões ou links que ainda não possuem destino funcional.
- Documente a substituição e revise periodicamente para atualizar os links assim que as rotas forem implementadas.
- Essa prática deve ser seguida em todos os cenários e módulos do sistema.
