# Padronização de Título de Páginas
## Regra obrigatória: Título da página

O título da página deve ser exibido exclusivamente pelo header base do sistema (template base/layout). Não é permitido incluir o título manualmente em templates filhos, evitando duplicidade e garantindo consistência visual. Caso o título seja incluído em um template filho, ele deve ser removido imediatamente.

Essa regra reforça a padronização e centralização do layout, facilitando manutenção e evolução visual do sistema.

Todas as páginas do sistema devem exibir o título no topo do conteúdo principal, conforme o padrão:

- O título é exibido em um elemento `<h4>` com as classes Bootstrap `fw-bold text-primary`.
- O texto segue o formato: `Título: [nome da página]`.
- O nome da página é definido pela variável de contexto `titulo_pagina` em cada view.
- Caso a variável não esteja definida, será exibido automaticamente o texto `Título: erro`.
- Este padrão deve ser aplicado em todos os templates base do projeto.

Exemplo no template base:
```django
<div class="mb-3">
  <h4 class="fw-bold text-primary">Título: {{ titulo_pagina|default:'erro' }}</h4>
</div>
```

Exemplo de definição na view:
```python
context['titulo_pagina'] = 'Cadastro de Médicos'
```

Essa regra garante consistência visual e semântica em todas as telas do sistema.
# Regras de Desenvolvimento (migradas de praticas_e_padroes.md)

## Formatação de Views Django
Todas as views devem seguir o padrão de formatação Django:
- Imports organizados no topo do arquivo, separados por grupos: padrão Python, terceiros, depois do próprio projeto.
- Funções e classes organizadas por ordem lógica (helpers, views, etc), com uma linha de espaço entre elas.
- Funções de view recebem `request` como primeiro argumento.
- Contexto para templates deve ser passado como dicionário.
- Uso de decorators (`@login_required`, etc) acima das views.
- Nomes de funções e variáveis em inglês, exceto quando o projeto exigir o contrário.
- Indentação de 4 espaços.

## Código como Fonte da Verdade
- O código hardcoded é SEMPRE a referência absoluta para documentação.
- Nunca gerar documentação baseada em versões anteriores ou memória.
- Toda documentação deve ser regenerada a partir do código atual.
- Eliminar aliases legacy e padronizar nomenclaturas conforme código real.
- Validar sempre que documentação reflete exatamente o estado do código.

