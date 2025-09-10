# Scripts e Ferramentas de Teste

Esta pasta contém scripts auxiliares, ferramentas de teste e documentação de correções aplicadas no projeto.

## Arquivos de Teste

### `teste_relatorio_limpo.py`
- **Propósito**: Teste simples para verificar se o código do relatório está funcionando após limpeza
- **Funcionalidade**: Valida imports e sintaxe da view de relatórios
- **Uso**: `python scripts/teste_relatorio_limpo.py`

### `test_percentual.py`
- **Propósito**: Comando Django para testar cálculo de percentual no relatório mensal do sócio
- **Funcionalidade**: Testa o builder `montar_relatorio_mensal_socio` com parâmetros específicos
- **Uso**: Era um Django management command (originalmente em `medicos/management/commands/`)

## Documentação de Correções

### `CORRECAO_ADICIONAL_IR_SOCIO.md`
- Documentação da correção de cálculo de IR adicional para sócios

### `CORRECAO_ADICIONAL_IR_TRIMESTRAL.md`
- Documentação da correção de cálculo de IR adicional trimestral

### `REMOCAO_ADICIONAL_IR_MENSAL.md`
- Documentação da remoção de cálculos mensais de IR adicional

## Diretrizes para Novos Scripts

1. **Testes e Debug**: Todos os arquivos de teste, debug e validação devem ser colocados nesta pasta
2. **Nomenclatura**: Use prefixos claros como `teste_`, `debug_`, `script_`, etc.
3. **Documentação**: Sempre inclua cabeçalho com propósito e instruções de uso
4. **Shebang**: Use `#!/usr/bin/env python` para scripts executáveis
5. **Configuração Django**: Scripts Django devem incluir configuração apropriada:
   ```python
   import os
   import sys
   import django
   
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
   django.setup()
   ```

## Execução

Para executar scripts Python nesta pasta:
```bash
cd f:\Projects\Django\prj_medicos
python scripts/nome_do_script.py
```

Para scripts que requerem ambiente Django ativo, certifique-se de ter o ambiente virtual ativado.
