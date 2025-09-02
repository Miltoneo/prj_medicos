#!/usr/bin/env python3
"""
Script para diagnosticar o problema de sincronização na tela "Despesas Apropriadas dos Sócios".
Replica exatamente o fluxo da interface para identificar onde está o problema.
"""

import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.base import Socio, Empresa
from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesa, GrupoDespesa, ItemDespesaRateioMensal
from medicos.models.conta_corrente import MovimentacaoContaCorrente

def verificar_estado_atual(empresa_id, socio_id):
    """Verifica o estado atual das despesas e lançamentos."""
    print("\n" + "="*80)
    print("VERIFICANDO ESTADO ATUAL")
    print("="*80)
    
    # Despesas de sócio do Antonio Conselheiro
    despesas_socio = DespesaSocio.objects.filter(
        socio_id=socio_id,
        data__month=8,
        data__year=2025
    ).order_by('data')
    
    print(f"📊 Despesas de Sócio (Agosto 2025):")
    for despesa in despesas_socio:
        print(f"   → {despesa.data} | {despesa.item_despesa.descricao} | R$ {despesa.valor}")
    
    # Despesas rateadas relevantes
    despesas_rateadas = DespesaRateada.objects.filter(
        item_despesa__grupo_despesa__empresa_id=empresa_id,
        data__month=8,
        data__year=2025
    ).order_by('data')
    
    print(f"\n📊 Despesas Rateadas (Agosto 2025):")
    for despesa in despesas_rateadas:
        # Verificar se o sócio tem rateio para esta despesa
        rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
            despesa.item_despesa, 
            Socio.objects.get(id=socio_id), 
            despesa.data
        )
        if rateio:
            valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
            print(f"   → {despesa.data} | {despesa.item_despesa.descricao} | R$ {despesa.valor} ({rateio.percentual_rateio}% = R$ {valor_apropriado})")
    
    # Lançamentos bancários do sócio
    lancamentos = MovimentacaoContaCorrente.objects.filter(
        socio_id=socio_id,
        data_movimentacao__month=8,
        data_movimentacao__year=2025
    ).order_by('data_movimentacao')
    
    print(f"\n📊 Lançamentos Bancários (Agosto 2025):")
    for lancamento in lancamentos:
        print(f"   → {lancamento.data_movimentacao} | {lancamento.historico_complementar} | R$ {lancamento.valor}")
    
    return len(despesas_socio) + len([d for d in despesas_rateadas if ItemDespesaRateioMensal.obter_rateio_para_despesa(d.item_despesa, Socio.objects.get(id=socio_id), d.data)]), len(lancamentos)


def simular_exclusao_despesa_socio(despesa_id):
    """Simula a exclusão de uma DespesaSocio pela interface."""
    print(f"\n🗑️ SIMULANDO EXCLUSÃO DE DESPESA SÓCIO ID {despesa_id}")
    
    try:
        despesa = DespesaSocio.objects.get(id=despesa_id)
        print(f"   Despesa encontrada: {despesa.data} | {despesa.item_despesa.descricao} | R$ {despesa.valor}")
        
        # Verificar lançamentos antes
        lancamentos_antes = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Sócio ID: {despesa_id}'
        )
        print(f"   Lançamentos relacionados antes: {lancamentos_antes.count()}")
        
        # Excluir a despesa (isso deve disparar o signal)
        despesa.delete()
        print(f"   ✅ Despesa excluída")
        
        # Verificar lançamentos depois
        lancamentos_depois = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Sócio ID: {despesa_id}'
        )
        print(f"   Lançamentos relacionados depois: {lancamentos_depois.count()}")
        
        if lancamentos_depois.count() == 0:
            print(f"   ✅ Signal funcionou - lançamentos removidos automaticamente")
            return True
        else:
            print(f"   ❌ Signal falhou - lançamentos ainda existem")
            return False
            
    except DespesaSocio.DoesNotExist:
        print(f"   ❌ Despesa ID {despesa_id} não encontrada")
        return False


def simular_exclusao_despesa_rateada(despesa_id):
    """Simula a exclusão de uma DespesaRateada pela interface."""
    print(f"\n🗑️ SIMULANDO EXCLUSÃO DE DESPESA RATEADA ID {despesa_id}")
    
    try:
        despesa = DespesaRateada.objects.get(id=despesa_id)
        print(f"   Despesa encontrada: {despesa.data} | {despesa.item_despesa.descricao} | R$ {despesa.valor}")
        
        # Verificar lançamentos antes
        lancamentos_antes = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Rateada ID: {despesa_id}'
        )
        print(f"   Lançamentos relacionados antes: {lancamentos_antes.count()}")
        for l in lancamentos_antes:
            print(f"     → {l.socio}: R$ {l.valor}")
        
        # Excluir a despesa (isso deve disparar o signal)
        despesa.delete()
        print(f"   ✅ Despesa excluída")
        
        # Verificar lançamentos depois
        lancamentos_depois = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Rateada ID: {despesa_id}'
        )
        print(f"   Lançamentos relacionados depois: {lancamentos_depois.count()}")
        
        if lancamentos_depois.count() == 0:
            print(f"   ✅ Signal funcionou - lançamentos removidos automaticamente")
            return True
        else:
            print(f"   ❌ Signal falhou - lançamentos ainda existem")
            for l in lancamentos_depois:
                print(f"     → {l.socio}: R$ {l.valor}")
            return False
            
    except DespesaRateada.DoesNotExist:
        print(f"   ❌ Despesa ID {despesa_id} não encontrada")
        return False


