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
