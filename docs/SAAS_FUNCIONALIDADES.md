# Funcionalidades SaaS Avançadas

Este documento descreve as novas funcionalidades SaaS implementadas no sistema médico conforme as melhores práticas para sistemas multi-tenant.

## 📋 Visão Geral

As funcionalidades implementadas incluem:

1. **ContaPreferencias** - Sistema de preferências personalizáveis por conta
2. **ContaAuditLog** - Rastreamento completo de ações e auditoria
3. **ContaMetrics** - Coleta e análise de métricas de uso
4. **Utilitários SaaS** - Ferramentas para facilitar o uso das funcionalidades

## 🎛️ ContaPreferencias - Configurações da Conta

### Funcionalidades

- **Interface e Aparência**: Tema, idioma, fuso horário, formato de data
- **Notificações**: Configurações de email e alertas de vencimento
- **Segurança**: Timeout de sessão, autenticação dupla (2FA)
- **Backup**: Configurações de backup automático

### Campos Disponíveis

```python
tema: 'claro' | 'escuro' | 'auto'
idioma: 'pt-br' | 'en' | 'es'
timezone: string (ex: 'America/Sao_Paulo')
formato_data_padrao: 'dd/mm/yyyy' | 'mm/dd/yyyy' | 'yyyy-mm-dd'
moeda_padrao: string (ex: 'BRL')
decimais_valor: integer (2)
notificacoes_email: boolean
notificacoes_vencimento: boolean
dias_antecedencia_vencimento: integer (1-30)
sessao_timeout_minutos: integer (30-480)
requerer_2fa: boolean
backup_automatico: boolean
frequencia_backup: 'diario' | 'semanal' | 'mensal'
```

### Como Usar

#### Via Views
```python
from medicos.utils_saas import SaaSPreferencesManager

# Obter preferências
preferences = SaaSPreferencesManager.get_or_create_preferences(conta)

# Atualizar preferências
preferences = SaaSPreferencesManager.update_preferences(
    conta, 
    tema='escuro',
    notificacoes_email=False
)
```

#### Via Template
```html
<!-- As preferências ficam disponíveis via context processor -->
<p>Tema atual: {{ conta_preferences.tema }}</p>
<p>Idioma: {{ conta_preferences.idioma }}</p>
```

#### Acessar Configurações
- URL: `/medicos/{empresa_id}/saas/configuracoes/`
- Template: `saas/configuracoes.html`

## 📊 ContaAuditLog - Auditoria e Rastreamento

### Funcionalidades

- Rastreamento de todas as ações dos usuários
- Histórico de modificações com dados antes/depois
- Informações técnicas (IP, User Agent)
- Filtros avançados por data, usuário, ação

### Tipos de Ação Disponíveis

```python
'login': 'Login'
'logout': 'Logout'
'create': 'Criação'
'update': 'Atualização'
'delete': 'Exclusão'
'export': 'Exportação'
'import': 'Importação'
'config_change': 'Mudança de Configuração'
'user_invite': 'Convite de Usuário'
'user_remove': 'Remoção de Usuário'
'backup': 'Backup'
'restore': 'Restauração'
```

### Como Usar

#### Registro Manual
```python
from medicos.utils_saas import SaaSAuditManager

# Registrar login
SaaSAuditManager.log_login(
    conta=request.conta,
    user=request.user,
    ip_address=request.META.get('REMOTE_ADDR')
)

# Registrar criação
SaaSAuditManager.log_create(
    conta=request.conta,
    user=request.user,
    objeto=nova_despesa,
    descricao="Criação de nova despesa"
)
```

#### Usando Decorador
```python
from medicos.utils_saas import audit_action

@audit_action('create', 'DespesaSocio')
def create_despesa(request, empresa_id):
    # Sua lógica aqui
    # Auditoria será registrada automaticamente
    pass
```

#### Visualizar Logs
- URL: `/medicos/{empresa_id}/saas/auditoria/`
- Template: `saas/auditoria.html`
- Filtros: ação, usuário, data início/fim

## 📈 ContaMetrics - Métricas e Analytics

### Funcionalidades

- Coleta automática de métricas de uso
- Dashboard visual com gráficos
- Resumos estatísticos (total, média, máximo)
- API para coleta em tempo real

### Tipos de Métrica Disponíveis

```python
'usuarios_ativos': 'Usuários Ativos'
'logins_dia': 'Logins por Dia'
'relatorios_gerados': 'Relatórios Gerados'
'despesas_lancadas': 'Despesas Lançadas'
'receitas_lancadas': 'Receitas Lançadas'
'notas_fiscais': 'Notas Fiscais'
'backup_executado': 'Backup Executado'
'storage_usado': 'Armazenamento Usado (MB)'
'api_calls': 'Chamadas de API'
'tempo_sessao_medio': 'Tempo Médio de Sessão (min)'
```

### Como Usar

#### Registrar Métrica
```python
from medicos.utils_saas import SaaSMetricsManager

# Registrar valor específico
SaaSMetricsManager.record_metric(
    conta=request.conta,
    metrica_tipo='relatorios_gerados',
    valor=1
)

# Incrementar métrica existente
SaaSMetricsManager.increment_metric(
    conta=request.conta,
    metrica_tipo='usuarios_ativos'
)
```

