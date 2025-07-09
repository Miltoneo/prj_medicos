# 📋 Registro de Regras de Negócio

Este documento centraliza as regras de negócio implementadas e validadas no código do projeto, conforme as diretrizes do sistema de gestão financeira médica.

## Como usar este documento
- Registre aqui toda regra de negócio relevante implementada no código.
- Sempre mantenha a documentação sincronizada com o código-fonte.
- Utilize exemplos reais e referências a métodos, models ou views quando necessário.

---

## Exemplos de registro

### 1. Cadastro de Usuário
- Todo usuário deve estar vinculado a pelo menos uma Conta (multi-tenant).
- Usuários sem vínculo não têm acesso ao sistema.
- O vínculo é feito via model `ContaMembership`.

### 2. Validação de Licença
- O acesso do usuário à Conta depende da validade da licença (`Licenca.is_valida()`).
- Usuários de contas com licença expirada são redirecionados para a tela de licença expirada.

### 3. Constraints de Modelos
- Respeitar `unique_together` e demais constraints definidas nos models.
- Validações adicionais devem ser implementadas no método `clean()` dos models.

### 4. Abordagem SaaS Multi-Tenant
- O sistema segue arquitetura SaaS multi-tenant, onde cada usuário deve estar vinculado a uma ou mais contas (model `Conta`).
- O isolamento de dados entre tenants é garantido por constraints e validações no código.
- Toda autenticação, autorização e acesso a dados considera o contexto da conta ativa do usuário.
- Usuários sem vínculo com conta não têm acesso ao sistema.

### 5. Registro e Criação de Conta
- O usuário poderá se registrar no sistema e criar sua própria Conta (tenant) de forma autônoma.
- O processo de registro deve criar automaticamente o vínculo entre o usuário e a nova Conta.
- Usuários registrados sem Conta não terão acesso ao sistema até concluírem o processo de criação/vinculação.

### 6. Confirmação de Registro por E-mail
- Após o registro, o usuário recebe um e-mail com um link de ativação.
- O acesso ao sistema só é liberado após a confirmação do e-mail.
- O link de ativação expira após determinado tempo (ex: 48h).
- Caso o link expire, o usuário pode solicitar novo e-mail de ativação.
- Implementação baseada em token seguro e view dedicada para ativação.

---

> Atualize este arquivo sempre que uma nova regra de negócio for implementada ou alterada no código.
