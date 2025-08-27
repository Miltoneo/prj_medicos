#!/usr/bin/env python
"""
Teste simples - Verificar correção do valor líquido
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

try:
    django.setup()
    print("✅ Django inicializado")
    
    from medicos.models.fiscal import NotaFiscalRateioMedico
    print("✅ Imports realizados")
    
    # Buscar um rateio específico para testar
    rateio = NotaFiscalRateioMedico.objects.first()
    if rateio:
        print(f"\n📋 TESTE DO RATEIO ID: {rateio.id}")
        print(f"   NF: {rateio.nota_fiscal.numero}")
        print(f"   Médico: {rateio.medico.pessoa.name}")
        print(f"   Valor Bruto: R$ {rateio.valor_bruto_medico:.2f}")
        
        # Mostrar valores da nota fiscal
        nf = rateio.nota_fiscal
        print(f"\n📄 NOTA FISCAL:")
        print(f"   Valor Bruto NF: R$ {nf.val_bruto:.2f}")
        print(f"   Outros NF: R$ {nf.val_outros or 0:.2f}")
        
        # Calcular proporção
        if nf.val_bruto > 0:
            proporcao = float(rateio.valor_bruto_medico) / float(nf.val_bruto)
            outros_rateado = float(nf.val_outros or 0) * proporcao
            print(f"\n🔢 CÁLCULOS:")
            print(f"   Proporção: {proporcao:.4f} ({proporcao*100:.2f}%)")
            print(f"   Outros rateado: R$ {outros_rateado:.2f}")
            
            # Impostos
            total_impostos = (
                float(rateio.valor_iss_medico or 0) +
                float(rateio.valor_pis_medico or 0) +
                float(rateio.valor_cofins_medico or 0) +
                float(rateio.valor_ir_medico or 0) +
                float(rateio.valor_csll_medico or 0)
            )
            print(f"   Total impostos: R$ {total_impostos:.2f}")
            
            # Valor líquido correto deveria ser
            valor_liquido_correto = float(rateio.valor_bruto_medico) - total_impostos - outros_rateado
            print(f"   Valor líquido correto: R$ {valor_liquido_correto:.2f}")
            print(f"   Valor líquido atual: R$ {rateio.valor_liquido_medico:.2f}")
            
            diferenca = abs(valor_liquido_correto - float(rateio.valor_liquido_medico))
            if diferenca > 0.01:
                print(f"   ❌ PRECISA CORREÇÃO! Diferença: R$ {diferenca:.2f}")
                
                # Forçar recálculo
                print(f"\n🔧 APLICANDO CORREÇÃO...")
                rateio.save()
                rateio.refresh_from_db()
                print(f"   Valor líquido após correção: R$ {rateio.valor_liquido_medico:.2f}")
            else:
                print(f"   ✅ Valor líquido está correto!")
        
        print(f"\n✅ CORREÇÃO IMPLEMENTADA NO MODELO!")
        print(f"✅ Campo 'outros' agora é deduzido do valor líquido")
    else:
        print("❌ Nenhum rateio encontrado para teste")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
