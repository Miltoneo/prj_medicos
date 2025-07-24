## 13. Padrão de Dropdown Filtrável Multi-tenant (Select2)

**Atenção:** Dropdowns e interfaces de despesas servem para apropriação e controle gerencial. Não utilize despesas como base de cálculo de impostos, exceto para ISS em casos previstos em lei municipal. Para apuração de ISS, PIS, COFINS, IRPJ e CSLL, utilize exclusivamente os dados das notas fiscais conforme documentação tributária.

Sempre que implementar dropdowns para seleção de itens em contexto multi-tenant (ex: despesas de empresa ou sócio), siga o padrão abaixo:

- O campo deve ser renderizado via ModelForm, já filtrado conforme o contexto de negócio (empresa ativa, rateio, etc).
- Utilize o widget Select2 para busca dinâmica, filtragem por texto, seleção clara e largura responsiva.
- Inicialize o Select2 no template:
  ```js
  $('#id_item_despesa').select2({
    placeholder: "Selecione ou digite para filtrar...",
    allowClear: true,
    width: '100%',
    minimumInputLength: 1
  });
  ```
- Garanta contraste e legibilidade dos itens com estilos customizados:
  ```css
  .select2-container--default .select2-results__option {
    color: #212529;
    background-color: #fff;
  }
  .select2-container--default .select2-selection__rendered {
    color: #212529;
  }
  ```
- Exiba erros de validação logo abaixo do campo.
- O filtro dos itens deve ser feito no ModelForm, nunca apenas no frontend.
- Carregue os assets JS/CSS do Select2 e jQuery no template.
- Exemplo de template:
  ```django
  <div style="max-width: 500px; min-width: 300px;">
    {{ form.item_despesa }}
  </div>
  {% if form.item_despesa.errors %}<div class="text-danger small">{{ form.item_despesa.errors }}</div>{% endif %}
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
  <script>
    $(document).ready(function() {
      $('#id_item_despesa').select2({
        placeholder: "Selecione ou digite para filtrar...",
        allowClear: true,
        width: '100%',
        minimumInputLength: 1
      });
    });
  </script>
  <style>
    .select2-container--default .select2-results__option {
      color: #212529;
      background-color: #fff;
    }
    .select2-container--default .select2-selection__rendered {
      color: #212529;
    }
  </style>
  ```
- O template deve ser único para inclusão e edição, recebendo variáveis de contexto como título, texto do botão e url de cancelamento.

Esse padrão garante dropdowns filtrados, acessíveis, responsivos e consistentes com as regras multi-tenant do projeto.
## Dropdowns filtráveis com digitação livre

Sempre que implementar um dropdown para seleção de itens em contexto multi-tenant, utilize widgets que permitam busca dinâmica (AJAX) e digitação direta na caixa de seleção (autocomplete) para filtrar os resultados.

Padrão recomendado:
- O campo de seleção deve permitir digitação direta (input embutido), servindo tanto para busca quanto para seleção.
- O campo inicia vazio ou com placeholder orientando a digitação.
- A cada caractere digitado, o frontend dispara requisição AJAX ao backend, enviando o termo de busca e parâmetros de contexto (ex: empresa_id).
- O backend retorna apenas os itens que correspondem ao termo digitado e aos filtros de negócio (ex: empresa ativa, tipo_rateio=COM_RATEIO).
- O dropdown exibe apenas os resultados filtrados, reduzindo a lista conforme o usuário digita.
- Se permitido (`data-tags: 'true'`), o usuário pode criar um novo valor digitando, além de selecionar itens existentes.
- O valor final é validado conforme as regras do modelo.

Referências de padrões de usabilidade:
- Select2: https://select2.org/getting-started/basic-usage
- Material Design Autocomplete: https://m3.material.io/components/autocomplete/overview
- Ant Design Select: https://ant.design/components/select/#components-select-demo-search
- Bootstrap Select: https://developer.snapappointments.com/bootstrap-select/examples/#live-search

