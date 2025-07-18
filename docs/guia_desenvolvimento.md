

# Guia de Desenvolvimento: Regras e Padrões do Projeto

## 1. Contexto Global, Header e Título (Obrigatório)

- Sempre utilize context processors para variáveis globais como `empresa`, `conta`, `usuario_atual`, etc. Nunca busque manualmente em `request.session` ou faça queries diretas nas views para obter instâncias globais.
- Toda lógica de obtenção, validação e fallback dessas instâncias deve estar centralizada no context processor correspondente.
- Se a variável não estiver disponível ou for `None`, o context processor deve tratar o erro e exibir mensagem apropriada.
- O parâmetro `empresa_id` deve ser mantido na URL das views para garantir navegação RESTful e escopo explícito da empresa (multi-tenant).
- Sempre sobrescreva `get_context_data(self, **kwargs)` em CBVs para adicionar variáveis específicas da página (ex: `titulo_pagina`, filtros, listas), chamando `super().get_context_data(**kwargs)`.
- Defina a variável `titulo_pagina` no contexto para exibição padronizada do título no header.
- O cabeçalho padrão deve ser incluído via `{% include 'layouts/base_header.html' %}` e o título exibido exclusivamente pelo header base do sistema, usando a variável `titulo_pagina`.
- É terminantemente proibido definir títulos de página manualmente em templates filhos. O título deve ser sempre passado pela variável `titulo_pagina` no contexto da view e exibido exclusivamente pelo header do template base. Qualquer ocorrência de `<h4 class="fw-bold text-primary">` ou similar fora do layout base deve ser considerada erro de padronização e corrigida imediatamente.

**Exemplo de uso em view:**
```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['titulo_pagina'] = 'Lançamentos'
    self.request.session['cenario_nome'] = 'Financeiro'
    return context
```
**Exemplo de context processor:**
```python
def empresa_context(request):
    # ...código para obter empresa...
    return {
        'empresa': empresa,
        # ...outros itens do contexto global...
    }
```
**Exemplo no template base:**
```django
<h4 class="fw-bold text-primary">Título: {{ titulo_pagina|default:'erro' }}</h4>
{% include 'layouts/base_header.html' %}
```

---

## 2. Código, Nomenclatura e Formatação

- Imports organizados no topo do arquivo, separados por grupos: padrão Python, terceiros, depois do próprio projeto.
- Funções e classes organizadas por ordem lógica (helpers, views, etc), com uma linha de espaço entre elas.
- Funções de view recebem `request` como primeiro argumento.
- Contexto para templates deve ser passado como dicionário.
- Uso de decorators (`@login_required`, etc) acima das views.
- Nomes de funções e variáveis em inglês, exceto quando o projeto exigir o contrário.
- Indentação de 4 espaços.
- Modelos: PascalCase; campos: snake_case; constantes: UPPER_SNAKE_CASE.
- Elimine aliases legacy e padronize nomenclaturas conforme código real.
- Atualize referências em `admin.py`, `forms.py`, `views.py`, `tables.py` quando necessário.
- Teste todas as alterações em ambiente de desenvolvimento.
- Mantenha compatibilidade com Django 4.x.
- Documente breaking changes quando necessário.
- Mantenha `requirements.txt` atualizado.
- Sempre que modificar um arquivo, corrija e padronize a formatação antes de finalizar a alteração.
    - Organize imports por categoria (Django, terceiros, local).
    - Remova duplicidades e imports não utilizados.
    - Mantenha espaçamento e indentação consistente.
    - Agrupe classes e funções relacionadas.
    - Garanta legibilidade e clareza do código.

## 3. Código como Fonte da Verdade

- O código hardcoded é SEMPRE a referência absoluta para documentação.
- Nunca gere documentação baseada em versões anteriores ou memória.
- Toda documentação deve ser regenerada a partir do código atual.
- Valide sempre que a documentação reflete exatamente o estado do código.

## 4. Arquitetura e Modularização

