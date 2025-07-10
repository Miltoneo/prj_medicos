# Diretiva: Cadastro de Empresas Médicas

## Objetivo
Padronizar o fluxo de cadastro de empresas médicas (clínicas, consultórios, grupos médicos) no sistema SaaS multi-tenant, garantindo segurança, integridade dos dados e experiência consistente.

## Regras de Cadastro

- O cadastro de empresa médica deve ser realizado por um usuário autenticado com perfil de administrador (staff/superuser).
- Cada empresa médica corresponde a uma nova instância de tenant (Conta) no sistema.
- O formulário de cadastro deve solicitar, no mínimo:
  - Nome da empresa
  - CNPJ (com validação de formato e unicidade)
  - E-mail de contato
  - Telefone
  - Endereço completo (logradouro, número, bairro, cidade, UF, CEP)
- O sistema deve validar se o CNPJ já está cadastrado para evitar duplicidade.
- Após o cadastro, a empresa deve ser criada como tenant, vinculando o usuário criador como administrador principal da conta.
- O painel deve exibir mensagem de sucesso ao administrador após o cadastro.
- O cadastro deve ser registrado em log para auditoria.
- Empresas cadastradas ficam inativas até validação documental/manual (opcional, se aplicável ao negócio).
- O painel deve permitir a visualização e edição dos dados da empresa cadastrada, respeitando permissões.

## Implementação
- Criar model `Conta` com os campos obrigatórios e relacionamentos necessários.
- Implementar formulário e view protegidos por permissão de staff.
- Garantir validação de CNPJ e unicidade.
- Registrar logs de cadastro e alterações.
- Permitir ativação/desativação manual da empresa pelo admin master do sistema.

## Diretrizes de Interface
- Toda template de lista deverá ter paginação (20 itens por página), com navegação clara entre páginas e integração com filtros e ordenação.