## Arquitetura e Modularização
- Manter separação clara entre módulos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`.
- Respeitar isolamento multi-tenant através do modelo `Conta`.
- Preservar hierarquia de relacionamentos e constraints definidas no código.
- Não criar dependências circulares entre módulos.
- Manter modelos simples, focados e com responsabilidade única.

## Nomenclatura e Padrões
- Modelos: PascalCase exato conforme definido no código.
- Campos: snake_case conforme implementação atual.
- Constantes: UPPER_SNAKE_CASE conforme padrões Django.
- Eliminar aliases de compatibilidade quando não utilizados.
- Manter consistência de nomes em todo o projeto.
- Atualizar referências em `admin.py`, `forms.py`, `views.py`, `tables.py` quando necessário.

## Desenvolvimento e Manutenção
- Testar todas as alterações em ambiente de desenvolvimento.
- Manter compatibilidade com Django 4.x.
- Preservar funcionalidades existentes ao fazer refatorações.
- Documentar breaking changes quando necessário.
- Manter requirements.txt atualizado.
- Otimizar queries com base em padrões de uso reais.
- Implementar paginação em listagens grandes.

## Segurança e Auditoria
- Manter isolamento de dados por tenant (Conta).
- Preservar rastreamento de IP e user-agent.
- Implementar controles de acesso granulares.
- Implementar validações client-side quando apropriado.
- Manter responsividade para dispositivos móveis.
- Mudanças de layout e estilo devem ser aplicadas de forma centralizada, facilitando manutenção e evolução visual.
- A padronização deve priorizar clareza, legibilidade e responsividade.
- O menu deve destacar a página ativa e exibir informações do usuário autenticado quando aplicável.
- Melhorias de usabilidade e acessibilidade devem ser priorizadas em toda evolução do menu.

## Melhores Práticas para Menus de Navegação
- Menus laterais (sidebar) são indicados para sistemas com múltiplas áreas, módulos ou funcionalidades agrupadas.
- O menu ativo deve ser destacado visualmente para orientar o usuário.
- Evitar menus excessivamente profundos ou complexos; priorizar clareza e rapidez de acesso.
- A escolha entre menu lateral ou topo deve considerar o perfil do usuário, quantidade de funcionalidades e contexto de uso.

## Views Django

## Revisão de Métodos de Validação
- Sempre revisar e, se necessário, remover ou ajustar validações duplicadas ou conflitantes tanto no formulário quanto no modelo.
- Garantir que a alteração foi testada na interface e no backend.
- Esta diretiva visa evitar retrabalho e garantir que as validações estejam centralizadas e alinhadas com as regras de negócio atuais do projeto.

# Regra de CRUD em Views de Lista

Toda view de lista deve obrigatoriamente incluir a implementação completa de CRUD (Create, Read, Update, Delete) utilizando Class-Based Views (CBV) do Django. Isso garante padronização, facilidade de manutenção e evolução do sistema.

Exemplo:
- Para cada model listado, devem existir views para criação, edição, exclusão e visualização detalhada, além da listagem.
- Os templates devem ser organizados por operação (`lista`, `form`, `confirm_delete`, etc).
- As rotas devem ser padronizadas e documentadas.

# Regras Gerais do Projeto

- Sempre que modificar um arquivo, corrija e padronize a formatação antes de finalizar a alteração.
    - Organize imports por categoria (Django, terceiros, local).
    - Remova duplicidades e imports não utilizados.
    - Mantenha espaçamento e indentação consistente.
    - Agrupe classes e funções relacionadas.
    - Garanta legibilidade e clareza do código.

Outras regras podem ser adicionadas conforme o projeto evoluir.
# Regras Gerais de Desenvolvimento

- Sempre que modificar um arquivo, corrija e padronize a formatação antes de finalizar a alteração.
    - Organize imports por categoria (Django, terceiros, local).
    - Remova duplicidades e imports não utilizados.
    - Mantenha espaçamento e indentação consistente.
    - Agrupe classes e funções relacionadas.
    - Garanta legibilidade e clareza do código.

Outras regras podem ser adicionadas conforme o projeto evoluir.
# Regra de Comportamento do Copilot

Sempre que for necessário remover fisicamente um arquivo do projeto, o Copilot deve executar o comando de exclusão diretamente no terminal Copilot, garantindo que a remoção seja efetiva no sistema de arquivos e não apenas lógica ou documental.

Exemplo:
Para remover um arquivo no Windows:
```
del "caminho/do/arquivo.ext"
```
Para remover um arquivo no Linux/Mac:
```
rm caminho/do/arquivo.ext
```
# Padronização de Rotas Django

## Objetivo
Evitar confusão e garantir clareza na navegação e manutenção do projeto.

## Regra
Sempre que definir uma rota no Django, o nome da rota (`name`) deve refletir o path da URL. Ou seja:
- Se o path é `empresas/<int:empresa_id>/`, o nome da rota deve ser `empresas`.
- Se o path é `startempresa/<int:empresa_id>/`, o nome da rota deve ser `startempresa`.

## Justificativa
- Facilita o uso do `{% url 'namespace:rota' %}` em templates e código Python.
- Evita ambiguidades e erros de reversão de URL.
- Torna o projeto mais intuitivo para novos desenvolvedores.

## Exemplo
```python
# Correto:
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='empresas')