- Mantenha separação clara entre módulos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`.
- Respeite isolamento multi-tenant através do modelo `Conta`.
- Preserve hierarquia de relacionamentos e constraints definidas no código.
- Não crie dependências circulares entre módulos.
- Mantenha modelos simples, focados e com responsabilidade única.

## 5. Views de Lista: CRUD, Tables, Filtros e Paginação (Regra Obrigatória)

Todas as views de listagem devem obrigatoriamente:
- Implementar CRUD completo (Create, Read, Update, Delete) usando Class-Based Views (CBV) do Django.
- Utilizar tables (preferencialmente com django-tables2) para exibição dos dados, exceto dashboards ou visualizações específicas justificadas na documentação.
- Implementar filtros para todos os campos relevantes, utilizando django-filter ou solução equivalente.
- Incluir paginação em todas as listagens com potencial de crescimento.
- Integrar o CRUD à navegação da tabela.
- Seguir o padrão visual do projeto, com responsividade e clareza.
- Documentar e aprovar em revisão de código qualquer exceção a essas regras.

**Stack recomendada:** django-tables2, django-filter, paginação nativa do Django ou equivalente.

Essas regras garantem padronização de UI/UX, facilitam manutenção e asseguram experiência consistente ao usuário.

## 6. Validação e Revisão

- Sempre revise e, se necessário, remova ou ajuste validações duplicadas ou conflitantes tanto no formulário quanto no modelo.
- Garanta que a alteração foi testada na interface e no backend.

## 7. Segurança, Auditoria e UI/UX

- Mantenha isolamento de dados por tenant (Conta).
- Preserve rastreamento de IP e user-agent.
- Implemente controles de acesso granulares.
- Implemente validações client-side quando apropriado.
- Mantenha responsividade para dispositivos móveis.
- Mudanças de layout e estilo devem ser aplicadas de forma centralizada.
- A padronização deve priorizar clareza, legibilidade e responsividade.
- O menu deve destacar a página ativa e exibir informações do usuário autenticado quando aplicável.
- Melhorias de usabilidade e acessibilidade devem ser priorizadas em toda evolução do menu.
- Menus laterais (sidebar) são indicados para sistemas com múltiplas áreas, módulos ou funcionalidades agrupadas.
- O menu ativo deve ser destacado visualmente para orientar o usuário.
- Evite menus excessivamente profundos ou complexos; priorize clareza e rapidez de acesso.
- A escolha entre menu lateral ou topo deve considerar o perfil do usuário, quantidade de funcionalidades e contexto de uso.
- Templates devem indicar rotas/funcionalidades pendentes com `href="#"` ou botão desabilitado.

## 8. Padronização de Rotas Django (Regra Obrigatória)

Sempre que definir uma rota no Django, o parâmetro `name` deve ser semanticamente alinhado ao parâmetro `path`, usando snake_case e refletindo o segmento principal da URL. Evite nomes diferentes entre path e rota.

**Exemplo correto:**
```python
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='empresas')
path('rateio/<int:nota_id>/', ..., name='rateio_nota')
path('usuarios/', ..., name='usuarios')
path('usuarios/<int:user_id>/', ..., name='usuario_detalhe')
```
**Exemplo errado:**
```python
path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='startempresa')
```

**Diretrizes:**
- O valor de `name` deve ser o mais próximo possível do path, usando snake_case.
- Evite nomes genéricos ou duplicados.
- Sempre revise se o path e o name estão alinhados antes de aprovar um PR.
- Documente esta regra em todos os projetos Django.

Essa padronização facilita o uso do `{% url %}` nos templates, a manutenção do código e a navegação entre as rotas do projeto.

## 9. Automação e Comportamento do Copilot

Sempre que for necessário remover fisicamente um arquivo do projeto, o Copilot deve executar o comando de exclusão diretamente no terminal Copilot, garantindo que a remoção seja efetiva no sistema de arquivos e não apenas lógica ou documental.

**Exemplo:**
Para remover um arquivo no Windows:
```
del "caminho/do/arquivo.ext"
```
Para remover um arquivo no Linux/Mac:
```
rm caminho/do/arquivo.ext
```

---
Outras regras podem ser adicionadas conforme o projeto evoluir.