Esse padrão garante eficiência, usabilidade, filtragem contextual e respeito às regras de negócio multi-tenant.
## 12. Campos de Seleção com Busca/Filtro (Dropdowns)
- Sempre utilize widgets ou componentes padronizados do Django para campos de seleção com busca/filtro (ex: Select2).
- Recomenda-se o uso de bibliotecas como `django-select2` ou widgets customizados integrados ao formulário.
- É proibido implementar filtros de busca em dropdowns via scripts manuais diretamente no template.
- Motivo: garantir manutenção, compatibilidade, rastreabilidade e reaproveitamento em todo o projeto.
- Referência: https://django-select2.readthedocs.io/en/latest/

Padrão obrigatório para usabilidade:
- O campo de seleção deve permitir digitação direta (autocomplete/input embutido), disparando busca dinâmica conforme o usuário digita.
- O dropdown exibe apenas os resultados filtrados, facilitando a escolha e evitando sobrecarga visual.
- O valor digitado ou selecionado deve ser validado conforme as regras do modelo.

# Guia de Desenvolvimento – prj_medicos

> Para regras comportamentais, exemplos de resposta, rastreabilidade e busca detalhada, consulte exclusivamente `.github/copilot-instructions.md`.

Este arquivo foca apenas em padrões técnicos, arquitetura, modularização, templates, URLs, contexto, nomenclatura, views, segurança, UI/UX e automação.

## 1. Templates Django
- Sempre utilize o bloco `{% block content %}` nos templates filhos.
- Não utilize blocos personalizados como `{% block conteudo_cadastro %}`.
- Exemplo correto:
  ```django
  {% extends 'layouts/base_cenario_cadastro.html' %}
  {% block content %}
  <!-- Conteúdo da tela aqui -->
  {% endblock %}
  ```
- O nome do template deve iniciar com o nome do fluxo, seguido do contexto funcional, separados por underline.
- Exemplo de nomenclatura de arquivos para o fluxo de despesas de sócio:
  ```
  despesas/despesas_socio_lista.html
  despesas/despesas_socio_form.html
  despesas/despesas_socio_confirm_delete.html
  ```
- Exemplo incorreto:
  ```django
  {% block conteudo_cadastro %}
  <!-- Não utilize blocos personalizados! -->
  {% endblock %}
  ```
- Fonte: docs/guia_desenvolvimento.md, linhas 1-18

## 2. URLs Django
- O início do path deve ser igual ao início do name, ambos em snake_case.
- Para rotas de listagem, use o prefixo `lista_` tanto no path quanto no name.
- O path deve ser direto, descritivo e sem redundâncias.
- Sempre inclua `empresa_id` em endpoints que dependem de contexto de empresa.
- Exemplo correto:
  ```python
  path('lista_itens_despesa/<int:empresa_id>/', views_despesa.ItemDespesaListView.as_view(), name='lista_itens_despesa')
  ```
- Exemplo incorreto:
  ```python
  path('itens_despesa/', ..., name='lista_itens_despesa')  # ERRADO
  ```
- Fonte: docs/guia_desenvolvimento.md, linhas 19-49

## 3. Contexto Global, Header e Título
- Utilize context processors para variáveis globais como `empresa`, `conta`, `usuario_atual`.
- Nunca busque manualmente em `request.session` ou faça queries diretas nas views para obter instâncias globais.
- O parâmetro `empresa_id` deve ser mantido na URL das views para garantir escopo explícito da empresa.