# Errado:
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='startempresa')
```

## Aplicação
- Sempre revise e padronize as rotas ao criar ou modificar URLs.
- Documente esta regra em todos os projetos Django.
# Regras Gerais e de Negócio

- Templates devem indicar rotas/funcionalidades pendentes com `href="#"` ou botão desabilitado.
- Sempre revisar e atualizar este documento quando novas regras de negócio ou fluxos específicos forem implementados no projeto.


# Padronização de Rotas Django

## Objetivo
Evitar confusão e garantir clareza na navegação e manutenção do projeto.

## Regra
Sempre que definir uma rota no Django, o nome da rota (`name`) deve refletir o path da URL, usando snake_case e alinhamento semântico. Ou seja:
- Se o path é `empresas/<int:empresa_id>/`, o nome da rota deve ser `empresas`.
- Se o path é `startempresa/<int:empresa_id>/`, o nome da rota deve ser `startempresa`.
- O valor do parâmetro `path` deve ser igual ao valor do parâmetro `name` (exceto por barras e snake_case), garantindo alinhamento total e previsibilidade.

## Justificativa
- Facilita o uso do `{% url 'namespace:rota' %}` em templates e código Python.
- Evita ambiguidades e erros de reversão de URL.
- Torna o projeto mais intuitivo para novos desenvolvedores.

## Exemplos
```python
# Correto:
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='empresas')
path('lista_notas_rateio/', view, name='lista_notas_rateio')
path('rateio/', ..., name='rateio')
path('rateio/<int:nota_id>/', ..., name='rateio_nota')
path('usuarios/', ..., name='usuarios')
path('usuarios/<int:user_id>/', ..., name='usuario_detalhe')

# Errado:
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='startempresa')
```

## Diretrizes
- O valor de `name` deve ser o mais próximo possível do path, usando snake_case.
- Evite nomes genéricos ou duplicados.
- Sempre revise se o path e o name estão alinhados antes de aprovar um PR.
- Documente esta regra em todos os projetos Django.
Facilita a manutenção, o uso do reverse e a padronização do projeto.
# Padrão para Rotas Django: Alinhamento entre path e name

**Regra:**
Para todas as rotas Django, o parâmetro `path` e o parâmetro `name` devem ser semanticamente alinhados, seguindo o mesmo padrão de nomenclatura, para garantir clareza, previsibilidade e padronização em todo o projeto.

**Exemplo:**
```python
path('rateio/', ..., name='rateio')
path('rateio/<int:nota_id>/', ..., name='rateio_nota')
path('usuarios/', ..., name='usuarios')
path('usuarios/<int:user_id>/', ..., name='usuario_detalhe')
```

**Diretrizes:**
- O valor de `name` deve ser o mais próximo possível do path, usando snake_case.
- Evite nomes genéricos ou duplicados.
- Sempre revise se o path e o name estão alinhados antes de aprovar um PR.

**Motivação:**
Essa padronização facilita o uso do `{% url %}` nos templates, a manutenção do código e a navegação entre as rotas do projeto.
# Guia de Desenvolvimento

## Padronização de Rotas Django

### Regra

**Regra:** O nome da rota (`name`) deve ser igual ao segmento principal do path da URL.

Ou seja:
- Se o path é `empresas/<int:empresa_id>/`, o nome da rota deve ser `empresas`.
- Se o path é `startempresa/<int:empresa_id>/`, o nome da rota deve ser `startempresa`.

Evite nomes diferentes entre path e rota, pois isso dificulta manutenção e entendimento do código.

### Justificativa
- Facilita o uso do `{% url 'namespace:rota' %}` em templates e código Python.
- Evita ambiguidades e erros de reversão de URL.
- Torna o projeto mais intuitivo para novos desenvolvedores.

### Exemplo
```python
# Correto:
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='empresas')

# Errado:
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='startempresa')
```

### Aplicação
- Sempre revise e padronize as rotas ao criar ou modificar URLs.
- Documente esta regra em todos os projetos Django.
