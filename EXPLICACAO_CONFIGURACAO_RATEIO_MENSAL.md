# Explicação do Modelo TemplateRateioMensalDespesas (Antes: ConfiguracaoRateioMensal)

## Visão Geral

O modelo `TemplateRateioMensalDespesas` (anteriormente `ConfiguracaoRateioMensal`) é uma entidade de controle que gerencia as configurações de rateio de despesas para um mês específico no sistema. Ele funciona como um "template" ou "controlador" para organizar e controlar todos os percentuais de rateio mensal definidos para cada item de despesa em um determinado período.

**⚠️ Nota**: Este documento usa o nome antigo `ConfiguracaoRateioMensal` no código. Na implementação real, deve ser usado `TemplateRateioMensalDespesas`.

## Propósito e Função

### Objetivo Principal
- **Controle temporal**: Organiza as configurações de rateio por período mensal
- **Status de configuração**: Controla o estado da configuração (rascunho, em configuração, finalizada, aplicada)
- **Facilitar cópia**: Permite copiar percentuais do mês anterior como base para o novo mês
- **Auditoria**: Mantém histórico de quem criou e finalizou cada configuração

### Funcionamento no Sistema
O modelo trabalha em conjunto com `PercentualRateioMensal` seguindo este fluxo:

1. **Criação da configuração**: Um novo registro é criado para um mês específico
2. **Configuração dos percentuais**: Os percentuais individuais são definidos via `PercentualRateioMensal`
3. **Finalização**: A configuração é marcada como finalizada quando todos os percentuais estão corretos
4. **Aplicação**: Quando despesas são rateadas, a configuração é marcada como aplicada

## Estrutura dos Campos

### Campos Principais

```python
# Identificação e relacionamento
conta = ForeignKey(Conta)           # Conta proprietária da configuração
mes_referencia = DateField          # Mês de referência (sempre dia 1)

# Status da configuração
status = CharField(choices=[
    'rascunho',         # Inicial, permite edições
    'em_configuracao',  # Em processo de configuração
    'finalizada',       # Configuração completa e validada
    'aplicada'          # Já foi utilizada em rateios de despesas
])

# Controle de criação e finalização
data_criacao = DateTimeField        # Quando foi criada
data_finalizacao = DateTimeField    # Quando foi finalizada
criada_por = ForeignKey(User)       # Usuário que criou
finalizada_por = ForeignKey(User)   # Usuário que finalizou

# Observações
observacoes = TextField             # Notas e comentários sobre a configuração
```

### Campos de Auditoria
- **data_criacao**: Registra quando a configuração foi criada
- **data_finalizacao**: Registra quando foi finalizada (liberada para uso)
- **criada_por**: Usuário responsável pela criação
- **finalizada_por**: Usuário que validou e finalizou a configuração

## Estados (Status) da Configuração

### 1. **rascunho** (Status Inicial)
- Configuração recém-criada
- Permite todas as edições
- Percentuais podem ser incluídos, alterados ou removidos
- Não pode ser usada para rateio de despesas

### 2. **em_configuracao** (Em Processo)
- Configuração em processo de definição
- Percentuais estão sendo definidos
- Ainda permite edições
- Não pode ser usada para rateio

### 3. **finalizada** (Pronta para Uso)
- Configuração completa e validada
- Todos os percentuais foram definidos e somam 100% para cada item
- Edições restritas ou bloqueadas
- Pode ser usada para rateio de despesas

### 4. **aplicada** (Em Uso)
- Configuração já foi utilizada em rateios reais
- Alterações bloqueadas para manter integridade
- Histórico preservado para auditoria

## Métodos Principais

### 1. **copiar_percentuais_mes_anterior()**

Este é o método mais importante do modelo. Sua função é:

```python
def copiar_percentuais_mes_anterior(self):
    """
    Copia os percentuais do mês anterior para este mês como base
    """
```

**Funcionamento:**
1. Identifica o mês anterior à `mes_referencia`
2. Busca todos os `PercentualRateioMensal` do mês anterior
3. Cria novos registros para o mês atual mantendo:
   - Mesmo item de despesa
   - Mesmo sócio
   - Mesmo percentual
4. Evita duplicação verificando se já existe percentual para o item/sócio no mês atual
5. Adiciona observação indicando que foi copiado do mês anterior

**Benefícios:**
- **Agilidade**: Evita reconfigurar todos os percentuais a cada mês
- **Consistência**: Mantém a distribuição anterior como base
- **Flexibilidade**: Permite ajustes após a cópia

