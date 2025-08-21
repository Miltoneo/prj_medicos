#!/usr/bin/env python
"""
Script para Recalcular Rateios Existentes
Aplicar a correção aos rateios já criados

Execução: python recalcular_rateios_existentes.py
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from decimal import Decimal
from medicos.models.fiscal import NotaFiscalRateioMedico

def recalcular_rateios_existentes():
    """
    Recalcular todos os rateios existentes com a nova lógica
    """
    print("=" * 80)
    print("RECÁLCULO DE RATEIOS EXISTENTES")
    print("=" * 80)
    
    try:
        # Buscar todos os rateios existentes
        rateios = NotaFiscalRateioMedico.objects.all()
        total_rateios = rateios.count()
        
        print(f"✓ Encontrados {total_rateios} rateios para recalcular")
        
        if total_rateios == 0:
            print("ℹ️  Nenhum rateio encontrado para recalcular")
            return True
        
        rateios_atualizados = 0
        rateios_com_erro = 0
        
        for rateio in rateios:
            try:
                print(f"\n📝 Processando rateio {rateio.id}:")
                print(f"   NF: {rateio.nota_fiscal.numero}")
                print(f"   Médico: {rateio.medico.pessoa.name}")
                print(f"   Valor Bruto: R$ {rateio.valor_bruto_medico:,.2f}")
                
                # Valores antigos (para comparação)
                valores_antigos = {
                    'iss': rateio.valor_iss_medico,
                    'pis': rateio.valor_pis_medico,
                    'cofins': rateio.valor_cofins_medico,
                    'ir': rateio.valor_ir_medico,
                    'csll': rateio.valor_csll_medico,
                    'liquido': rateio.valor_liquido_medico
                }
                
                # Forçar recálculo salvando novamente
                rateio.save()
                
                # Recarregar do banco
                rateio.refresh_from_db()
                
                # Verificar se houve mudança
                mudancas = []
                if valores_antigos['iss'] != rateio.valor_iss_medico:
                    mudancas.append(f"ISS: R$ {valores_antigos['iss']:,.2f} → R$ {rateio.valor_iss_medico:,.2f}")
                if valores_antigos['pis'] != rateio.valor_pis_medico:
                    mudancas.append(f"PIS: R$ {valores_antigos['pis']:,.2f} → R$ {rateio.valor_pis_medico:,.2f}")
                if valores_antigos['cofins'] != rateio.valor_cofins_medico:
                    mudancas.append(f"COFINS: R$ {valores_antigos['cofins']:,.2f} → R$ {rateio.valor_cofins_medico:,.2f}")
                if valores_antigos['ir'] != rateio.valor_ir_medico:
                    mudancas.append(f"IR: R$ {valores_antigos['ir']:,.2f} → R$ {rateio.valor_ir_medico:,.2f}")
                if valores_antigos['csll'] != rateio.valor_csll_medico:
                    mudancas.append(f"CSLL: R$ {valores_antigos['csll']:,.2f} → R$ {rateio.valor_csll_medico:,.2f}")
                if valores_antigos['liquido'] != rateio.valor_liquido_medico:
                    mudancas.append(f"Líquido: R$ {valores_antigos['liquido']:,.2f} → R$ {rateio.valor_liquido_medico:,.2f}")
                
                if mudancas:
                    print(f"   ✅ Rateio atualizado:")
                    for mudanca in mudancas:
                        print(f"      • {mudanca}")
                else:
                    print(f"   ➖ Sem alterações necessárias")
                
                rateios_atualizados += 1
                
            except Exception as e:
                print(f"   ❌ Erro ao processar rateio {rateio.id}: {e}")
                rateios_com_erro += 1
        
        print(f"\n📊 RESULTADO DO RECÁLCULO:")
        print(f"   Total processado: {total_rateios}")
        print(f"   Atualizados: {rateios_atualizados}")
        print(f"   Com erro: {rateios_com_erro}")
        
        if rateios_com_erro == 0:
            print(f"\n✅ SUCESSO: Todos os rateios foram recalculados")
            return True
        else:
            print(f"\n⚠️  ATENÇÃO: {rateios_com_erro} rateios com erro")
            return False
        
    except Exception as e:
        print(f"❌ ERRO geral: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Iniciando recálculo de rateios existentes...")
    
    resposta = input("\n⚠️  Este script irá recalcular TODOS os rateios existentes. Continuar? (s/N): ")
    
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        sucesso = recalcular_rateios_existentes()
        
        print("\n" + "=" * 80)
        if sucesso:
            print("🎉 RECÁLCULO CONCLUÍDO!")
            print("✅ Rateios atualizados com a nova lógica")
            print("✅ Valores agora baseados na NF original")
        else:
            print("💥 RECÁLCULO COM PROBLEMAS!")
            print("❌ Verificar erros acima")
        print("=" * 80)
    else:
        print("\n❌ Operação cancelada pelo usuário")
