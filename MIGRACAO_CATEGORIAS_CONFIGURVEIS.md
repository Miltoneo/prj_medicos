# Instruções para Migração de Categorias Hardcoded para Configuráveis

## Contexto

Este arquivo documenta as alterações realizadas para tornar as categorias de movimentação financeira configuráveis pelos usuários, em vez de usar valores hardcoded.

## Alterações Realizadas

### 1. Novo Modelo: CategoriaMovimentacao

- **Arquivo**: `medicos/models/financeiro.py`
- **Descrição**: Modelo para categorias configuráveis por conta/usuário
- **Características**:
  - Categorias dinâmicas por conta
  - Configuração visual (cores, ícones)
  - Ordenação personalizável
  - Configurações contábeis e fiscais
  - Validações e regras de negócio

### 2. Refatoração do Modelo DescricaoMovimentacao

- **Alteração**: Campo `categoria` (CharField com choices hardcoded) substituído por `categoria_movimentacao` (ForeignKey)
- **Compatibilidade**: Propriedade `categoria` mantida para código legacy
- **Benefícios**:
  - Flexibilidade total na categorização
  - Configuração por usuário/conta
  - Relacionamento normalizado

### 3. Atualizações em Formulários

- **Arquivo**: `medicos/forms.py`
- **Alteração**: `DescricaoMovimentacaoForm` atualizado para usar novo campo
- **Filtro**: Categorias filtradas por conta do usuário

### 4. Atualizações em Relatórios

- **Arquivo**: `medicos/models/relatorios.py`
- **Alteração**: Método `_calcular_distribuicao_categorias` atualizado
- **Mapeamento**: Novos códigos de categoria para campos de relatório

## Migração de Dados Necessária

### Passos Recomendados:

1. **Criar migração Django**:
   ```bash
   python manage.py makemigrations medicos
   ```

2. **Executar migração com dados**:
   - Criar categorias padrão para contas existentes
   - Migrar descrições existentes para usar nova estrutura
   - Manter compatibilidade durante transição

3. **Script de migração de dados** (exemplo):
   ```python
   from medicos.models.financeiro import CategoriaMovimentacao, DescricaoMovimentacao
   
   # Para cada conta existente
   for conta in Conta.objects.all():
       # Criar categorias padrão
       CategoriaMovimentacao.criar_categorias_padrao(conta)
       
       # Migrar descrições existentes
       categorias_map = {cat.codigo: cat for cat in CategoriaMovimentacao.objects.filter(conta=conta)}
       
       for desc in DescricaoMovimentacao.objects.filter(conta=conta, categoria_movimentacao__isnull=True):
           # Mapear categoria antiga para nova
           categoria_antiga = getattr(desc, '_categoria_antiga', 'outros')
           categoria_nova = categorias_map.get(categoria_antiga, categorias_map.get('outros'))
           if categoria_nova:
               desc.categoria_movimentacao = categoria_nova
               desc.save()
   ```

## Compatibilidade

### Código Legacy
- Propriedade `categoria` mantida no modelo `DescricaoMovimentacao`
- Retorna código da categoria para compatibilidade
- Permite migração gradual de código dependente

### APIs e Views
- Verificar views que filtram por `categoria`
- Atualizar para usar `categoria_movimentacao__codigo`
- Considerar criar métodos de conveniência

## Benefícios da Refatoração

1. **Flexibilidade Total**: Usuários podem criar suas próprias categorias
2. **Configuração Visual**: Cores e ícones personalizáveis
3. **Organização**: Ordenação e agrupamento configurável
4. **Escalabilidade**: Facilita adição de novas funcionalidades
5. **Normalização**: Estrutura de dados mais limpa e eficiente

## Próximos Passos

1. Testar em ambiente de desenvolvimento
2. Criar migração de dados robusta
3. Atualizar documentação de API
4. Treinar usuários sobre nova funcionalidade
5. Monitorar performance e uso

## Arquivos Modificados

- `medicos/models/financeiro.py` - Novos modelos e refatoração
- `medicos/forms.py` - Formulário atualizado
- `medicos/models/relatorios.py` - Cálculos atualizados
- Este arquivo de documentação

## Observações Importantes

- **Backup**: Sempre fazer backup antes da migração
- **Testes**: Testar extensivamente em ambiente de desenvolvimento
- **Rollback**: Manter plano de rollback para emergências
- **Performance**: Monitorar impacto nos relatórios e consultas
