# Diretiva: Convite e cadastro de usuários

- Sempre que um usuário for criado pelo painel/admin, o sistema deve enviar automaticamente um e-mail de convite para o endereço informado.
- O e-mail de convite deve conter um link único de ativação, permitindo que o usuário defina sua senha e ative sua conta.
- O usuário convidado permanece inativo até completar o cadastro via link recebido.
- O fluxo de ativação deve ser seguro, expirar após uso e permitir apenas uma ativação por convite.
- O template do e-mail deve ser claro, responsivo e conter instruções para o usuário finalizar o cadastro.
- O painel deve exibir mensagem de sucesso ao administrador após o envio do convite.
- O sistema deve registrar logs de convites enviados e ativados.
- **Quando o usuário clicar no link de convite, ele deve ser redirecionado para a tela de cadastro, onde poderá definir sua senha e completar o cadastro.**

## Exemplo de texto do convite

Olá, você foi convidado para acessar o sistema. Clique no link abaixo para ativar sua conta e definir sua senha:

{{ activation_link }}

Se não reconhece este convite, ignore este e-mail.

---

## Implementação
- O método `form_valid` da view de criação de usuário já envia o convite e marca o usuário como inativo.
- O link de ativação utiliza token seguro e expira após uso.
- O template de ativação pode ser customizado em `templates/registration/activation_email.txt`.
- O endpoint `/medicos/auth/activate/<uidb64>/<token>/` deve permitir o cadastro da senha e ativação do usuário convidado, redirecionando para a tela de cadastro caso o link seja válido.
