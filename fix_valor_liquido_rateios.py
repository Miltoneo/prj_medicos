#!/usr/bin/env python
"""
Script para corrigir valores líquidos dos rateios existentes
Executa novamente o cálculo considerando o campo "outros"

Execução: python fix_valor_liquido_rateios.py
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
    from medicos.models.fiscal import NotaFiscalRateioMedico
    print("✅ Imports realizados com sucesso")
except Exception as e:
    print(f"❌ Erro nos imports: {e}")
    sys.exit(1)

def corrigir_valores_liquidos():
    print("\n" + "="*70)
    print("CORREÇÃO - Valores líquidos dos rateios considerando 'outros'")
    print("="*70)
    
    try:
        # Buscar todos os rateios existentes
        rateios = NotaFiscalRateioMedico.objects.all()
        total_rateios = rateios.count()
        print(f"✅ Encontrados {total_rateios} rateios para verificar")
        
        if total_rateios == 0:
            print("ℹ️  Nenhum rateio encontrado para corrigir")
            return
        
        rateios_corrigidos = 0
        
        for i, rateio in enumerate(rateios, 1):
            if i % 10 == 0:
                print(f"   Processando rateio {i}/{total_rateios}...")
            
            # Armazenar valor líquido anterior
            valor_liquido_anterior = rateio.valor_liquido_medico
            
            # Forçar recálculo salvando o rateio
            # O método save() agora inclui o desconto do campo "outros"
            rateio.save()
            
            # Recarregar do banco para obter o valor atualizado
            rateio.refresh_from_db()
            valor_liquido_novo = rateio.valor_liquido_medico
            
            # Verificar se houve mudança significativa (diferença > 0.01)
            diferenca = abs(float(valor_liquido_anterior) - float(valor_liquido_novo))
            if diferenca > 0.01:
                rateios_corrigidos += 1
                if rateios_corrigidos <= 5:  # Mostrar apenas os primeiros 5 exemplos
                    print(f"   📝 Rateio {rateio.id} - NF {rateio.nota_fiscal.numero}")
                    print(f"      Médico: {rateio.medico.pessoa.name}")
                    print(f"      Valor líquido anterior: R$ {valor_liquido_anterior:.2f}")
                    print(f"      Valor líquido corrigido: R$ {valor_liquido_novo:.2f}")
                    print(f"      Diferença: R$ {diferenca:.2f}")
                    
                    # Mostrar detalhes do cálculo
                    if rateio.nota_fiscal.val_outros:
                        nf = rateio.nota_fiscal
                        proporcao = float(rateio.valor_bruto_medico) / float(nf.val_bruto)
                        outros_rateado = float(nf.val_outros) * proporcao
                        print(f"      'Outros' da NF: R$ {nf.val_outros:.2f}")
                        print(f"      'Outros' rateado: R$ {outros_rateado:.2f}")
                    print()
        
        print(f"\n📊 RESULTADO DA CORREÇÃO:")
        print(f"   Total de rateios processados: {total_rateios}")
        print(f"   Rateios corrigidos: {rateios_corrigidos}")
        print(f"   Rateios sem alteração: {total_rateios - rateios_corrigidos}")
        
        if rateios_corrigidos > 0:
            print(f"\n✅ CORREÇÃO CONCLUÍDA!")
            print(f"✅ {rateios_corrigidos} valores líquidos foram corrigidos")
            print(f"✅ Campo 'outros' agora é deduzido corretamente")
        else:
            print(f"\nℹ️  Nenhum valor precisou ser corrigido")
            print(f"ℹ️  Todos os valores já estavam corretos")
        
    except Exception as e:
        print(f"❌ Erro na correção: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    corrigir_valores_liquidos()
