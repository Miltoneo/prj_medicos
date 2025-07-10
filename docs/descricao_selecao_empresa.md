# Funcionamento da Caixa de Seleção de Empresa no Dashboard

A caixa de seleção de empresa no dashboard permite ao usuário escolher, entre as empresas disponíveis para sua conta, qual será a empresa “ativa” no contexto da navegação e das operações do sistema.

## Como funciona

1. **Listagem dinâmica:**
   - O select exibe todas as empresas vinculadas à conta do usuário autenticado (ou às contas em que ele possui permissão via `ContaMembership`).
   - Cada opção mostra o nome da empresa.

2. **Seleção e persistência:**
   - Ao selecionar uma empresa e submeter o formulário, o sistema salva o `empresa_id` escolhido na sessão do usuário (`request.session['empresa_id']`).
   - Isso define a empresa “ativa” para as próximas operações.

3. **Contexto global:**
   - A empresa selecionada passa a ser usada como referência para todas as operações, filtros e visualizações do sistema (ex: relatórios, cadastros, lançamentos, etc.), garantindo o isolamento multi-tenant.

4. **Atualização automática:**
   - Sempre que o usuário acessar o dashboard, a empresa atualmente selecionada será destacada no select.
   - Se o usuário não tiver selecionado nenhuma, a primeira empresa disponível será automaticamente definida como ativa.

5. **Segurança e consistência:**
   - O sistema só exibe empresas para as quais o usuário tem permissão, evitando acesso indevido a dados de outras contas.

## Resumo visual do fluxo
- Usuário acessa o dashboard → vê a caixa de seleção de empresa.
- Seleciona a empresa desejada → sistema salva na sessão.
- Todas as telas e operações passam a considerar a empresa selecionada como contexto principal.

> Para customizações (múltiplas contas, permissões diferenciadas), consulte a equipe de desenvolvimento.