#### Obter Resumo
```python
# Resumo dos últimos 30 dias
summary = SaaSMetricsManager.get_metric_summary(
    conta=request.conta,
    metrica_tipo='logins_dia',
    periodo_dias=30
)
# Retorna: {'total': 150, 'media': 5.0, 'maximo': 12, ...}
```

#### Dashboard de Métricas
- URL: `/medicos/{empresa_id}/saas/metrics/`
- Template: `saas/metrics_dashboard.html`
- Gráficos interativos com Chart.js

#### API para Coleta em Tempo Real
```javascript
// Registrar métrica via JavaScript
fetch('/medicos/{empresa_id}/saas/api/collect-metric/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        metrica_tipo: 'api_calls',
        valor: 1,
        metadados: { origem: 'frontend' }
    })
});
```

## 🛠️ Utilitários SaaS

### Context Processor
Adicione ao `settings.py`:
```python
TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'medicos.utils_saas.saas_preferences_context'
)
```

### Decorador de Auditoria
```python
@audit_action('update', 'NotaFiscal')
def update_nota_fiscal(request, empresa_id, pk):
    # Auditoria automática
    pass
```

## 📱 URLs Disponíveis

```python
# Configurações
medicos/{empresa_id}/saas/configuracoes/

# Auditoria
medicos/{empresa_id}/saas/auditoria/

# Dashboard de Métricas
medicos/{empresa_id}/saas/metrics/

# API para coleta de métricas
medicos/{empresa_id}/saas/api/collect-metric/

# Exportação de dados
medicos/{empresa_id}/saas/export/?type=audit|metrics
```

## 🔧 Administração Django

### Acesso ao Admin
- ContaPreferencias: Configuração de preferências por conta
- ContaAuditLog: Visualização de logs com filtros avançados
- ContaMetrics: Análise de métricas com ações customizadas

### Permissões
- ContaPreferencias: Não pode ser excluída
- ContaAuditLog: Somente leitura, exclusão apenas para superusuários
- ContaMetrics: Criação/edição normal, ações de resumo disponíveis

## 📊 Exportação de Dados

### Auditoria (CSV)
- Colunas: Data/Hora, Usuário, Ação, Objeto, Descrição, IP
- Filtros aplicados automaticamente
- Nome do arquivo: `auditoria_{conta}_{data}.csv`

### Métricas (CSV)
- Colunas: Data, Tipo de Métrica, Valor, Unidade, Período
- Dados ordenados por data
- Nome do arquivo: `metricas_{conta}_{data}.csv`

## 🔍 Exemplos de Integração

### Em Views Existentes
```python
# views_despesas.py
from medicos.utils_saas import SaaSAuditManager, SaaSMetricsManager

def create_despesa(request, empresa_id):
    if request.method == 'POST':
        # ... lógica de criação ...
        
        # Registrar auditoria
        SaaSAuditManager.log_create(
            conta=request.conta,
            user=request.user,
            objeto=despesa,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Registrar métrica
        SaaSMetricsManager.increment_metric(
            conta=request.conta,
            metrica_tipo='despesas_lancadas'
        )
```

### Em Signals
```python
# signals.py
from django.db.models.signals import post_save
from medicos.utils_saas import SaaSMetricsManager

@receiver(post_save, sender=NotaFiscal)
def nota_fiscal_created(sender, instance, created, **kwargs):
    if created:
        SaaSMetricsManager.increment_metric(
            conta=instance.conta,
            metrica_tipo='notas_fiscais'
        )
```

## 🚀 Próximos Passos

1. **Dashboard Executivo**: Métricas consolidadas para gestores
2. **Alertas Automáticos**: Notificações baseadas em métricas
3. **Relatórios de Uso**: Análises detalhadas de utilização
4. **API de Métricas**: Endpoints REST para integração externa
5. **Backup Automático**: Implementação do sistema de backup configurável

## 📚 Arquivos Criados/Modificados

### Novos Arquivos
- `medicos/models/base.py` - Adicionadas classes SaaS
- `medicos/utils_saas.py` - Utilitários e managers
- `medicos/views_saas.py` - Views para funcionalidades SaaS
- `medicos/urls_saas.py` - URLs das funcionalidades SaaS
- `medicos/admin_saas.py` - Configurações do Django Admin
- `medicos/templates/saas/` - Templates para SaaS
- `docs/SAAS_FUNCIONALIDADES.md` - Esta documentação

### Arquivos Modificados
- `medicos/models/__init__.py` - Imports das novas classes
- `medicos/urls.py` - Include das URLs SaaS
- `medicos/admin.py` - Import das configurações SaaS

### Migração
- `medicos/migrations/0047_add_saas_preferences_audit_metrics.py`

## 💡 Benefícios Implementados

1. **✅ Customização por Tenant**: Cada conta pode ter suas preferências
2. **✅ Auditoria Completa**: Rastreamento de todas as ações
3. **✅ Analytics Detalhado**: Métricas de uso para otimização
4. **✅ Interface Moderna**: Dashboard responsivo com gráficos
5. **✅ Exportação de Dados**: Conformidade com LGPD/GDPR
6. **✅ Administração Eficiente**: Interface admin personalizada
7. **✅ Performance Otimizada**: Queries otimizadas e indexes
8. **✅ Segurança Aprimorada**: Logs de auditoria e configurações de segurança

---

**Sistema de Gerenciamento Médico - prj_medicos**  
*Funcionalidades SaaS implementadas em 10/09/2025*
