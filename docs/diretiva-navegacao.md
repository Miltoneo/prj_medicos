# Diretiva de Navegação - Barra de Menu Superior

## Definição
A barra de menu superior é um componente horizontal fixo no topo do sistema, responsável por centralizar a navegação principal do aplicativo. Ela deve:

- Exibir o logotipo ou nome do sistema à esquerda, funcionando como link para a página inicial.
- Apresentar links principais (ex: Início, Usuários, Configurações) dispostos horizontalmente, cada um com ícone representativo.
- Exibir, à direita, a área do usuário autenticado (e-mail/nome) e o botão de login/logout, ambos com ícones.
- Manter fundo escuro e texto claro, seguindo o padrão visual do tema escuro do sistema.
- Ser responsiva, mantendo a disposição horizontal dos itens em telas grandes e adaptando para dispositivos móveis se necessário.

## Resumo gráfico das barras de navegação

### Navbar Superior (Horizontal, Fixa no Topo)

```
+-------------------------------------------------------------------------------------- +
| [MedicosApp]   🏠 Início   👥 Usuários   ⚙️ Configurações                [Usuário]   |
+-------------------------------------------------------------------------------------- +
```
- Fixa no topo (`position: fixed; top: 0;`)
- Fundo escuro (`bg-dark`), texto claro
- Logotipo à esquerda
- Links principais (com ícones): Início, Usuários, Configurações
- Área do usuário à direita (login/logout, nome/email, ícone)

### Sidebar Lateral (Vertical, Fixa à Esquerda em Desktop)

```
+---------------------- +
| Painel Médico        |
|----------------------|
| 🏠 Dashboard         |
| 📅 Consultas         |
| 📊 Relatórios        |
| ---- Cadastros ----  |
| 👥 Usuários          |
| 🏢 Empresas Médicas  |
|----------------------|
| Usuário: ...         |
+---------------------- +
```
- Fixa à esquerda em desktop, overlay em mobile
- Fundo escuro, texto claro
- Links de navegação com ícones
- Seções (ex: Cadastros)
- Rodapé com status do usuário

### Observações
- Responsividade: Sidebar some ou vira overlay em telas pequenas; navbar permanece fixa.
- Tema escuro: Todas as cores e fundos definidos via CSS global.
- Ícones: Bootstrap Icons.
- Consistência: Todos os templates principais herdam de `base.html` para garantir padrão visual.

## Exemplo visual (wireframe):

+--------------------------------------------------------------------------------------+
| MedicosApp   | Início | Usuários | Configurações | usuario@email.com | Sair/Entrar   |
+--------------------------------------------------------------------------------------+

## Exemplo de código (Bootstrap 5):

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark border-bottom shadow-sm">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">MedicosApp</a>
    <ul class="navbar-nav ms-auto flex-row gap-3 align-items-center mb-0">
      <li class="nav-item"><a class="nav-link text-white" href="#"><i class="bi bi-house"></i> Início</a></li>
      <li class="nav-item"><a class="nav-link text-white" href="#"><i class="bi bi-people"></i> Usuários</a></li>
      <li class="nav-item"><a class="nav-link text-white" href="#"><i class="bi bi-gear"></i> Configurações</a></li>
      <li class="nav-item"><span class="nav-link text-white"><i class="bi bi-person-circle"></i> usuario@email.com</span></li>
      <li class="nav-item"><a class="nav-link text-white" href="#"><i class="bi bi-box-arrow-right"></i> Sair</a></li>
    </ul>
  </div>
</nav>
```

Essa barra garante navegação clara, moderna e acessível em todo o sistema.
