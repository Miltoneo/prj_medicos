## Troubleshooting e Correção de Dropdowns Multi-Tenant (`medicos/forms_despesas.py`)

### 1. Diagnóstico Assertivo de Dropdowns

- Siga o fluxo de troubleshooting conforme `.github/copilot-instructions.md`, seção "Fluxo assertivo para troubleshooting de dropdowns multi-tenant e filtrados".
- Confirme a regra de negócio do filtro consultando `.github/documentacao_especifica_instructions.md` e os modelos envolvidos.
- Valide se existem registros no banco que atendam ao filtro esperado (`ItemDespesa` vinculado a `GrupoDespesa` com `tipo_rateio` e empresa correta).
- Cheque se o parâmetro de contexto (`empresa_id`) está sendo passado corretamente da view para o form/widget.
- Revise o widget: o queryset do campo deve aplicar todos os filtros de negócio necessários, sem sobrescrever o widget após definir o queryset.
- Valide o template: confirme que os assets JS/CSS do widget estão carregados e não há erro de renderização.
- Teste o fluxo completo criando/editando um registro real e validando o comportamento na interface.
- Documente a causa e a solução, citando sempre os arquivos e linhas usados para referência.

### 2. Correção Aplicada em `medicos/forms_despesas.py`

- Problema: O dropdown de `item_despesa` estava vazio no HTML porque o widget era sobrescrito após a definição do queryset, quebrando o padrão do ModelForm.
- Solução: Remover a sobrescrita do widget após definir o queryset, mantendo o padrão do ModelForm. Isso garante que as opções do dropdown sejam renderizadas corretamente no HTML.

#### Exemplo de código corrigido:

```python
class DespesaEmpresaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)
        queryset = ItemDespesa.objects.filter(
            grupo_despesa__empresa_id=empresa_id,
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
        )
        self.fields['item_despesa'].queryset = queryset
        # Não sobrescrever o widget após definir o queryset, mantendo o padrão do ModelForm

    class Meta:
        model = DespesaRateada
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

class DespesaSocioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
        )
        self.fields['item_despesa'].required = True
        # Não sobrescrever o widget após definir o queryset, mantendo o padrão do ModelForm

    class Meta:
        model = DespesaSocio
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
```

- Fonte: `medicos/forms_despesas.py`, linhas 1-41 (após patch).
- Referência: `.github/copilot-instructions.md`, seção 3.

### 3. Recomendações

- Nunca sobrescrever widgets após definir o queryset em ModelForms.
- Garantir que o contexto (`empresa_id`) seja passado corretamente via context processor.
- Validar que o dropdown renderiza opções no HTML, não apenas no bloco de debug.
- Citar sempre os arquivos e linhas utilizados para referência.

---

Se precisar adaptar para outro fluxo ou arquivo, utilize este modelo como base.
## REGRA FUNDAMENTAL DE CONTEXTO DJANGO

Sempre considere que o ambiente de desenvolvimento, execução e troubleshooting é um projeto Django. Todas as sugestões, exemplos, revisões e implementações devem assumir o contexto, padrões e dependências de um ambiente Django, salvo instrução explícita em contrário. Não utilize exemplos ou padrões de outros frameworks ou linguagens.

---

### REGRA OBRIGATÓRIA DE TITULAÇÃO DE PÁGINA
- O título da página deve ser passado via variável de contexto `titulo_pagina` na view.
- O template filho deve obrigatoriamente usar `{% extends 'layouts/base_cenario_financeiro.html' %}` (ou outro base conforme o fluxo) e nunca exibir, definir ou duplicar o título em nenhum bloco, elemento ou variável; o base incorpora e exibe o título automaticamente.
- O título é exibido exclusivamente pelo template base, nunca pelo filho.
- Toda tela deve seguir este fluxo, sem exceções ou dubiedade.
- Exemplo correto na view:
  ```python
  context['titulo_pagina'] = 'Lançamentos de movimentações financeiras'
  ```
- Exemplo correto no template filho:
  ```django
  {% extends 'layouts/base_cenario_financeiro.html' %}
  {% block content %}
  ...conteúdo...
  {% endblock %}
  ```
- Exemplo de exibição no layout base:
  ```django
  <!-- medicos/templates/layouts/base_cenario_financeiro.html -->
  <h4 class="fw-bold text-primary">Título: {{ titulo_pagina }}</h4>
  ```
