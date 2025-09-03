#!/usr/bin/env python
import os
import sys
import django

# Adicionar o diretório do projeto ao Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

try:
    # Tentar importar a view modificada
    from medicos.views_relatorios import ApuracaoImpostosView
    print("✅ Sintaxe correta - nenhum erro encontrado")
    print("✅ View ApuracaoImpostosView importada com sucesso")
    
    # Verificar se as alíquotas estão sendo referenciadas corretamente
    from medicos.models.fiscal import Aliquotas
    print("✅ Modelo Aliquotas importado com sucesso")
    
    # Verificar os campos específicos
    fields = ['CSLL_ALIQUOTA', 'CSLL_PRESUNCAO_CONSULTA', 'CSLL_PRESUNCAO_OUTROS', 
              'IRPJ_ALIQUOTA', 'IRPJ_PRESUNCAO_CONSULTA', 'IRPJ_PRESUNCAO_OUTROS']
    
    for field in fields:
        if hasattr(Aliquotas, field):
            print(f"✅ Campo {field} encontrado no modelo")
        else:
            print(f"❌ Campo {field} NÃO encontrado no modelo")
            
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
except SyntaxError as e:
    print(f"❌ Erro de sintaxe: {e}")
except Exception as e:
    print(f"❌ Erro geral: {e}")
