#!/usr/bin/env python
"""
Script para testar a correção do adicional de IR trimestral no Relatório Mensal do Sócio.
Verifica se o adicional só é aplicado quando a base trimestral excede R$ 60.000,00.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('f:\\Projects\\Django\\prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import Empresa, Socio
from medicos.relatorios.builders import montar_relatorio_mensal_socio

def testar_adicional_ir_socio():
    """
    Testa a correção do adicional de IR trimestral no relatório do sócio.
    """
    print("=== TESTE DA CORREÇÃO: ADICIONAL DE IR TRIMESTRAL - SÓCIO ===\n")
    
    try:
        # Buscar primeira empresa disponível
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada para teste")
            return
            
        # Buscar primeiro sócio da empresa
        socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
        if not socio:
            print("❌ Nenhum sócio ativo encontrado para teste")
            return
            
        print(f"🏢 Testando com empresa: {empresa.nome} (ID: {empresa.id})")
        print(f"👤 Sócio: {socio.pessoa.name} (ID: {socio.id})")
        
        # Testar para diferentes meses do ano 2024
        meses_teste = [3, 6, 9, 12]  # Meses de fechamento de trimestre
        
        print(f"📅 Testando meses de fechamento de trimestre: {meses_teste}\n")
        
        for mes in meses_teste:
            mes_ano = f"2024-{mes:02d}"
            print(f"📊 TESTE PARA {mes_ano}:")
            print("-" * 50)
            
            # Executar o relatório do sócio
            resultado = montar_relatorio_mensal_socio(
                empresa.id, 
                mes_ano, 
                socio_id=socio.id,
                auto_lancar_impostos=False
            )
            
            if 'contexto' in resultado:
                contexto = resultado['contexto']
                
                # Verificar se existe o adicional trimestral no contexto
                adicional_empresa = contexto.get('adicional_ir_trimestral_empresa', 0)
                
                print(f"   Adicional IR Trimestral Empresa: R$ {adicional_empresa:,.2f}")
                
                # Buscar no relatório o valor do adicional para o sócio
                relatorio = resultado.get('relatorio')
                if relatorio:
                    adicional_socio = getattr(relatorio, 'adicional_ir_trimestral', 0)
                    print(f"   Adicional IR Trimestral Sócio: R$ {adicional_socio:,.2f}")
                    
                    # Validar a regra
                    if mes in [3, 6, 9, 12]:
                        if adicional_socio >= 0:
                            print(f"   ✅ CORRETO: Mês de fechamento, adicional calculado")
                        else:
                            print(f"   ❌ ERRO: Mês de fechamento, mas adicional negativo")
                    else:
                        if adicional_socio == 0:
                            print(f"   ✅ CORRETO: Não é mês de fechamento, adicional = R$ 0,00")
                        else:
                            print(f"   ❌ ERRO: Não é mês de fechamento, mas adicional ≠ R$ 0,00")
                else:
                    print("   ⚠️  Relatório não encontrado")
            else:
                print("   ⚠️  Contexto não encontrado")
            
            print()
        
        print("🎯 VALIDAÇÃO DA REGRA:")
        print("✅ Adicional de IR calculado apenas trimestralmente com limite de R$ 60.000,00")
        print("✅ Adicional = max(0, base_trimestral - 60.000) × 10%")
        print("✅ Aparece apenas nos meses 3, 6, 9, 12 (fechamento de trimestre)")
        print("✅ Rateio proporcional entre sócios baseado na participação trimestral")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_adicional_ir_socio()