### 2. **save()** (Sobrescrito)
- Normaliza a `mes_referencia` sempre para o dia 1 do mês
- Garante consistência temporal

## Relacionamentos com Outros Modelos

### Com PercentualRateioMensal
- **Relação**: Um para muitos (1:N)
- **Funcionamento**: Uma configuração pode ter vários percentuais específicos
- **Chave**: `mes_referencia` + `conta` conectam os modelos

### Com Despesa
- **Relação**: Indireta através de PercentualRateioMensal
- **Funcionamento**: Quando uma despesa é rateada, usa os percentuais da configuração do mês correspondente

### Com Conta e Usuários
- **Conta**: Define a propriedade da configuração
- **Usuários**: Rastreiam criação e finalização para auditoria

## Fluxo de Uso Típico

### 1. **Início do Mês**
```python
# Criar nova configuração para o mês
configuracao = ConfiguracaoRateioMensal.objects.create(
    conta=conta,
    mes_referencia=date(2024, 3, 1),
    criada_por=usuario,
    status='rascunho'
)

# Copiar percentuais do mês anterior
percentuais_copiados = configuracao.copiar_percentuais_mes_anterior()
```

### 2. **Configuração dos Percentuais**
```python
# Atualizar status
configuracao.status = 'em_configuracao'
configuracao.save()

# Ajustar percentuais específicos conforme necessário
# (via interface administrativa ou programaticamente)
```

### 3. **Finalização**
```python
# Validar se todos os percentuais somam 100% para cada item
# Finalizar configuração
configuracao.status = 'finalizada'
configuracao.data_finalizacao = timezone.now()
configuracao.finalizada_por = usuario
configuracao.save()
```

### 4. **Uso em Rateios**
```python
# Quando uma despesa é rateada, a configuração é marcada como aplicada
configuracao.status = 'aplicada'
configuracao.save()
```

## Vantagens do Modelo

### 1. **Organização Temporal**
- Cada mês tem sua configuração específica
- Histórico preservado para auditoria
- Facilita comparações entre períodos

### 2. **Controle de Estado**
- Status claro do processo de configuração
- Previne uso de configurações incompletas
- Protege dados após aplicação

### 3. **Facilidade de Manutenção**
- Cópia automática do mês anterior
- Reduz trabalho manual repetitivo
- Permite ajustes graduais

### 4. **Auditoria Completa**
- Registro de quem criou e finalizou
- Histórico de mudanças de status
- Rastreabilidade completa

## Integração com o Sistema de Rateio

### Validações Automáticas
O sistema valida que:
- Soma dos percentuais = 100% para cada item de despesa
- Apenas itens dos grupos FOLHA e GERAL podem ter rateio
- Configurações finalizadas/aplicadas não podem ser alteradas

### Uso em Despesas
Quando uma despesa é rateada:
1. Sistema identifica o mês da despesa
2. Busca a configuração correspondente
3. Utiliza os percentuais definidos para criar os rateios
4. Marca a configuração como "aplicada"

## Exemplo Prático

```python
# Cenário: Configuração de rateio para março/2024

# 1. Criar configuração
config_marco = ConfiguracaoRateioMensal.objects.create(
    conta=minha_conta,
    mes_referencia=date(2024, 3, 1),
    criada_por=usuario_admin,
    status='rascunho',
    observacoes='Configuração base copiada de fevereiro com ajustes para novo sócio'
)

# 2. Copiar do mês anterior
config_marco.copiar_percentuais_mes_anterior()
# Resultado: Todos os percentuais de fevereiro são copiados para março

# 3. Ajustar percentuais específicos
# (Exemplo: Dr. Silva saiu, Dr. Santos entrou)
# Isso seria feito via interface administrativa ou métodos específicos

# 4. Finalizar configuração
config_marco.status = 'finalizada'
config_marco.data_finalizacao = timezone.now()
config_marco.finalizada_por = usuario_supervisor
config_marco.save()

# 5. Uso automático em rateios
# Quando uma despesa de março é rateada, o sistema automaticamente:
# - Busca config_marco
# - Usa os percentuais definidos
# - Marca status como 'aplicada'
```

## Conclusão

O modelo `TemplateRateioMensalDespesas` é essencial para a organização e controle do sistema de rateio de despesas. Ele oferece:

- **Estrutura organizacional** por período mensal
- **Controle de fluxo** através dos status
- **Facilidades operacionais** como cópia automática
- **Auditoria completa** de todo o processo
- **Integração natural** com o sistema de rateio

Este modelo garante que o rateio de despesas seja feito de forma consistente, auditável e eficiente, proporcionando uma base sólida para a gestão financeira do sistema de médicos.
