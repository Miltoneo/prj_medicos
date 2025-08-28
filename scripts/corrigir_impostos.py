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

def corrigir_impostos_mes_anterior():
    print("=== CORREÇÃO DOS IMPOSTOS DO MÊS ANTERIOR ===\n")
    
    # Buscar todos os relatórios ordenados por competência
    relatorios = RelatorioMensalSocio.objects.all().order_by('empresa', 'socio', 'competencia')
    
    print(f"Total de relatórios encontrados: {relatorios.count()}\n")
    
    relatorios_corrigidos = 0
    
    for relatorio in relatorios:
        # Calcular competência do mês anterior
        competencia = relatorio.competencia
        
        if competencia.month == 1:
            mes_anterior = competencia.replace(year=competencia.year - 1, month=12, day=1)
        else:
            mes_anterior = competencia.replace(month=competencia.month - 1, day=1)
        
        # Buscar relatório do mês anterior
        try:
            relatorio_anterior = RelatorioMensalSocio.objects.get(
                empresa=relatorio.empresa,
                socio=relatorio.socio,
                competencia=mes_anterior
            )
            
            # Valor correto = impostos_total do mês anterior
            valor_correto = relatorio_anterior.impostos_total or Decimal('0')
            valor_atual = relatorio.imposto_provisionado_mes_anterior or Decimal('0')
            
            # Se o valor estiver incorreto, corrigir
            if valor_atual != valor_correto:
                print(f"📊 {relatorio.empresa.nome_fantasia} | {relatorio.socio.pessoa.name}")
                print(f"   Competência: {competencia.strftime('%Y-%m')}")
                print(f"   Valor atual: {valor_atual}")
                print(f"   Valor correto: {valor_correto}")
                
                # Atualizar o valor
                relatorio.imposto_provisionado_mes_anterior = valor_correto
                relatorio.save()
                
                print(f"   ✅ CORRIGIDO!\n")
                relatorios_corrigidos += 1
            
        except RelatorioMensalSocio.DoesNotExist:
            # Não existe relatório do mês anterior, valor deve ser 0
            if relatorio.imposto_provisionado_mes_anterior != Decimal('0'):
                print(f"📊 {relatorio.empresa.nome_fantasia} | {relatorio.socio.pessoa.name}")
                print(f"   Competência: {competencia.strftime('%Y-%m')}")
                print(f"   Mês anterior ({mes_anterior.strftime('%Y-%m')}) não encontrado")
                print(f"   Valor atual: {relatorio.imposto_provisionado_mes_anterior}")
                print(f"   Valor correto: 0,00")
                
                relatorio.imposto_provisionado_mes_anterior = Decimal('0')
                relatorio.save()
                
                print(f"   ✅ CORRIGIDO!\n")
                relatorios_corrigidos += 1
    
    print(f"🎉 CONCLUÍDO! {relatorios_corrigidos} relatórios corrigidos.")
    
    # Verificar especificamente o cenário do usuário
    print("\n=== VERIFICAÇÃO DO CENÁRIO ESPECÍFICO ===")
    try:
        empresa_4 = Empresa.objects.get(id=4)
        socio_7 = Socio.objects.get(id=7)
        
        # Relatório de julho/2025
        julho_2025 = datetime(2025, 7, 1)
        rel_julho = RelatorioMensalSocio.objects.get(
            empresa=empresa_4,
            socio=socio_7,
            competencia=julho_2025
        )
        
        print(f"📈 Relatório JULHO/2025:")
        print(f"   Empresa: {empresa_4.nome_fantasia}")
        print(f"   Sócio: {socio_7.pessoa.name}")
        print(f"   IMPOSTO PROVISIONADO MÊS ANTERIOR: {rel_julho.imposto_provisionado_mes_anterior}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar cenário específico: {e}")

if __name__ == "__main__":
    corrigir_impostos_mes_anterior()