- Nunca defina `<h1>`, `<h2>`, ou `{{ titulo_pagina }}` no template filho.
Fonte: medicos/templates/layouts/base_cenario_financeiro.html, linhas 15-25; medicos/views_financeiro_lancamentos.py, método get_context_data.
## 4. Propagação obrigatória de revisões

Toda revisão ou alteração em código (modelos, views, forms, builders, templates, etc.) deve ser analisada para identificar a necessidade de propagação para todos os arquivos relacionados. Sempre verifique se campos, regras ou lógicas novas/alteradas precisam ser refletidas em outros pontos do sistema (ex: modelo, view, builder, template, filtro, serializer, etc.).

Exemplo:
> "Campo 'credito_mes_anterior' incluído no modelo ApuracaoPIS. Propagado para builder, view e template conforme documentação."

Fonte: .github/copilot-instructions.md, seção 4

### REGRA DE ANÁLISE GLOBAL DE IMPACTO
Toda revisão ou implementação de código deve ser obrigatoriamente analisada em contexto global do projeto, considerando dependências, integrações e fluxos existentes, para eliminar qualquer possibilidade de efeito colateral em funcionalidades já implementadas e operacionais. A validação deve incluir modelos, views, forms, templates, URLs, context processors e regras de negócio documentadas. Sempre cite a fonte e o trecho utilizado para justificar decisões.

## 5. REGRA CRÍTICA: Exclusões e Operações em Lote com Signals

### PROIBIÇÃO DE EXCLUSÕES EM LOTE PARA MODELOS COM SIGNALS

**NUNCA use `queryset.delete()` para modelos que possuem signals críticos de sincronização!**

#### ❌ **OPERAÇÕES PROIBIDAS:**
```python
# ERRADO - NÃO dispara signals individuais
MovimentacaoContaCorrente.objects.filter(...).delete()
DespesaSocio.objects.filter(...).delete()
DespesaRateada.objects.filter(...).delete()
ItemDespesaRateioMensal.objects.filter(...).delete()
```

#### ✅ **OPERAÇÕES CORRETAS:**
```python
# CORRETO - Dispara signals para cada objeto
for objeto in queryset:
    objeto.delete()  # Dispara pre_delete e post_delete signals

# OU usar script com método individual
python script_apagar_debitos_sincronizado.py --metodo individual
```

#### 🎯 **CAUSA RAIZ:**
- `QuerySet.delete()` é uma operação SQL em lote que NÃO dispara signals `pre_delete` e `post_delete` por objeto individual
- Isso quebra a sincronização automática entre modelos relacionados (ex: despesas ↔ lançamentos bancários)
- Resulta em dados "órfãos" e inconsistências que requerem correção manual

#### 🔧 **MODELOS AFETADOS:**
- `MovimentacaoContaCorrente` - Sincronizado com despesas via signals
- `DespesaSocio` - Signal de sincronização com conta corrente
- `DespesaRateada` - Signal de sincronização com conta corrente
- `ItemDespesaRateioMensal` - Signal de recálculo automático de rateios
- Qualquer modelo com `@receiver(pre_delete)` ou `@receiver(post_delete)`

#### 📋 **PROTOCOLO OBRIGATÓRIO:**
1. **Antes de qualquer exclusão em lote**: Verificar se o modelo possui signals críticos
2. **Para operações grandes**: Usar scripts com opção `--metodo individual` 
3. **Após exclusões em lote acidentais**: Executar `python corrigir_sincronizacao.py`
4. **Em scripts de produção**: Sempre incluir aviso sobre método de exclusão

#### 📚 **REFERÊNCIAS:**
- `medicos/signals_financeiro.py` - Signals de sincronização implementados
- `script_apagar_debitos_sincronizado.py` - Script correto com opções de sincronização
- `corrigir_sincronizacao.py` - Script de correção para inconsistências

**Fonte**: Correção aplicada em 02/09/2025 após identificação de inconsistências causadas por exclusão em lote no sistema de sincronização despesas ↔ conta corrente.

## 3. Fluxo assertivo para troubleshooting de dropdowns multi-tenant e filtrados

Sempre que houver problema em dropdowns (ex: lista vazia, lista errada, filtro não aplicado), siga este fluxo:

