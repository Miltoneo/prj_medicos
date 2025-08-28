#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from medicos.models.relatorios import RelatorioMensalSocio
from medicos.models.base import Empresa, Socio

def verificar_cenario_especifico():
    print("=== VERIFICAÇÃO DO CENÁRIO ESPECÍFICO ===")
    print("URL: http://localhost:8000/medicos/relatorio-mensal-socio/4/?mes_ano=2025-06&socio_id=7")
    print()
    
    # Buscar empresa e sócio específicos
    try:
        empresa = Empresa.objects.get(id=4)
        socio = Socio.objects.get(id=7)
        print(f"✅ Empresa: {empresa.nome_fantasia} (ID: {empresa.id})")
        print(f"✅ Sócio: {socio.pessoa.name} (ID: {socio.id})")
    except (Empresa.DoesNotExist, Socio.DoesNotExist) as e:
        print(f"❌ Erro ao buscar empresa ou sócio: {e}")
        return
    
    print("\n=== VERIFICAÇÃO DOS RELATÓRIOS ===")
    
    # Verificar relatório de junho/2025
    junho_2025 = datetime(2025, 6, 1)
    try:
        rel_junho = RelatorioMensalSocio.objects.get(
            empresa=empresa,
            socio=socio,
            competencia=junho_2025
        )
        print(f"📊 JUNHO/2025:")
        print(f"   impostos_total (IMPOSTO A PROVISIONAR): {rel_junho.impostos_total}")
        print(f"   imposto_provisionado_mes_anterior: {rel_junho.imposto_provisionado_mes_anterior}")
        
        # Este valor deveria aparecer no relatório de julho
        valor_esperado_julho = rel_junho.impostos_total
        print(f"   👉 Este valor deveria aparecer em JULHO como: {valor_esperado_julho}")
        
    except RelatorioMensalSocio.DoesNotExist:
        print(f"❌ JUNHO/2025: Relatório não encontrado")
        valor_esperado_julho = Decimal('0')
    
    # Verificar relatório de julho/2025  
    julho_2025 = datetime(2025, 7, 1)
    try:
        rel_julho = RelatorioMensalSocio.objects.get(
            empresa=empresa,
            socio=socio,
            competencia=julho_2025
        )
        print(f"\n📊 JULHO/2025:")
        print(f"   impostos_total (IMPOSTO A PROVISIONAR): {rel_julho.impostos_total}")
        print(f"   imposto_provisionado_mes_anterior: {rel_julho.imposto_provisionado_mes_anterior}")
        
        # Verificar se está correto
        if rel_julho.imposto_provisionado_mes_anterior == valor_esperado_julho:
            print(f"   ✅ VALOR CORRETO! ({rel_julho.imposto_provisionado_mes_anterior})")
        else:
            print(f"   ❌ VALOR INCORRETO!")
            print(f"      Atual: {rel_julho.imposto_provisionado_mes_anterior}")
            print(f"      Esperado: {valor_esperado_julho}")
            
            # Corrigir o valor
            print(f"\n🔧 CORRIGINDO VALOR...")
            rel_julho.imposto_provisionado_mes_anterior = valor_esperado_julho
            rel_julho.save()
            print(f"   ✅ Valor corrigido para: {valor_esperado_julho}")
            
    except RelatorioMensalSocio.DoesNotExist:
        print(f"❌ JULHO/2025: Relatório não encontrado")
    
    print("\n=== TESTE MANUAL DO CÁLCULO ===")
    # Simular o cálculo do builder
    competencia_julho = datetime(2025, 7, 1)
    
    if competencia_julho.month == 1:
        mes_anterior = competencia_julho.replace(year=competencia_julho.year - 1, month=12, day=1)
    else:
        mes_anterior = competencia_julho.replace(month=competencia_julho.month - 1, day=1)
    
    print(f"Competência atual: {competencia_julho.strftime('%Y-%m')}")
    print(f"Mês anterior calculado: {mes_anterior.strftime('%Y-%m')}")
    
    try:
        relatorio_mes_anterior = RelatorioMensalSocio.objects.get(
            empresa=empresa,
            socio=socio,
            competencia=mes_anterior
        )
        valor_calculado = relatorio_mes_anterior.impostos_total or Decimal('0')
        print(f"✅ Valor calculado pelo builder: {valor_calculado}")
    except RelatorioMensalSocio.DoesNotExist:
        valor_calculado = Decimal('0')
        print(f"❌ Builder retornaria: {valor_calculado} (relatório não encontrado)")

if __name__ == "__main__":
    verificar_cenario_especifico()
