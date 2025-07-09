# 🎯 Diretivas do Projeto - Sistema de Gestão Financeira Médica

**Data de Criação**: 07/07/2025  
**Framework**: Django 4.x  
**Arquitetura**: SaaS Multi-Tenant

---

## 📜 **DIRETIVAS FUNDAMENTAIS**

### **🔒 1. CÓDIGO COMO FONTE DA VERDADE**
- O código hardcoded é SEMPRE a referência absoluta para documentação
- Nunca gerar documentação baseada em versões anteriores ou memória
- Toda documentação deve ser regenerada a partir do código atual
- Eliminar aliases legacy e padronizar nomenclaturas conforme código real
- Validar sempre que documentação reflete exatamente o estado do código

### **🏗️ 2. ARQUITETURA E MODULARIZAÇÃO**
- Manter separação clara entre módulos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`
- Respeitar isolamento multi-tenant através do modelo `Conta`
- Preservar hierarquia de relacionamentos e constraints definidas no código
- Não criar dependências circulares entre módulos
- Manter modelos simples, focados e com responsabilidade única

### **🔧 3. NOMENCLATURA E PADRÕES**
- **Modelos**: PascalCase exato conforme definido no código
- **Campos**: snake_case conforme implementação atual
- **Constantes**: UPPER_SNAKE_CASE conforme padrões Django
- Eliminar aliases de compatibilidade quando não utilizados
- Manter consistência de nomes em todo o projeto
- Atualizar referências em `admin.py`, `forms.py`, `views.py`, `tables.py` quando necessário

### **📊 4. MODELAGEM DE DADOS**
- Respeitar constraints de unique_together definidas no código
- Manter validações em métodos `clean()` conforme implementado
- Preservar índices de performance existentes
- Não alterar relacionamentos sem análise completa de impacto
- Documentar decisões de design baseadas no código atual

### **🔍 5. ANÁLISE DE MODELAGEM COMPLETA**
- Toda análise de modelagem solicitada deve considerar TODOS os modelos definidos em hardcode Django
- Incluir obrigatoriamente modelos de todos os arquivos: `base.py`, `fiscal.py`, `financeiro.py`, `despesas.py`, `auditoria.py`, `relatorios.py`
- Analisar relacionamentos entre todos os modelos, não apenas subconjuntos
- Validar constraints e dependencies em toda a base de modelos
- Nunca fazer análise parcial ignorando modelos existentes no código

### **🛡️ 6. VALIDAÇÕES E COMPLIANCE**
- Manter validações tributárias conforme legislação brasileira
- Preservar regras de negócio implementadas nos modelos
- Respeitar constraints de integridade de dados
- Manter logs de auditoria em todas as operações críticas
- Validar percentuais de rateio (soma = 100%)

### **📝 7. DOCUMENTAÇÃO E ORGANIZAÇÃO**
- Manter documentação centralizada em `docs/` com subpastas temáticas
- Remover arquivos `.md` não solicitados da pasta principal
- Gerar diagramas ER apenas quando solicitado explicitamente
- Manter arquivo de diretivas sempre atualizado
- Documentar apenas o que está implementado no código
- Scripts de teste devem ficar exclusivamente na pasta de scripts (ex: `test_scripts/`)

### **📁 7.1. CENTRALIZAÇÃO E NÃO DUPLICIDADE DE DOCUMENTAÇÃO**
- Não criar novo arquivo de documentação se já existir arquivo que trate do mesmo assunto.
- Utilize e atualize sempre o arquivo existente para manter a rastreabilidade e evitar duplicidade de informações.
- Antes de documentar, verifique a existência de arquivos relacionados no diretório `docs/` e subpastas.

### **🔄 8. DESENVOLVIMENTO E MANUTENÇÃO**
- Testar todas as alterações em ambiente de desenvolvimento
- Manter compatibilidade com Django 4.x
- Preservar funcionalidades existentes ao fazer refatorações
- Documentar breaking changes quando necessário
- Manter requirements.txt atualizado

### **⚡ 9. PERFORMANCE E OTIMIZAÇÃO**
- Usar select_related para consultas com relacionamentos
- Manter índices compostos para filtros frequentes
- Otimizar queries com base em padrões de uso reais
- Implementar paginação em listagens grandes
- Monitorar performance de consultas complexas

### **🔐 10. SEGURANÇA E AUDITORIA**
- Manter isolamento de dados por tenant (Conta)
- Registrar todas as operações em LogAuditoriaFinanceiro
- Validar permissões conforme ContaMembership roles
- Preservar rastreamento de IP e user-agent
- Implementar controles de acesso granulares

### **🎨 11. INTERFACE E USABILIDADE**
- Manter consistência visual conforme templates existentes
- Preservar funcionalidades de filtros e busca
- Implementar validações client-side quando apropriado
- Manter responsividade para dispositivos móveis
- Priorizar usabilidade sobre complexidade técnica

### **🎨 11.2. PADRONIZAÇÃO DE ESTILOS DE PÁGINA**
- O projeto deve possuir uma padronização de estilos de página, garantindo identidade visual consistente em todas as telas.
- Os templates devem herdar de um template base comum e utilizar CSS global compartilhado.
- Mudanças de layout e estilo devem ser aplicadas de forma centralizada, facilitando manutenção e evolução visual.
- A padronização deve priorizar clareza, legibilidade e responsividade.

### **🧭 11.1. SISTEMA DE NAVEGAÇÃO E USABILIDADE**
- O sistema deve possuir um menu de navegação global, acessível em todas as páginas principais.
- O menu deve garantir acesso fácil e intuitivo a todas as funcionalidades essenciais do sistema (Dashboard, Usuários, Admin, Login/Logout, etc).
- A navegação deve ser responsiva e clara, priorizando a experiência do usuário.
- O menu deve destacar a página ativa e exibir informações do usuário autenticado quando aplicável.
- Melhorias de usabilidade e acessibilidade devem ser priorizadas em toda evolução do menu.

### **🧭 11.3. MELHORES PRÁTICAS PARA MENUS DE NAVEGAÇÃO**
- O sistema deve adotar menus de navegação claros, intuitivos e consistentes em todas as páginas.
- Menus de topo (navbar) são recomendados para sistemas com poucas seções principais e navegação simples.
- Menus laterais (sidebar) são indicados para sistemas com múltiplas áreas, módulos ou funcionalidades agrupadas.
- O menu ativo deve ser destacado visualmente para orientar o usuário.
- Menus devem ser responsivos: colapsar ou adaptar em telas menores.
- Ícones e agrupamento de itens podem ser usados para facilitar a identificação de funcionalidades.
- Sempre priorizar acessibilidade: contraste, navegação por teclado e leitores de tela.
- Evitar menus excessivamente profundos ou complexos; priorizar clareza e rapidez de acesso.
- A escolha entre menu lateral ou topo deve considerar o perfil do usuário, quantidade de funcionalidades e contexto de uso.

### **🧭 11.4. MELHORES PRÁTICAS DE FUNCIONALIDADE PARA MENU SUPERIOR (NAVBAR)**
- O menu superior deve conter links para as principais áreas do sistema (Dashboard, Usuários, Admin, etc.), sempre visíveis.
- Exibir claramente o usuário autenticado e opção de login/logout.
- Destacar visualmente a página/rota ativa.
- O menu deve ser responsivo: colapsar em um botão (hambúrguer) em telas pequenas.
- Permitir fácil expansão para novos módulos sem poluir visualmente.
- Utilizar ícones para reforçar a identificação das seções, quando apropriado.
- Garantir contraste e acessibilidade para navegação por teclado e leitores de tela.
- Evitar menus suspensos excessivamente profundos; priorizar acesso rápido.
- O logo ou nome do sistema deve estar sempre visível e servir de atalho para o dashboard.
- O menu deve ser fixo no topo para acesso constante durante a navegação.

### **🧭 11.5. CARACTERÍSTICAS E FUNCIONALIDADES DE UM MENU SUPERIOR (NAVBAR)**
- Deve ser exibido no topo de todas as páginas principais do sistema.
- Apresentar o logo ou nome do sistema à esquerda, servindo de atalho para o dashboard.
- Exibir links para as principais áreas: Dashboard, Usuários, Admin, Relatórios, etc.
- Destacar visualmente a página ativa para orientar o usuário.
- Mostrar o nome/e-mail do usuário autenticado e opção de login/logout à direita.
- Ser responsivo: transformar-se em menu hambúrguer em telas pequenas.
- Permitir fácil expansão para novos módulos sem poluir o visual.
- Suportar ícones ao lado dos itens para facilitar identificação.
- Garantir contraste, acessibilidade e navegação por teclado.
- Ser fixo no topo para acesso constante durante a navegação.
- Opcionalmente, pode incluir notificações, atalhos rápidos ou menu de perfil do usuário.

### **🧭 11.6. MELHORES PRÁTICAS PARA MENU DE NAVEGAÇÃO LATERAL (SIDEBAR)**
- Deve ser exibido à esquerda da tela, disponível em todas as páginas principais.
- Agrupar funcionalidades por seções ou módulos, facilitando a navegação em sistemas com muitos recursos.
- Destacar visualmente o item ativo e o grupo expandido.
- Permitir colapso/expansão do menu para economizar espaço, especialmente em telas menores.
- Utilizar ícones ao lado dos itens para rápida identificação.
- Garantir contraste, acessibilidade e navegação por teclado.
- O menu deve ser responsivo: ocultar ou transformar-se em menu deslizante em dispositivos móveis.
- Permitir fácil expansão para novos módulos sem comprometer a clareza.
- Pode incluir avatar, nome do usuário e atalhos rápidos no topo ou rodapé do menu.
- Evitar menus excessivamente profundos; priorizar acesso rápido às principais áreas.
- Manter o menu fixo durante a navegação para acesso constante.

### **🧭 11.7. PADRÃO DE NAVEGAÇÃO ENTRE MENUS SUPERIOR E LATERAL**
- A navegação entre as funcionalidades específicas do aplicativo "medicos" (ex: dashboard, relatórios, módulos médicos, consultas, etc.) deve ser realizada prioritariamente pelo menu lateral (sidebar).
- O menu lateral deve agrupar e organizar todas as funcionalidades do domínio médico, facilitando o acesso rápido e contextual.
- O menu superior (navbar) será reservado para funcionalidades de sistema: login, logout, admin, usuários, perfil, notificações e demais ações globais.
- O menu superior deve estar sempre visível, enquanto o menu lateral pode ser colapsável para melhor uso do espaço.
- Essa separação garante clareza, escalabilidade e melhor experiência de navegação para o usuário.

### **🎨 11.8. USO DE FRAMEWORKS DE ESTILO (BOOTSTRAP)**
- O projeto deve utilizar frameworks de estilo modernos, como Bootstrap, para garantir responsividade, consistência visual e agilidade no desenvolvimento.
- O Bootstrap deve ser incluído via CDN ou arquivos locais no template base, antes dos estilos customizados.
- Aproveitar classes utilitárias e componentes do Bootstrap para layout, espaçamento, tipografia, botões, alertas, navegação, etc.
- Estruturar o layout com o grid do Bootstrap (`container`, `row`, `col`) para responsividade nativa.
- Personalizações devem ser feitas preferencialmente via variáveis ou classes próprias, evitando sobrescrever regras do framework.
- Consultar sempre a documentação oficial do Bootstrap para melhores práticas e exemplos.
- Remover estilos não utilizados e revisar periodicamente para manter a consistência visual.

### **📈 12. EVOLUÇÃO E FUTURO**
- Preparar APIs para futuras integrações
- Manter código flexível para novas funcionalidades
- Documentar limitações conhecidas
- Planejar evolutivas baseadas em necessidades reais
- Manter código legível e bem documentado

### **🚨 13. CRITÉRIOS DE QUALIDADE**
- Zero breaking changes sem aviso prévio
- Todas as migrações devem ser testadas
- Código deve passar em linting e formatação
- Cobertura de testes para funcionalidades críticas
- Documentação deve estar sempre sincronizada

### **🧩 4.1. ATUALIZAÇÃO DE HARDCODE**
- Sempre que houver alteração em modelos, campos ou relacionamentos, atualizar imediatamente o diagrama ER hardcoded e os arquivos de definição de modelos.
- O diagrama ER e as definições hardcoded devem refletir fielmente o código-fonte vigente dos modelos Django.
- Toda documentação de modelagem deve ser gerada ou revisada a partir do código real, nunca de versões antigas ou memória.
- Mudanças em nomes de campos, remoção de redundâncias ou ajustes de nomenclatura devem ser refletidos nos arquivos de documentação e diagramas imediatamente.
- A sincronização entre código e documentação é obrigatória e contínua.

---

### **✅ Checklist para ER e Modelagem de Dados Confiável (Revisado)**

- [ ] Todos os arquivos em `medicos/models/` foram lidos e analisados?
- [ ] Para cada modelo, o código-fonte está aberto lado a lado com o ER durante a revisão?
- [ ] Todos os modelos definidos no código estão presentes no ER?
- [ ] **Cada campo de cada modelo foi conferido linha a linha entre o código e o ER?**
- [ ] Todos os tipos de campo (incluindo FKs, M2M, O2O, Decimal, Boolean, Date, etc.) estão corretos no ER?
- [ ] Todos os relacionamentos (FK, M2M, O2O) estão representados?
- [ ] Todas as constraints (`unique_together`, `indexes`, etc.) estão documentadas?
- [ ] O ER/documentação foi atualizado imediatamente após a última alteração no código?
- [ ] O ER/documentação não contém modelos/campos/relacionamentos que não existem mais no código?
- [ ] Nomenclatura dos modelos e campos está idêntica à do código (sem aliases)?
- [ ] O ER/documentação foi validado por outro desenvolvedor ou por revisão cruzada?
- [ ] Toda alteração em modelos foi refletida nos arquivos de documentação e diagramas?
- [ ] (Recomendado) Utilizou script ou ferramenta para extração automática dos campos dos modelos?

> **Este checklist deve ser seguido e marcado a cada alteração de modelagem para garantir total confiabilidade e aderência ao código-fonte. Conferência linha a linha é obrigatória para cada campo de cada modelo.**

---

## ⚠️ **PROIBIÇÕES ABSOLUTAS**

- ❌ **NUNCA** gerar documentação baseada em versões antigas
- ❌ **NUNCA** criar aliases sem verificar uso no código
- ❌ **NUNCA** alterar modelos sem análise completa de impacto
- ❌ **NUNCA** quebrar isolamento multi-tenant
- ❌ **NUNCA** remover validações de compliance fiscal
- ❌ **NUNCA** criar documentação não solicitada na pasta principal
- ❌ **NUNCA** assumir estruturas sem validar no código
- ❌ **NUNCA** implementar sem testar em ambiente de desenvolvimento

---

## ✅ **OBRIGAÇÕES SEMPRE**

- ✅ **SEMPRE** ler o código antes de documentar
- ✅ **SEMPRE** validar nomenclaturas no código hardcoded
- ✅ **SEMPRE** atualizar referências em arquivos dependentes
- ✅ **SEMPRE** manter sincronização entre código e documentação
- ✅ **SEMPRE** preservar funcionalidades existentes
- ✅ **SEMPRE** documentar decisões técnicas importantes
- ✅ **SEMPRE** manter logs de auditoria atualizados
- ✅ **SEMPRE** validar multi-tenancy em alterações

---

## 🎯 **OBJETIVO FINAL**

Manter um sistema Django robusto, bem documentado e perfeitamente sincronizado entre código e documentação, com foco em:
- **Confiabilidade** dos dados financeiros
- **Compliance** fiscal brasileiro
- **Escalabilidade** multi-tenant
- **Manutenibilidade** do código
- **Usabilidade** para médicos e contadores

---

*Estas diretivas são mandatórias para qualquer alteração no projeto e devem ser consultadas antes de qualquer modificação no código ou documentação.*
