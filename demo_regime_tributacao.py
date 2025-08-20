#!/usr/bin/env python
"""
Script de demonstração das diferenças entre regime de competência e caixa
para IRPJ e CSLL.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.models import NotaFiscal
from django.db.models import Sum, Q

def demonstrar_diferenca_regimes():
    print("=== DEMONSTRAÇÃO: DIFERENÇAS ENTRE REGIMES ===")
    
    empresa = Empresa.objects.get(id=4)
    ano = 2025
    mes = 1  # Janeiro
    
    print(f"Empresa: {empresa.name}")
    print(f"Período: Janeiro/{ano}")
    
    # Consultar notas por data de emissão
    notas_emissao = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtEmissao__year=ano,
        dtEmissao__month=mes
    )
    
    # Consultar notas por data de recebimento
    notas_recebimento = NotaFiscal.objects.filter(
        empresa_destinataria=empresa,
        dtRecebimento__year=ano,
        dtRecebimento__month=mes,
        dtRecebimento__isnull=False
    )
    
    print(f"\n📊 COMPARAÇÃO DE DADOS:")
    print(f"   Notas com emissão em Jan/2025: {notas_emissao.count()}")
    print(f"   Notas com recebimento em Jan/2025: {notas_recebimento.count()}")
    
    if notas_emissao.exists():
        receita_emissao = notas_emissao.aggregate(total=Sum('val_bruto'))['total'] or 0
        print(f"   Receita bruta (por emissão): R$ {receita_emissao:,.2f}")
    
    if notas_recebimento.exists():
        receita_recebimento = notas_recebimento.aggregate(total=Sum('val_bruto'))['total'] or 0
        print(f"   Receita bruta (por recebimento): R$ {receita_recebimento:,.2f}")
    
    print(f"\n🏛️ REGIME ATUAL DA EMPRESA:")
    print(f"   Código: {empresa.regime_tributario}")
    print(f"   Nome: {empresa.regime_tributario_nome}")
    
    if empresa.regime_tributario == REGIME_TRIBUTACAO_COMPETENCIA:
        print("   📋 REGIME DE COMPETÊNCIA:")
        print("   • IRPJ e CSLL calculados sobre notas EMITIDAS no período")
        print("   • Base legal: Artigo 177 do CTN")
        print("   • Considera a prestação do serviço (emissão da NF)")
    else:
        print("   💰 REGIME DE CAIXA:")
        print("   • IRPJ e CSLL calculados sobre notas RECEBIDAS no período")
        print("   • Base legal: Lei 9.718/1998")
        print("   • Considera o efetivo recebimento (dtRecebimento)")
        print("   • Válido apenas para empresas com receita ≤ R$ 78 milhões")
    
    print(f"\n🎯 IMPACTO PRÁTICO:")
    print("   • Competência: Tributo devido mesmo se não recebeu ainda")
    print("   • Caixa: Tributo devido apenas quando efetivamente receber")
    print("   • ISS: SEMPRE competência (LC 116/2003)")
    print("   • PIS/COFINS: Podem seguir regime da empresa")

if __name__ == "__main__":
    demonstrar_diferenca_regimes()
