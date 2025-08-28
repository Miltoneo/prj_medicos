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

def criar_relatorio_teste():
    # Buscar empresa e sócio
    empresa = Empresa.objects.first()
    socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
    
    if not empresa or not socio:
        print("Empresa ou sócio não encontrado")
        return
    
    print(f"Empresa: {empresa.nome_fantasia}")
    print(f"Sócio: {socio.pessoa.name}")
    
    # Criar relatório de julho/2025 com impostos para testar
    julho_2025 = datetime(2025, 7, 1)
    
    relatório_julho, created = RelatorioMensalSocio.objects.update_or_create(
        empresa=empresa,
        socio=socio,
        competencia=julho_2025,
        defaults={
            'impostos_total': Decimal('1500.75'),
            'data_geracao': datetime.now(),
            'despesas_total': Decimal('0'),
            'receita_liquida': Decimal('0'),
            'saldo_a_transferir': Decimal('0'),
            'imposto_provisionado_mes_anterior': Decimal('0')
        }
    )
    
    if created:
        print(f"✅ Relatório de julho/2025 CRIADO com impostos_total: {relatório_julho.impostos_total}")
    else:
        print(f"📝 Relatório de julho/2025 ATUALIZADO com impostos_total: {relatório_julho.impostos_total}")
    
    print("\n🔍 Agora gere o relatório de agosto/2025 na interface para ver o imposto provisionado!")
    print("O valor deve aparecer como: 1.500,75")

if __name__ == "__main__":
    criar_relatorio_teste()
