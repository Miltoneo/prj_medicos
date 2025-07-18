# Sempre considere e siga a documentação do projeto

Antes de propor, revisar ou alterar qualquer código, leia e siga rigorosamente a documentação oficial do projeto (guia de desenvolvimento, padrões de URL, exemplos, etc). Todas as decisões devem estar alinhadas com as regras e exemplos documentados.

**Nunca assuma padrões apenas por dedução ou experiência prévia.**

**Checklist obrigatório:**
- Consulte a documentação do projeto antes de sugerir ou aprovar qualquer padrão.
- Certifique-se de que a solução está de acordo com as regras e exemplos documentados.
- Se houver dúvida, questione e peça esclarecimento antes de aplicar mudanças.

**Exemplo de comportamento correto:**
"Antes de definir o padrão de URL, consultei o guia de desenvolvimento e alinhei o path e name conforme o exemplo documentado, incluindo todos os parâmetros necessários."
# Evite comportamento superficial (lazy) na análise de URLs

Ao revisar ou criar URLs, nunca se limite apenas à padronização de nomes (path e name). Sempre:
- Verifique se todos os parâmetros necessários ao contexto de negócio estão presentes (ex: empresa_id, usuario_id, etc).
- Compare com padrões já adotados para recursos semelhantes no projeto.
- Questione se a ausência de parâmetros pode causar ambiguidade, falhas de segurança ou inconsistência.
- Priorize a consistência e a lógica de negócio, não apenas a sintaxe.

**Exemplo de comportamento a evitar:**
"Apenas alinhar path e name sem analisar se falta algum parâmetro essencial para o contexto."

**Exemplo de comportamento correto:**
"Além de alinhar path e name, garantir que todos os parâmetros de contexto (como empresa_id) estejam presentes, conforme o padrão dos outros recursos do projeto."
# Regras de Comportamento do Copilot (migradas de praticas_e_padroes.md)

- Sempre revisar e, se necessário, remover ou ajustar validações duplicadas ou conflitantes tanto no formulário quanto no modelo.
- Garantir que a alteração foi testada na interface e no backend.
- Esta diretiva visa evitar retrabalho e garantir que as validações estejam centralizadas e alinhadas com as regras de negócio atuais do projeto.
# Guia de Comportamento do Copilot

## 1. Regras para Mensagens de Operações no Sistema

- O Copilot não deve emitir mensagens afirmando que arquivos foram removidos fisicamente, a menos que a exclusão seja realmente confirmada no sistema de arquivos.
- Todas as respostas sobre operações de exclusão devem refletir apenas o que foi possível executar no ambiente atual.
- Mensagens e confirmações devem sempre corresponder ao estado real do projeto e dos arquivos.
- Caso uma operação não possa ser realizada por limitações do ambiente, o Copilot deve informar claramente ao usuário.
- Não emitir mensagens que afirmem ações não realizadas, como exclusão física de arquivos, e todas as respostas devem refletir apenas o estado real do ambiente.

---

Este guia deve ser seguido em todas as interações e operações realizadas pelo Copilot no projeto prj_medicos.

## 2. Regra obrigatória: Busca detalhada na documentação

Toda solicitação feita ao Copilot deve ser respondida com busca detalhada tanto nos arquivos de documentação do projeto quanto no código fonte. A resposta deve sempre citar o(s) trecho(s) utilizado(s), o arquivo e as linhas correspondentes. Não é permitido responder apenas de memória ou por padrão; é obrigatório realizar uma busca ativa nos arquivos de documentação e no código antes de responder.

Exemplo de resposta:
> "Fonte: docs/README.md, linhas 10-25. Trecho: ..."
> "Fonte: medicos/views_aplicacoes_financeiras.py, linhas 10-30. Trecho: ..."

Esta regra garante rastreabilidade, precisão e transparência em todas as respostas do assistente.
