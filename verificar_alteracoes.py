#!/usr/bin/env python
import ast

def verificar_sintaxe():
    try:
        with open('medicos/views_relatorios.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tentar fazer parse do arquivo
        ast.parse(content)
        print("✅ Sintaxe Python válida")
        
        # Verificar se as alíquotas estão sendo referenciadas
        if 'aliquotas_empresa.CSLL_ALIQUOTA' in content:
            print("✅ CSLL_ALIQUOTA está sendo referenciada")
        else:
            print("❌ CSLL_ALIQUOTA NÃO encontrada")
            
        if 'aliquotas_empresa.CSLL_PRESUNCAO_CONSULTA' in content:
            print("✅ CSLL_PRESUNCAO_CONSULTA está sendo referenciada")
        else:
            print("❌ CSLL_PRESUNCAO_CONSULTA NÃO encontrada")
            
        if 'aliquotas_empresa.CSLL_PRESUNCAO_OUTROS' in content:
            print("✅ CSLL_PRESUNCAO_OUTROS está sendo referenciada")
        else:
            print("❌ CSLL_PRESUNCAO_OUTROS NÃO encontrada")
            
        # Verificar se não há valores hardcoded antigos
        if "Decimal('0.09')" in content:
            print("⚠️  Ainda existe valor hardcoded 0.09 no código")
        else:
            print("✅ Valor hardcoded 0.09 removido")
            
        if "Decimal('0.32')" in content:
            print("⚠️  Ainda existe valor hardcoded 0.32 no código")
        else:
            print("✅ Valor hardcoded 0.32 removido")
            
        if "Decimal('0.08')" in content:
            print("⚠️  Ainda existe valor hardcoded 0.08 no código")
        else:
            print("✅ Valor hardcoded 0.08 removido")
        
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verificar_sintaxe()
