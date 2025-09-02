#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificação completa: Confirma integração de despesas e notas fiscais no extrato
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio
from medicos.models import NotaFiscal
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.base import Socio

def verificar_integracao_completa():
    """Verifica integração completa de despesas e notas fiscais no extrato"""
    
    print("=" * 90)
    print("VERIFICAÇÃO COMPLETA: Integração Despesas + Notas Fiscais → Extrato Conta Corrente")
    print("=" * 90)
    
    # Buscar todos os sócios com transações
    socios = Socio.objects.all().order_by('pessoa__name')
    
    print(f"👥 Total de sócios no sistema: {socios.count()}")
    print()
    
    resumo_global = {
        'despesas_total': 0,
        'despesas_integradas': 0,
        'nf_total': 0,
        'nf_integradas': 0,
        'movimentacoes_despesas': 0,
        'movimentacoes_nf': 0
    }
    
    for socio in socios:
        socio_nome = getattr(getattr(socio, 'pessoa', None), 'name', str(socio))
        
        # Despesas do sócio
        despesas = DespesaSocio.objects.filter(socio=socio)
        despesas_count = despesas.count()
        
        # Notas fiscais recebidas do sócio
        notas_fiscais = NotaFiscal.objects.filter(socio=socio, tipo='RECEBIDA')
        nf_count = notas_fiscais.count()
        
        if despesas_count == 0 and nf_count == 0:
            continue  # Pular sócios sem transações
        
        print(f"👤 {socio_nome}")
        
        # Verificar integração de despesas
        despesas_integradas = 0
        if despesas_count > 0:
            for despesa in despesas:
                existe = MovimentacaoContaCorrente.objects.filter(
                    socio=despesa.socio,
                    data_movimentacao=despesa.data,
                    valor=-abs(despesa.valor),  # Negativo para débito
                    historico_complementar__icontains=f"Despesa ID: {despesa.id}"
                ).exists()
                if existe:
                    despesas_integradas += 1
        
        # Verificar integração de notas fiscais
        nf_integradas = 0
        if nf_count > 0:
            for nf in notas_fiscais:
                if nf.valor_liquido and nf.valor_liquido > 0:
                    existe = MovimentacaoContaCorrente.objects.filter(
                        socio=nf.socio,
                        data_movimentacao=nf.data_competencia,
                        valor=abs(nf.valor_liquido),  # Positivo para crédito
                        historico_complementar__icontains=f"Nota Fiscal ID: {nf.id}"
                    ).exists()
                    if existe:
                        nf_integradas += 1
        
        # Exibir estatísticas do sócio
        print(f"   💰 Despesas: {despesas_integradas}/{despesas_count} integradas")
        print(f"   📄 NF Recebidas: {nf_integradas}/{nf_count} integradas")
        
        # Atualizar resumo global
        resumo_global['despesas_total'] += despesas_count
        resumo_global['despesas_integradas'] += despesas_integradas
        resumo_global['nf_total'] += nf_count
        resumo_global['nf_integradas'] += nf_integradas
        
        print()
    
    # Contar movimentações no extrato
    movimentacoes_despesas = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Despesa ID:"
    ).count()
    
    movimentacoes_nf = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Nota Fiscal ID:"
    ).count()
    
    resumo_global['movimentacoes_despesas'] = movimentacoes_despesas
    resumo_global['movimentacoes_nf'] = movimentacoes_nf
    
    # Resumo final
    print("=" * 90)
    print("RESUMO GLOBAL:")
    print("-" * 90)
    
    print("💰 DESPESAS DE SÓCIO:")
    print(f"   📊 Total no sistema: {resumo_global['despesas_total']}")
    print(f"   ✅ Integradas no extrato: {resumo_global['despesas_integradas']}")
    print(f"   🏦 Movimentações débito no extrato: {resumo_global['movimentacoes_despesas']}")
    if resumo_global['despesas_total'] > 0:
        taxa_despesas = (resumo_global['despesas_integradas'] / resumo_global['despesas_total']) * 100
        print(f"   📈 Taxa de integração: {taxa_despesas:.1f}%")
    
    print()
    print("📄 NOTAS FISCAIS RECEBIDAS:")
    print(f"   📊 Total no sistema: {resumo_global['nf_total']}")
    print(f"   ✅ Integradas no extrato: {resumo_global['nf_integradas']}")
    print(f"   🏦 Movimentações crédito no extrato: {resumo_global['movimentacoes_nf']}")
    if resumo_global['nf_total'] > 0:
        taxa_nf = (resumo_global['nf_integradas'] / resumo_global['nf_total']) * 100
        print(f"   📈 Taxa de integração: {taxa_nf:.1f}%")
    
    print()
    print("🏦 EXTRATO CONTA CORRENTE:")
    total_movimentacoes = resumo_global['movimentacoes_despesas'] + resumo_global['movimentacoes_nf']
    print(f"   💸 Total de débitos (despesas): {resumo_global['movimentacoes_despesas']}")
    print(f"   💰 Total de créditos (NF recebidas): {resumo_global['movimentacoes_nf']}")
    print(f"   📋 Total de movimentações: {total_movimentacoes}")
    
    # Verificar consistência
    print()
    print("🔍 VERIFICAÇÃO DE CONSISTÊNCIA:")
    inconsistencias = 0
    
    if resumo_global['despesas_integradas'] != resumo_global['movimentacoes_despesas']:
        print(f"   ⚠ INCONSISTÊNCIA: Despesas integradas ({resumo_global['despesas_integradas']}) ≠ Movimentações débito ({resumo_global['movimentacoes_despesas']})")
        inconsistencias += 1
    
    if resumo_global['nf_integradas'] != resumo_global['movimentacoes_nf']:
        print(f"   ⚠ INCONSISTÊNCIA: NF integradas ({resumo_global['nf_integradas']}) ≠ Movimentações crédito ({resumo_global['movimentacoes_nf']})")
        inconsistencias += 1
    
    if inconsistencias == 0:
        print("   ✅ Todas as verificações de consistência passaram!")
    
    print("=" * 90)

if __name__ == "__main__":
    verificar_integracao_completa()
