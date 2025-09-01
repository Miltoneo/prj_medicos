#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificação: Confirma quantas despesas foram incluídas no extrato da conta corrente
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.base import Socio

def verificar_integracao_despesas():
    """Verifica quantas despesas foram integradas ao extrato da conta corrente"""
    
    print("=" * 80)
    print("VERIFICAÇÃO: Integração Despesas de Sócio → Extrato Conta Corrente")
    print("=" * 80)
    
    # Buscar todas as despesas de sócio
    todas_despesas = DespesaSocio.objects.all().order_by('socio__pessoa__name', 'data')
    total_despesas = todas_despesas.count()
    
    print(f"📊 Total de despesas de sócio no sistema: {total_despesas}")
    
    if total_despesas == 0:
        print("⚠ Nenhuma despesa de sócio encontrada no sistema")
        return
    
    # Verificar integração por sócio
    socios_com_despesas = Socio.objects.filter(
        id__in=todas_despesas.values_list('socio', flat=True).distinct()
    ).order_by('pessoa__name')
    
    print(f"👥 Sócios com despesas: {socios_com_despesas.count()}")
    print()
    
    total_integradas = 0
    total_nao_integradas = 0
    
    for socio in socios_com_despesas:
        socio_nome = getattr(getattr(socio, 'pessoa', None), 'name', str(socio))
        despesas_socio = todas_despesas.filter(socio=socio)
        
        print(f"👤 {socio_nome}")
        print(f"   📋 Despesas no sistema: {despesas_socio.count()}")
        
        integradas = 0
        nao_integradas = 0
        
        for despesa in despesas_socio:
            # Verificar se existe no extrato
            existe_no_extrato = MovimentacaoContaCorrente.objects.filter(
                socio=despesa.socio,
                data_movimentacao=despesa.data,
                valor=-abs(despesa.valor),  # Negativo para débito
                historico_complementar__icontains=f"Despesa ID: {despesa.id}"
            ).exists()
            
            if existe_no_extrato:
                integradas += 1
            else:
                nao_integradas += 1
                print(f"   ⚠ Despesa ID {despesa.id} ({despesa.data}, R$ {despesa.valor}) NÃO integrada")
        
        print(f"   ✅ Integradas ao extrato: {integradas}")
        if nao_integradas > 0:
            print(f"   ❌ Não integradas: {nao_integradas}")
        print()
        
        total_integradas += integradas
        total_nao_integradas += nao_integradas
    
    # Resumo geral
    print("-" * 80)
    print("RESUMO GERAL:")
    print(f"✅ Total de despesas integradas: {total_integradas}")
    print(f"❌ Total de despesas não integradas: {total_nao_integradas}")
    print(f"📊 Taxa de integração: {(total_integradas/total_despesas*100):.1f}%")
    
    # Verificar movimentações órfãs (que não correspondem a despesas)
    movimentacoes_despesa = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Despesa ID:"
    )
    
    print(f"🔍 Movimentações de despesas no extrato: {movimentacoes_despesa.count()}")
    
    if movimentacoes_despesa.count() != total_integradas:
        print("⚠ ATENÇÃO: Discrepância entre contadores!")
    
    print("=" * 80)

if __name__ == "__main__":
    verificar_integracao_despesas()