1. **Confirme a regra de negócio exata** esperada para o filtro (ex: só mostrar itens com rateio, só da empresa ativa, etc). Consulte `.github/documentacao_especifica_instructions.md` e os modelos envolvidos.
2. **Valide os dados reais**: verifique se existem registros no banco que atendam ao filtro esperado (ex: ItemDespesa vinculado a GrupoDespesa com tipo_rateio=COM_RATEIO e empresa correta).
3. **Cheque o parâmetro de contexto**: garanta que o parâmetro (ex: empresa_id) está sendo passado corretamente da view para o form/widget.
4. **Revise o widget**: confira se o queryset do widget está aplicando todos os filtros de negócio necessários.
5. **Valide o template**: confirme que os assets JS/CSS do widget estão carregados e não há erro de renderização.
6. **Teste o fluxo completo**: crie/edite um registro real e valide o comportamento na interface.
7. **Documente a causa e a solução**: cite sempre os arquivos e linhas usados para referência.

Exemplo de troubleshooting assertivo:
> "Dropdown de ItemDespesa não mostra opções. Validei que empresa_id=1 está correto na view (medicos/views_despesas.py, linha X), existem itens válidos no banco (ItemDespesa.objects.filter(...)), e o filtro do widget está correto (medicos/widgets.py, linha Y). Ajuste realizado para filtrar apenas COM_RATEIO."
# Copilot Instructions for prj_medicos



## 1. Regras Comportamentais e de Busca (AI/Agent)

### REGRA OBRIGATÓRIA DE TITULAÇÃO DE PÁGINA

REGRA OBRIGATÓRIA DE TITULAÇÃO DE PÁGINA
- O título da página deve ser passado via variável de contexto `titulo_pagina` na view.
- O template filho NÃO pode definir título fixo ou duplicado; o layout base (`base_cenario_financeiro.html`) incorpora e exibe o título automaticamente.
- Toda tela deve seguir este fluxo, sem exceções ou dubiedade.
- Exemplo correto na view:
  ```python
  context['titulo_pagina'] = 'Lançamentos de movimentações financeiras'
  ```
- Exemplo de exibição no layout base:
  ```django
  <!-- medicos/templates/layouts/base_cenario_financeiro.html -->
  <h4 class="fw-bold text-primary">Título: {{ titulo_pagina }}</h4>
  ```
Fonte: medicos/templates/layouts/base_cenario_financeiro.html, linhas 15-25; medicos/views_financeiro_lancamentos.py, método get_context_data.

    - Sempre considere apenas o código presente no repositório como referência. Não utilize memória, versões antigas, padrões genéricos de frameworks ou suposições.
    - Desabilite heurística genérica: ignore qualquer padrão não documentado nos arquivos do repositório.
    - Não utilize convenções do Django, Python ou outros frameworks sem validação e citação explícita do repositório.
    - Consulte a documentação oficial do projeto antes de qualquer alteração. Não deduza regras por experiência prévia.
    - Antes de propor, revisar ou alterar código:
      - Execute busca detalhada nos arquivos `.github/copilot-instructions.md` e `.github/guia-desenvolvimento-instructions.md`.
      - Leia a documentação relevante e cite o arquivo e linha utilizada.
      - Verifique se a solução segue exatamente as regras e exemplos documentados.
      - Se houver dúvida, pergunte antes de modificar.
    - Ao citar regras ou exemplos, informe sempre o arquivo e as linhas exatas utilizadas.
    - Nunca crie, adapte ou assuma convenções não documentadas. Siga apenas o que está registrado oficialmente.
    - Toda resposta deve citar o arquivo e linha de referência. Respostas sem fonte devem ser rejeitadas.

**Exemplo correto:**
> "Antes de definir o padrão de URL, consultei o guia de desenvolvimento e alinhei o path e name conforme o exemplo documentado, incluindo todos os parâmetros necessários."

**Exemplo incorreto:**
> "Apenas alinhar path e name sem analisar se falta algum parâmetro essencial para o contexto."

**Ao revisar ou criar URLs:**
- Verifique se todos os parâmetros necessários ao contexto de negócio estão presentes (ex: empresa_id, usuario_id, etc).
- Compare com padrões já adotados para recursos semelhantes.
- Questione se a ausência de parâmetros pode causar ambiguidade, falhas de segurança ou inconsistência.
- Priorize a lógica de negócio e a consistência, não apenas a sintaxe.

**Validação e Mudanças de Modelos:**
- Remova ou ajuste validações duplicadas ou conflitantes tanto no formulário quanto no modelo.
- Toda alteração de modelo deve respeitar unique_together, constraints e validação em métodos clean().
- Garanta que a alteração foi testada na interface e no backend.

**Formato das Respostas:**
- Sempre cite o(s) trecho(s) utilizado(s), o arquivo e as linhas correspondentes para qualquer regra ou exemplo usado.
- Nunca afirme que um arquivo foi removido sem confirmação real no ambiente.
- Se uma operação não puder ser realizada por limitações do ambiente, informe claramente ao usuário.