def buscar_despesas_problematicas(empresa_id, socio_id):
    """Busca despesas que podem estar causando problemas."""
    print("\n" + "="*80)
    print("BUSCANDO DESPESAS PROBLEMÁTICAS")
    print("="*80)
    
    # Buscar lançamentos órfãos (sem despesa correspondente)
    lancamentos = MovimentacaoContaCorrente.objects.filter(
        socio_id=socio_id,
        historico_complementar__contains='Despesa'
    )
    
    print(f"📊 Total de lançamentos com 'Despesa': {lancamentos.count()}")
    
    orfaos_socio = []
    orfaos_rateada = []
    
    for lancamento in lancamentos:
        if 'Despesa Sócio ID:' in lancamento.historico_complementar:
            # Extrair ID da despesa
            try:
                id_str = lancamento.historico_complementar.split('Despesa Sócio ID: ')[1].split(')')[0]
                despesa_id = int(id_str)
                
                # Verificar se a despesa ainda existe
                if not DespesaSocio.objects.filter(id=despesa_id).exists():
                    orfaos_socio.append((lancamento, despesa_id))
            except:
                pass
                
        elif 'Despesa Rateada ID:' in lancamento.historico_complementar:
            # Extrair ID da despesa
            try:
                id_str = lancamento.historico_complementar.split('Despesa Rateada ID: ')[1].split(' ')[0]
                despesa_id = int(id_str)
                
                # Verificar se a despesa ainda existe
                if not DespesaRateada.objects.filter(id=despesa_id).exists():
                    orfaos_rateada.append((lancamento, despesa_id))
            except:
                pass
    
    print(f"\n❌ Lançamentos órfãos de DespesaSocio: {len(orfaos_socio)}")
    for lancamento, despesa_id in orfaos_socio:
        print(f"   → Lançamento ID {lancamento.id} referencia Despesa Sócio ID {despesa_id} (não existe)")
        print(f"     Data: {lancamento.data_movimentacao}, Valor: R$ {lancamento.valor}")
    
    print(f"\n❌ Lançamentos órfãos de DespesaRateada: {len(orfaos_rateada)}")
    for lancamento, despesa_id in orfaos_rateada:
        print(f"   → Lançamento ID {lancamento.id} referencia Despesa Rateada ID {despesa_id} (não existe)")
        print(f"     Data: {lancamento.data_movimentacao}, Valor: R$ {lancamento.valor}")
    
    return orfaos_socio, orfaos_rateada


def main():
    """Função principal."""
    empresa_id = 5
    socio_id = 10  # Antonio Conselheiro
    
    print("🔍 DIAGNÓSTICO DE SINCRONIZAÇÃO - DESPESAS APROPRIADAS")
    print(f"📅 Data/Hora: {datetime.now()}")
    print(f"🏢 Empresa ID: {empresa_id}")
    print(f"👤 Sócio ID: {socio_id} (Antonio Conselheiro)")
    
    try:
        # Verificar estado atual
        count_despesas, count_lancamentos = verificar_estado_atual(empresa_id, socio_id)
        
        # Buscar problemas
        orfaos_socio, orfaos_rateada = buscar_despesas_problematicas(empresa_id, socio_id)
        
        print("\n" + "="*80)
        print("RESUMO DO DIAGNÓSTICO")
        print("="*80)
        print(f"📊 Total de despesas apropriadas: {count_despesas}")
        print(f"📊 Total de lançamentos bancários: {count_lancamentos}")
        print(f"❌ Lançamentos órfãos de DespesaSocio: {len(orfaos_socio)}")
        print(f"❌ Lançamentos órfãos de DespesaRateada: {len(orfaos_rateada)}")
        
        if len(orfaos_socio) > 0 or len(orfaos_rateada) > 0:
            print("\n⚠️ PROBLEMA IDENTIFICADO:")
            print("   Existem lançamentos bancários referenciam despesas que não existem mais.")
            print("   Isso indica que os signals não foram disparados corretamente durante exclusões anteriores.")
            print("\n💡 POSSÍVEIS CAUSAS:")
            print("   1. Exclusões foram feitas diretamente no banco (sem Django ORM)")
            print("   2. Signals foram desabilitados temporariamente")
            print("   3. Erro durante a transação de exclusão")
            print("   4. Exclusões em lote (.delete() em QuerySet) que não disparam signals por item")
        else:
            print("\n✅ ESTADO CONSISTENTE:")
            print("   Todos os lançamentos bancários têm despesas correspondentes.")
            print("   Os signals parecem estar funcionando corretamente.")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
