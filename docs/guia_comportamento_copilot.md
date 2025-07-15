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
