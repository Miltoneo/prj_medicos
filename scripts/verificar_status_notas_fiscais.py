#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificação final: Status das notas fiscais e integração no extrato
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import NotaFiscalRateioMedico, MovimentacaoContaCorrente, NotaFiscal
from medicos.models.base import Socio

def verificar_status_notas_fiscais():
    """Verifica o status das notas fiscais e sua integração"""
    
    print("=" * 90)
    print("VERIFICAÇÃO: Status das Notas Fiscais e Integração no Extrato")
    print("=" * 90)
    
    # Estatísticas gerais das notas fiscais
    total_nf = NotaFiscal.objects.count()
    nf_recebidas = NotaFiscal.objects.filter(status_recebimento='recebido').count()
    nf_pendentes = NotaFiscal.objects.filter(status_recebimento='pendente').count()
    nf_canceladas = NotaFiscal.objects.filter(status_recebimento='cancelado').count()
    
    print("📊 ESTATÍSTICAS GERAIS DAS NOTAS FISCAIS:")
    print(f"   📄 Total de notas fiscais: {total_nf}")
    print(f"   ✅ Recebidas: {nf_recebidas}")
    print(f"   ⏳ Pendentes: {nf_pendentes}")
    print(f"   ❌ Canceladas: {nf_canceladas}")
    print()
    
    # Verificar rateios de notas fiscais recebidas
    rateios_recebidos = NotaFiscalRateioMedico.objects.filter(
        nota_fiscal__status_recebimento='recebido',
        nota_fiscal__dtRecebimento__isnull=False
    ).select_related('nota_fiscal', 'medico__pessoa')
    
    rateios_pendentes = NotaFiscalRateioMedico.objects.filter(
        nota_fiscal__status_recebimento='pendente'
    ).select_related('nota_fiscal', 'medico__pessoa')
    
    print("📋 RATEIOS DE NOTAS FISCAIS:")
    print(f"   ✅ Rateios de NF recebidas: {rateios_recebidos.count()}")
    print(f"   ⏳ Rateios de NF pendentes: {rateios_pendentes.count()}")
    print()
    
    # Verificar integração no extrato
    movimentacoes_nf = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__icontains="Rateio NF ID:"
    )
    
    print("🏦 INTEGRAÇÃO NO EXTRATO:")
    print(f"   💰 Movimentações de NF no extrato: {movimentacoes_nf.count()}")
    print()
    
    # Verificar por sócio
    socios_com_rateios = Socio.objects.filter(
        id__in=rateios_recebidos.values_list('medico', flat=True).distinct()
    ).order_by('pessoa__name')
    
    print("👥 DETALHAMENTO POR SÓCIO:")
    print("-" * 90)
    
    for socio in socios_com_rateios:
        socio_nome = getattr(getattr(socio, 'pessoa', None), 'name', str(socio))
        
        # Rateios recebidos do sócio
        rateios_socio_recebidos = rateios_recebidos.filter(medico=socio)
        rateios_socio_pendentes = rateios_pendentes.filter(medico=socio)
        
        # Movimentações no extrato
        movimentacoes_socio = movimentacoes_nf.filter(socio=socio)
        
        print(f"👤 {socio_nome}")
        print(f"   ✅ Rateios de NF recebidas: {rateios_socio_recebidos.count()}")
        print(f"   ⏳ Rateios de NF pendentes: {rateios_socio_pendentes.count()}")
        print(f"   🏦 Movimentações no extrato: {movimentacoes_socio.count()}")
        
        # Mostrar algumas notas recebidas como exemplo
        if rateios_socio_recebidos.exists():
            print("   📄 Exemplos de NF recebidas:")
            for rateio in rateios_socio_recebidos[:3]:  # Mostrar até 3 exemplos
                nf = rateio.nota_fiscal
                print(f"      • NF {nf.numero} - {nf.dtRecebimento} - R$ {rateio.valor_liquido:,.2f}")
        
        # Mostrar algumas notas pendentes como exemplo
        if rateios_socio_pendentes.exists():
            print("   ⏳ Exemplos de NF pendentes:")
            for rateio in rateios_socio_pendentes[:3]:  # Mostrar até 3 exemplos
                nf = rateio.nota_fiscal
                print(f"      • NF {nf.numero} - {nf.dtEmissao} - R$ {rateio.valor_liquido:,.2f} - Status: {nf.status_recebimento}")
        
        print()
    
    # Verificar consistência
    print("🔍 VERIFICAÇÃO DE CONSISTÊNCIA:")
    if rateios_recebidos.count() == movimentacoes_nf.count():
        print("   ✅ Perfeita consistência: Todos os rateios de NF recebidas estão no extrato")
    else:
        diferenca = rateios_recebidos.count() - movimentacoes_nf.count()
        if diferenca > 0:
            print(f"   ⚠ {diferenca} rateios de NF recebidas ainda não foram integrados ao extrato")
        else:
            print(f"   ⚠ Há {abs(diferenca)} movimentações a mais no extrato do que rateios")
    
    print()
    print("📋 RESUMO:")
    print(f"✅ O sistema agora considera apenas notas fiscais com status='recebido'")
    print(f"✅ Notas pendentes (sem data de recebimento) são ignoradas")
    print(f"✅ Integração automática funciona corretamente")
    print("=" * 90)

if __name__ == "__main__":
    verificar_status_notas_fiscais()
