#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from medicos.models.relatorios import RelatorioMensalSocio
from medicos.models.base import Empresa, Socio

def debug_imposto_anterior():
    print("=== DEBUG: Imposto Provisionado Mês Anterior ===\n")
    
    # Buscar todos os relatórios existentes
    relatorios = RelatorioMensalSocio.objects.all().order_by('-competencia')[:10]
    
    print(f"Total de relatórios no sistema: {RelatorioMensalSocio.objects.count()}")
    print("\nÚltimos 10 relatórios:")
    for rel in relatorios:
        print(f"ID: {rel.id} | Competência: {rel.competencia.strftime('%Y-%m')} | "
              f"Empresa: {rel.empresa.nome_fantasia} | Sócio: {rel.socio.pessoa.name}")
        print(f"  impostos_total: {rel.impostos_total}")
        print(f"  imposto_provisionado_mes_anterior: {rel.imposto_provisionado_mes_anterior}")
        print()
    
    # Testar o cálculo manual do mês anterior
    if relatorios:
        rel_atual = relatorios[0]
        competencia_atual = rel_atual.competencia
        
        print(f"=== TESTE MANUAL ===")
        print(f"Relatório atual: {competencia_atual.strftime('%Y-%m')}")
        
        # Calcular mês anterior usando a mesma lógica do builder
        if competencia_atual.month == 1:
            mes_anterior = competencia_atual.replace(year=competencia_atual.year - 1, month=12, day=1)
        else:
            mes_anterior = competencia_atual.replace(month=competencia_atual.month - 1, day=1)
        
        print(f"Mês anterior calculado: {mes_anterior.strftime('%Y-%m')}")
        
        # Buscar relatório do mês anterior
        try:
            rel_anterior = RelatorioMensalSocio.objects.get(
                empresa=rel_atual.empresa,
                socio=rel_atual.socio,
                competencia=mes_anterior
            )
            print(f"✅ Relatório mês anterior encontrado!")
            print(f"   impostos_total do mês anterior: {rel_anterior.impostos_total}")
            print(f"   Valor que deveria aparecer: {rel_anterior.impostos_total or 0}")
        except RelatorioMensalSocio.DoesNotExist:
            print(f"❌ Relatório do mês anterior NÃO encontrado")
            print(f"   Valor correto: 0,00")
        
        # Verificar se o valor está sendo salvo corretamente no relatório atual
        print(f"\nValor salvo no relatório atual:")
        print(f"   imposto_provisionado_mes_anterior: {rel_atual.imposto_provisionado_mes_anterior}")

if __name__ == "__main__":
    debug_imposto_anterior()
