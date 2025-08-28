#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from medicos.models.relatorios import RelatorioMensalSocio
from medicos.models.base import Empresa, Socio

def test_imposto_anterior():
    print("=== Teste do Imposto Provisionado Mês Anterior ===")
    
    # Buscar empresas e sócios
    empresas = Empresa.objects.all()
    print(f"Encontradas {empresas.count()} empresas no sistema")
    
    for empresa in empresas:
        print(f"\nEmpresa: {empresa.nome_fantasia} (ID: {empresa.id})")
        socios = Socio.objects.filter(empresa=empresa, ativo=True)
        print(f"Sócios ativos: {socios.count()}")
        
        for socio in socios:
            print(f"  Sócio: {socio.pessoa.name} (ID: {socio.id})")
            
            # Buscar relatórios dos últimos 3 meses
            hoje = datetime.now()
            for i in range(3):
                mes_ref = (hoje.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                relatorios = RelatorioMensalSocio.objects.filter(
                    empresa=empresa,
                    socio=socio,
                    competencia__year=mes_ref.year,
                    competencia__month=mes_ref.month
                )
                
                if relatorios.exists():
                    relatorio = relatorios.first()
                    print(f"    {mes_ref.strftime('%Y-%m')}: impostos_total={relatorio.impostos_total}, imposto_provisionado_mes_anterior={relatorio.imposto_provisionado_mes_anterior}")
                else:
                    print(f"    {mes_ref.strftime('%Y-%m')}: Sem relatório")

if __name__ == "__main__":
    test_imposto_anterior()
