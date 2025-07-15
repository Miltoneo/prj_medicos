# Regra: O path deve ser igual ao nome da rota

Para todas as rotas Django, o valor do parâmetro `path` deve ser igual ao valor do parâmetro `name` (exceto por barras e snake_case), garantindo alinhamento total e previsibilidade.

**Exemplo:**
```python
path('lista_notas_rateio/', view, name='lista_notas_rateio')
path('usuarios/', view, name='usuarios')
```

**Motivação:**
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
