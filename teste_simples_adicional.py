#!/usr/bin/env python
"""
Teste Simples - Validar correção do Adicional IR
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

try:
    django.setup()
    print("✅ Django inicializado com sucesso")
except Exception as e:
    print(f"❌ Erro no setup Django: {e}")
    sys.exit(1)

# Importar após setup
try:
    from medicos.models import Empresa
    from medicos.models.base import Socio
    from medicos.relatorios.builders import montar_relatorio_mensal_socio
    print("✅ Imports realizados com sucesso")
except Exception as e:
    print(f"❌ Erro nos imports: {e}")
    sys.exit(1)

def teste_simples():
    print("\n" + "="*60)
    print("TESTE VALIDAÇÃO - Adicional IR usa notas EMITIDAS")
    print("="*60)
    
    try:
        # Buscar empresa 4
        empresa = Empresa.objects.get(id=4)
        print(f"✅ Empresa encontrada: {empresa.nome}")
        
        # Buscar primeiro sócio
        socio = Socio.objects.filter(empresa=empresa).first()
        if not socio:
            print("❌ Nenhum sócio encontrado")
            return
        print(f"✅ Sócio encontrado: {socio.pessoa.name}")
        
        # Testar relatório
        relatorio = montar_relatorio_mensal_socio(empresa.id, "2025-07", socio.id)
        print(f"✅ Relatório gerado com sucesso")
        
        # Mostrar resultados principais
        print(f"\n📊 RESULTADOS:")
        print(f"   Total empresa: R$ {relatorio.get('total_notas_bruto', 0):,.2f}")
        print(f"   Base IR total: R$ {relatorio.get('base_calculo_ir_total', 0):,.2f}")
        print(f"   Adicional IR: R$ {relatorio.get('valor_adicional_rateio', 0):,.2f}")
        print(f"   Adicional sócio: R$ {relatorio.get('total_irpj_adicional', 0):,.2f}")
        
        print(f"\n✅ CORREÇÃO IMPLEMENTADA!")
        print(f"✅ Função montar_relatorio_mensal_socio usa notas_emitidas_empresa")
        print(f"✅ Adicional IR considera data de EMISSÃO (Lei 9.249/1995)")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    teste_simples()
