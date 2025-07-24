## 4. Propagação obrigatória de revisões

Toda revisão ou alteração em código (modelos, views, forms, builders, templates, etc.) deve ser analisada para identificar a necessidade de propagação para todos os arquivos relacionados. Sempre verifique se campos, regras ou lógicas novas/alteradas precisam ser refletidas em outros pontos do sistema (ex: modelo, view, builder, template, filtro, serializer, etc.).

Exemplo:
> "Campo 'credito_mes_anterior' incluído no modelo ApuracaoPIS. Propagado para builder, view e template conforme documentação."

Fonte: .github/copilot-instructions.md, seção 4
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


## Documentation & Examples

- Consulte sempre os arquivos de instrução em `.github/` para padrões comportamentais, técnicos e de negócio.
- Não crie novos arquivos de documentação se já existir um relevante—atualize o arquivo existente.

---

**Para padrões técnicos detalhados, consulte também:**
- `.github/guia-desenvolvimento-instructions.md` (padrões técnicos e de desenvolvimento)
- `.github/documentacao_especifica_instructions.md` (regras de modelagem e negócio)
