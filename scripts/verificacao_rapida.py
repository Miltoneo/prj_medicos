#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificação rápida: Status da integração de despesas e receitas no extrato
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio
from medicos.models import NotaFiscalRateioMedico
from medicos.models.conta_corrente import MovimentacaoContaCorrente

def verificacao_rapida():
    """Verificação rápida do status de integração"""
    
    print("=" * 70)
    print("VERIFICAÇÃO RÁPIDA: Status da Integração")
    print("=" * 70)
    
    # Contar despesas de sócio
    total_despesas = DespesaSocio.objects.count()
    despesas_integradas = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Despesa ID:"
    ).count()
    
    # Contar rateios de notas fiscais
    total_rateios = NotaFiscalRateioMedico.objects.count()
    rateios_integrados = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Rateio NF ID:"
    ).count()
    
    # Total de movimentações no extrato
    total_movimentacoes = MovimentacaoContaCorrente.objects.count()
    
    print(f"💰 DESPESAS DE SÓCIO:")
    print(f"   📊 Total no sistema: {total_despesas}")
    print(f"   🏦 Integradas no extrato: {despesas_integradas}")
    if total_despesas > 0:
        taxa_despesas = (despesas_integradas / total_despesas) * 100
        print(f"   📈 Taxa de integração: {taxa_despesas:.1f}%")
    
    print()
    print(f"📄 RECEITAS DE NOTAS FISCAIS:")
    print(f"   📊 Total de rateios no sistema: {total_rateios}")
    print(f"   🏦 Integrados no extrato: {rateios_integrados}")
    if total_rateios > 0:
        taxa_rateios = (rateios_integrados / total_rateios) * 100
        print(f"   📈 Taxa de integração: {taxa_rateios:.1f}%")
    
    print()
    print(f"🏦 EXTRATO CONTA CORRENTE:")
    print(f"   💸 Movimentações de despesas: {despesas_integradas}")
    print(f"   💰 Movimentações de receitas: {rateios_integrados}")
    print(f"   📋 Total de movimentações: {total_movimentacoes}")
    
    # Status geral
    print()
    if despesas_integradas > 0 and rateios_integrados > 0:
        print("✅ SUCESSO: Despesas e receitas foram integradas ao extrato!")
    elif despesas_integradas > 0:
        print("⚠ PARCIAL: Apenas despesas foram integradas")
    elif rateios_integrados > 0:
        print("⚠ PARCIAL: Apenas receitas foram integradas")
    else:
        print("❌ PENDENTE: Nenhuma integração realizada")
    
    print("=" * 70)

if __name__ == "__main__":
    verificacao_rapida()
