# 🚀 Dashboard SaaS Multi-Tenant - Guia de Uso

## 📋 **Visão Geral**

O Dashboard SaaS foi implementado com isolamento completo por tenant, oferecendo uma experiência personalizada para cada conta/empresa no sistema.

---

## 🎯 **Funcionalidades Principais**

### 📊 **Métricas em Tempo Real**
- **Faturamento**: Total dos últimos 30 dias
- **Saldo**: Diferença entre faturamento e despesas
- **Médicos**: Quantidade de profissionais cadastrados
- **Notas Fiscais**: Status e valores pendentes

### 📈 **Gráficos Interativos**
- **Evolução do Faturamento**: Gráfico de linha com últimos 6 meses
- **Status das NFs**: Gráfico de pizza com distribuição
- **Configurável**: Períodos de 6 ou 12 meses

### 🔔 **Sistema de Alertas**
- Licença próxima do vencimento (7 dias)
- Limite de usuários atingido
- Notas fiscais vencidas
- Alertas contextuais por tenant

---

## 🏗️ **Arquitetura do Sistema**

### **Isolamento por Tenant**
```python
# Middleware garante isolamento automático
class TenantMiddleware:
    - Valida acesso do usuário à conta
    - Define contexto global da conta ativa
    - Filtra automaticamente todos os dados
```

### **Validação de Licenças**
```python
# Middleware de licença ativa
class LicenseValidationMiddleware:
    - Verifica vencimento da licença
    - Redireciona para tela de renovação
    - Bloqueia acesso em caso de expiração
```

### **Controle de Usuários**
```python
# Middleware de limite de usuários
class UserLimitMiddleware:
    - Monitora quantidade de usuários ativos
    - Aplica limites do plano contratado
    - Fornece informações de uso
```

---

## 🎨 **Interface do Dashboard**

### **Layout Responsivo**
- **Desktop**: Sidebar fixa com menu completo
- **Mobile**: Sidebar colapsível e menu hamburger
- **Tablet**: Layout adaptativo automático

### **Componentes Visuais**
- **Cards**: Animações de hover e shadow
- **Gráficos**: Chart.js com cores temáticas
- **Badges**: Indicadores de status coloridos
- **Botões**: Gradientes e efeitos de elevação

### **Navegação Contextual**
- **Breadcrumbs**: Localização atual no sistema
- **Menu Lateral**: Itens baseados em permissões
- **Ações Rápidas**: Botões para operações comuns

---

## 🔗 **URLs e Roteamento**

### **Estrutura de URLs**
```python
# Dashboard principal
/                           # Home do dashboard
/dashboard/                 # Alias para o dashboard
/dashboard/widgets/         # Endpoint para widgets AJAX
/dashboard/relatorio-executivo/  # Relatório avançado

# Autenticação
/auth/login/               # Login multi-tenant
/auth/select-account/      # Seleção de conta
/auth/logout/              # Logout do sistema
```

### **Namespaces**
```python
# URLs organizadas por módulos
app_name = 'dashboard'     # dashboard:home
app_name = 'auth'          # auth:login_tenant
```

---

## 📱 **Responsividade**

### **Breakpoints**
- **Mobile**: < 768px (sidebar colapsada)
- **Tablet**: 768px - 1024px (layout adaptativo)
- **Desktop**: > 1024px (layout completo)

### **Adaptações Mobile**
- Menu hamburger para navegação
- Cards empilhados em coluna única
- Gráficos redimensionados automaticamente
- Textos e botões otimizados para touch

---

## 🛡️ **Segurança e Permissões**

### **Isolamento de Dados**
- Todos os dados filtrados por `conta_id`
- Validação de acesso em cada requisição
- Storage thread-safe para contexto global

### **Níveis de Permissão**
- **PROPRIETARIO**: Acesso total, incluindo relatórios executivos
- **ADMIN**: Gestão de usuários e configurações
- **USUARIO**: Operações básicas do sistema
- **VISUALIZADOR**: Apenas leitura de dados

