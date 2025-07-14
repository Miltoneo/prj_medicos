# Regra de Desenvolvimento: Padronização de Rotas Django

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