---

## 2. Busca Detalhada e Rastreabilidade

- Toda solicitação deve ser respondida com busca detalhada no código fonte e documentação oficial.
- Sempre cite o(s) trecho(s), arquivo e linhas utilizados.
- Exemplo:
  > "Fonte: docs/README.md, linhas 10-25. Trecho: ..."
  > "Fonte: medicos/views_aplicacoes_financeiras.py, linhas 10-30. Trecho: ..."

---

## Big Picture & Architecture

- Django-based SaaS for medical/financial management, multi-tenant (each user linked to one or more `Conta` tenants).
- Data isolation and business logic enforced at model and middleware level (`medicos/models/`, `medicos/middleware/`).
- Modularized models: split by domain (`base.py`, `fiscal.py`, `financeiro.py`, `auditoria.py`, `relatorios.py`). O módulo `despesas.py` é utilizado apenas para controle gerencial e rateio, não para cálculo direto de impostos.
- Main app: `medicos`. Core config: `prj_medicos/settings.py`.
- Context parameters (e.g., `empresa_id`) are required in all business URLs/views. See `docs/guia_desenvolvimento.md`.
- Temporal context (`mes/ano`) is always in `request.session['mes_ano']` and must be respected by all business logic and UI.

## Developer Workflows

- Use Docker Compose (`compose.dev.yaml`) for local dev: `app` (Django), `db` (Postgres), `redis`.
- Start: `docker compose -f compose.dev.yaml up --build`
- Migrations and server startup are handled automatically by the app container.
- Dependencies: `requirements.txt`. Logs: `django_logs/`.


- **Templates:** Use `{% block content %}` in all child templates. Never use custom block names (e.g., `{% block conteudo_cadastro %}`), as this breaks rendering. Veja `.github/guia-desenvolvimento-instructions.md`, seção 1.
- **URLs:** URL patterns must align `path` and `name` (both in snake_case), and always include required context parameters (e.g., `empresa_id`). Veja `.github/guia-desenvolvimento-instructions.md`, seção 2.
- **Context Processors:** Use context processors for global variables (e.g., `empresa`, `conta`, `usuario_atual`). Never fetch these directly in views or templates. Veja `.github/guia-desenvolvimento-instructions.md`, seção 3.
- All business rules, especially for models and validation, are documented in `.github/documentacao_especifica_instructions.md`.
- Multi-tenant logic: always filter/query by the active tenant (`conta`) and enforce license checks (see `medicos/middleware.py`).
- The system uses custom user model (`CustomUser` in `medicos/models/base.py`).

## Integration & Data Flow

- External dependencies: Postgres, Redis, SMTP (for user registration/activation).
- All user registration and activation flows are email-based and tokenized.
- Data flows: User → Membership (ContaMembership) → Conta → Empresa → domain models (Despesas, Financeiro, etc.).
- All business logic is enforced both in views and models; always check for duplicated/conflicting validation.

## Sincronização Automática Despesas ↔ Conta Corrente

### Funcionamento dos Signals Implementados:

1. **DespesaSocio**: Toda despesa individual gera lançamento automático na conta corrente
2. **DespesaRateada**: Toda despesa rateada gera lançamentos proporcionais para cada sócio
3. **ItemDespesaRateioMensal**: Alterações no rateio recalculam automaticamente todos os lançamentos do mês

### Scripts de Manutenção:

- `corrigir_sincronizacao.py` - Remove lançamentos órfãos e recria os faltantes
- `script_apagar_debitos_sincronizado.py` - Exclusão segura com opções de sincronização
- `testar_sincronizacao_despesas.py` - Validação completa dos signals

### Localização dos Signals:

- Arquivo: `medicos/signals_financeiro.py`
- Registrado em: `medicos/apps.py` método `ready()`
- Logs em: `django_logs/` com level INFO

**Fonte**: Implementação completa da sincronização aplicada em 02/09/2025 conforme seção 5 deste documento.

## Documentation & Examples

- Consulte sempre os arquivos de instrução em `.github/` para padrões comportamentais, técnicos e de negócio.
- Não crie novos arquivos de documentação se já existir um relevante—atualize o arquivo existente.

---

**Para padrões técnicos detalhados, consulte também:**
- `.github/guia-desenvolvimento-instructions.md` (padrões técnicos e de desenvolvimento)
- `.github/documentacao_especifica_instructions.md` (regras de modelagem e negócio)
