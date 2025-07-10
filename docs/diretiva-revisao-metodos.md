# Diretiva de Projeto: Revisão de Métodos de Validação

Sempre que for solicitada a remoção ou alteração de validações em formulários, é obrigatório revisar também os métodos de validação presentes nos modelos (ex: métodos `clean`, `clean_fields`, validadores customizados ou restrições no próprio campo do modelo).

> O motivo: O Django executa a validação do modelo ao salvar a instância, mesmo que a validação tenha sido removida do formulário. Portanto, validações como "CNPJ deve ter 14 dígitos" podem continuar sendo disparadas se estiverem implementadas no modelo, como no método `clean` da classe `Empresa` em `base.py`.

**Procedimento:**
- Sempre revisar e, se necessário, remover ou ajustar validações duplicadas ou conflitantes tanto no formulário quanto no modelo.
- Documentar no PR ou commit que a revisão foi feita em ambos os locais.
- Garantir que a alteração foi testada na interface e no backend.

---

Esta diretiva visa evitar retrabalho e garantir que as validações estejam centralizadas e alinhadas com as regras de negócio atuais do projeto.
