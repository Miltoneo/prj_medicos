# Diretiva de Interface: Rotas e Funcionalidades Pendentes

Sempre que uma funcionalidade, rota ou view ainda não estiver implementada, os templates devem:

- Utilizar `href="#"` ou um botão desabilitado (`disabled`) para indicar que a ação está indisponível.
- Nunca usar `{% url ... %}` para rotas que não existem, evitando erros de execução.
- Opcionalmente, adicionar um comentário ou texto "em breve" para informar o usuário.
- Comentar ou remover qualquer referência a rotas inexistentes no código.

**Exemplo:**
```django
<a href="#" class="btn btn-secondary disabled">Convidar Usuário (em breve)</a>
{# <a href="{% url 'medicos:user_invite' %}">Convidar Usuário</a> #}
```

**Objetivo:**
Evitar erros de navegação, garantir clareza para o usuário e facilitar a manutenção do sistema.