### **Validações de Licença**
- Verificação automática de vencimento
- Bloqueio preventivo antes da expiração
- Alertas visuais e notificações

---

## 🎯 **Métricas e KPIs**

### **Financeiras**
- **Faturamento Total**: Soma de todas as NFs do período
- **Taxa de Inadimplência**: % de valores em atraso
- **Crescimento**: Comparação com período anterior
- **Saldo Líquido**: Faturamento - Despesas

### **Operacionais**
- **Médicos Ativos**: Profissionais cadastrados
- **Empresas**: Clientes/parceiros registrados
- **Usuários**: Membros ativos da conta
- **NFs Processadas**: Volume de documentos

### **Licenciamento**
- **Usuários Utilizados**: vs Limite do plano
- **Dias para Vencimento**: Alertas preventivos
- **Tipo de Plano**: Recursos disponíveis

---

## 🚀 **Como Usar**

### **1. Login Multi-Tenant**
1. Acesse `/auth/login/`
2. Digite email e senha
3. Sistema exibe contas disponíveis
4. Selecione a conta desejada

### **2. Navegação do Dashboard**
1. **Home**: Visão geral das métricas
2. **Cadastros**: Médicos e empresas
3. **Financeiro**: NFs e despesas
4. **Relatórios**: Análises detalhadas
5. **Administração**: Usuários e licenças (se admin)

### **3. Troca de Contas**
1. Clique no menu do usuário (topo direito)
2. Selecione "Trocar Conta"
3. Escolha nova conta na lista
4. Dashboard recarrega com novos dados

### **4. Relatório Executivo**
1. Acesse (apenas admin/proprietário)
2. Selecione período de análise
3. Visualize KPIs e rankings
4. Baixe ou compartilhe dados

---

## 🎨 **Customização**

### **Cores e Tema**
```css
:root {
    --primary-color: #4e73df;
    --success-color: #1cc88a;
    --warning-color: #f6c23e;
    --danger-color: #e74a3b;
}
```

### **Componentes Reutilizáveis**
- **Dashboard Cards**: Widgets modulares
- **Metric Cards**: Cartões de métricas
- **Chart Containers**: Contêineres para gráficos
- **Activity Items**: Itens de atividade recente

---

## 📊 **Próximas Melhorias**

### **Sprint 2 - Gestão de Membros**
- [ ] CRUD completo de usuários por conta
- [ ] Sistema de convites por email
- [ ] Gestão de permissões granulares
- [ ] Log de atividades dos usuários

### **Sprint 3 - Relatórios Avançados**
- [ ] Exportação de dados (PDF, Excel)
- [ ] Dashboards personalizáveis
- [ ] Filtros avançados por período
- [ ] Comparação entre contas

### **Sprint 4 - API RESTful**
- [ ] Endpoints para integração
- [ ] Autenticação via tokens
- [ ] Documentação Swagger
- [ ] SDKs para diferentes linguagens

---

## 🐛 **Troubleshooting**

### **Problemas Comuns**

**1. "Conta não selecionada"**
- Verifique se fez login corretamente
- Confirme se tem acesso à conta
- Limpe cookies e tente novamente

**2. "Licença expirada"**
- Contate o administrador da conta
- Renove a licença no painel de admin
- Verifique a data de vencimento

**3. "Acesso negado"**
- Confirme seu nível de permissão
- Solicite acesso ao proprietário
- Verifique se a conta está ativa

**4. Gráficos não carregam**
- Verifique conexão com internet (Chart.js CDN)
- Limpe cache do navegador
- Confirme se há dados no período

---

## 📞 **Suporte**

Para dúvidas técnicas ou suporte:
- **Email**: suporte@miltoneo.dev
- **GitHub Issues**: Repositório do projeto
- **Documentação**: `/docs/` no projeto

---

*Dashboard SaaS v1.0 - Desenvolvido com ❤️ para gestão médica multi-tenant*