## 4. Código, Nomenclatura e Formatação
- Os imports devem SEMPRE ser inseridos e agrupados no topo do arquivo, organizados por grupos: padrão Python, terceiros, depois do próprio projeto.
- É proibido adicionar imports dentro de funções ou blocos de código. Sempre siga este padrão para garantir rastreabilidade e manutenção.
- Funções e classes organizadas por ordem lógica.
- Funções de view recebem `request` como primeiro argumento.
- Contexto para templates deve ser passado como dicionário.
- Use decorators acima das views.
- Nomes de funções e variáveis em inglês, exceto quando o projeto exigir o contrário.
- Indentação de 4 espaços.
- Modelos: PascalCase; campos: snake_case; constantes: UPPER_SNAKE_CASE.
- Elimine aliases legacy e padronize nomenclaturas.
- Atualize referências em arquivos relacionados quando necessário.
- Teste todas as alterações em ambiente de desenvolvimento.
- Mantenha compatibilidade com Django 4.x.
- Documente breaking changes quando necessário.
- Mantenha `requirements.txt` atualizado.
- Corrija e padronize a formatação antes de finalizar alterações.

## 5. Código como Fonte da Verdade
- O código hardcoded é sempre a referência absoluta para documentação.
- Nunca gere documentação baseada em versões anteriores ou memória.
- Toda documentação deve ser regenerada a partir do código atual.

## 6. Arquitetura e Modularização
- Mantenha separação clara entre módulos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`.
- Respeite isolamento multi-tenant através do modelo `Conta`.
- Preserve hierarquia de relacionamentos e constraints.
- Não crie dependências circulares entre módulos.
- Mantenha modelos simples, focados e com responsabilidade única.

## 7. Views de Lista: CRUD, Tables, Filtros e Paginação
- Views de listagem devem implementar CRUD completo usando CBVs do Django.
- Utilize django-tables2 para exibição dos dados.
- Implemente filtros com django-filter ou equivalente.
- Inclua paginação em todas as listagens.
- Integre o CRUD à navegação da tabela.
- Siga o padrão visual do projeto.
- Documente e aprove exceções em revisão de código.
- Fonte: docs/guia_desenvolvimento.md, linhas 132-150

## 8. Validação e Revisão
- Sempre revise e, se necessário, remova ou ajuste validações duplicadas ou conflitantes.
- Garanta que a alteração foi testada na interface e no backend.
- Fonte: docs/guia_desenvolvimento.md, linhas 152-155

## 9. Segurança, Auditoria e UI/UX
- Mantenha isolamento de dados por tenant.
- Preserve rastreamento de IP e user-agent.
- Implemente controles de acesso granulares.
- Implemente validações client-side quando apropriado.
- Mantenha responsividade para dispositivos móveis.
- Mudanças de layout e estilo devem ser centralizadas.
- O menu deve destacar a página ativa e exibir informações do usuário autenticado.
- Menus laterais são indicados para sistemas com múltiplas áreas.
- O menu ativo deve ser destacado visualmente.
- Evite menus excessivamente profundos ou complexos.
- Templates devem indicar rotas/funcionalidades pendentes com `href="#"` ou botão desabilitado.
- Fonte: docs/guia_desenvolvimento.md, linhas 157-180

## 10. Padronização de Rotas Django
- O parâmetro `name` deve ser semanticamente alinhado ao parâmetro `path`, usando snake_case.
- Evite nomes diferentes entre path e rota.
- Exemplo correto:
  ```python
  path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='empresas')
  path('rateio/<int:nota_id>/', ..., name='rateio_nota')
  path('usuarios/', ..., name='usuarios')
  path('usuarios/<int:user_id>/', ..., name='usuario_detalhe')
  ```
- Exemplo errado:
  ```python
  path('empresas/<int:empresa_id>/', views.dashboard_empresa, name='startempresa')
  ```
- Fonte: docs/guia_desenvolvimento.md, linhas 182-200

## 11. Automação e Comportamento do Copilot
- Para remover fisicamente um arquivo, execute o comando de exclusão diretamente no terminal.
- Exemplo para Windows:
  ```
  del "caminho/do/arquivo.ext"
  ```
- Exemplo para Linux/Mac:
  ```
  rm caminho/do/arquivo.ext
  ```
- Fonte: docs/guia_desenvolvimento.md, linhas 202-215

---

Este arquivo foi gerado a partir de docs/guia_desenvolvimento.md para servir como referência rápida e operacional para agentes e desenvolvedores.
