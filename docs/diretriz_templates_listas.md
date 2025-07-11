# Diretriz de Interface para Templates de Listas

Todos os templates de listas do projeto devem priorizar a seguinte implementação:

1. Utilizar o recurso `{% render_table table %}` do django-tables2 para renderização automática das tabelas, aproveitando ordenação, paginação e responsividade.
2. Integrar filtros visuais usando django-filter, exibindo o formulário de filtro acima da tabela, preferencialmente com o padrão `{{ filter.form.as_p }}` ou `as_crispy_field`.
3. Garantir paginação nativa, seja pelo django-tables2 ou pelo próprio ListView, sempre exibindo controles de navegação de página.
4. O layout deve ser responsivo, limpo e seguir o padrão visual do projeto (Bootstrap 5).
5. O nome da empresa ou contexto principal deve ser exibido no topo da página.

Exemplo mínimo:
```django
{% extends 'layouts/base_cenario_cadastro.html' %}
{% load render_table from django_tables2 %}
{% block content %}
  <form method="get">{{ filter.form.as_p }}<button type="submit">Filtrar</button></form>
  {% render_table table %}
{% endblock %}
```

Essa diretriz garante padronização, usabilidade e manutenção facilitada em todas as listas do sistema.
