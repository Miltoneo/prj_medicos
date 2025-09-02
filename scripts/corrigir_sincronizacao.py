#!/usr/bin/env python3
"""
Script para limpar lançamentos órfãos que ficaram após exclusões em lote.
Remove lançamentos que referenciam despesas que não existem mais.
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio, DespesaRateada
from medicos.models.conta_corrente import MovimentacaoContaCorrente

def limpar_lancamentos_orfaos():
    """Remove lançamentos órfãos de despesas que não existem mais."""
    print("🧹 LIMPANDO LANÇAMENTOS ÓRFÃOS")
    print("="*50)
    
    orfaos_removidos = 0
    
    # 1. Lançamentos de DespesaSocio órfãos
    print("\n🔍 Verificando lançamentos de Despesa Sócio...")
    lancamentos_socio = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__contains='Despesa Sócio ID:'
    )
    
    for lancamento in lancamentos_socio:
        try:
            # Extrair ID da despesa do histórico
            id_str = lancamento.historico_complementar.split('Despesa Sócio ID: ')[1].split(')')[0]
            despesa_id = int(id_str)
            
            # Verificar se a despesa ainda existe
            if not DespesaSocio.objects.filter(id=despesa_id).exists():
                print(f"   🗑️ Removendo lançamento órfão: ID {lancamento.id} → Despesa Sócio {despesa_id}")
                print(f"      Data: {lancamento.data_movimentacao}, Valor: R$ {lancamento.valor}")
                lancamento.delete()
                orfaos_removidos += 1
        except (ValueError, IndexError):
            print(f"   ⚠️ Lançamento com formato inválido: {lancamento.historico_complementar}")
    
    # 2. Lançamentos de DespesaRateada órfãos
    print("\n🔍 Verificando lançamentos de Despesa Rateada...")
    lancamentos_rateada = MovimentacaoContaCorrente.objects.filter(
        historico_complementar__contains='Despesa Rateada ID:'
    )
    
    for lancamento in lancamentos_rateada:
        try:
            # Extrair ID da despesa do histórico
            id_str = lancamento.historico_complementar.split('Despesa Rateada ID: ')[1].split(' ')[0]
            despesa_id = int(id_str)
            
            # Verificar se a despesa ainda existe
            if not DespesaRateada.objects.filter(id=despesa_id).exists():
                print(f"   🗑️ Removendo lançamento órfão: ID {lancamento.id} → Despesa Rateada {despesa_id}")
                print(f"      Data: {lancamento.data_movimentacao}, Valor: R$ {lancamento.valor}")
                lancamento.delete()
                orfaos_removidos += 1
        except (ValueError, IndexError):
            print(f"   ⚠️ Lançamento com formato inválido: {lancamento.historico_complementar}")
    
    print(f"\n✅ Limpeza concluída!")
    print(f"📊 Total de lançamentos órfãos removidos: {orfaos_removidos}")
    
    return orfaos_removidos


def recriar_lancamentos_faltantes():
    """Recria lançamentos para despesas que deveriam ter mas não têm."""
    print("\n🔧 RECRIANDO LANÇAMENTOS FALTANTES")
    print("="*50)
    
    criados = 0
    
    # 1. Verificar despesas de sócio sem lançamento
    print("\n🔍 Verificando despesas de sócio sem lançamento...")
    despesas_socio = DespesaSocio.objects.all()
    
    for despesa in despesas_socio:
        lancamentos = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Sócio ID: {despesa.id}'
        )
        
        if not lancamentos.exists():
            print(f"   ➕ Criando lançamento para Despesa Sócio {despesa.id}")
            print(f"      {despesa.data} | {despesa.socio} | {despesa.item_despesa.descricao} | R$ {despesa.valor}")
            
            # Disparar signal manualmente para recriar o lançamento
            from medicos.signals_financeiro import criar_ou_atualizar_debito_despesa_socio
            criar_ou_atualizar_debito_despesa_socio(DespesaSocio, despesa, created=False)
            criados += 1
    
    # 2. Verificar despesas rateadas sem lançamento
    print("\n🔍 Verificando despesas rateadas sem lançamento...")
    despesas_rateadas = DespesaRateada.objects.all()
    
    for despesa in despesas_rateadas:
        lancamentos = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Rateada ID: {despesa.id}'
        )
        
        if not lancamentos.exists():
            print(f"   ➕ Criando lançamentos para Despesa Rateada {despesa.id}")
            print(f"      {despesa.data} | {despesa.item_despesa.descricao} | R$ {despesa.valor}")
            
            # Disparar signal manualmente para recriar os lançamentos
            from medicos.signals_financeiro import criar_ou_atualizar_debitos_despesa_rateada
            criar_ou_atualizar_debitos_despesa_rateada(DespesaRateada, despesa, created=False)
            criados += 1
    
    print(f"\n✅ Recriação concluída!")
    print(f"📊 Total de lançamentos criados: {criados}")
    
    return criados


def main():
    """Função principal."""
    print("🔧 CORREÇÃO DE SINCRONIZAÇÃO DESPESAS ↔ CONTA CORRENTE")
    print(f"📅 Data/Hora: {datetime.now()}")
    print("="*80)
    
    try:
        # 1. Limpar órfãos
        orfaos_removidos = limpar_lancamentos_orfaos()
        
        # 2. Recriar faltantes
        criados = recriar_lancamentos_faltantes()
        
        # 3. Resultado final
        print("\n" + "="*80)
        print("RESULTADO FINAL")
        print("="*80)
        print(f"🗑️ Lançamentos órfãos removidos: {orfaos_removidos}")
        print(f"➕ Lançamentos criados: {criados}")
        
        if orfaos_removidos > 0 or criados > 0:
            print("\n✅ CORREÇÃO APLICADA COM SUCESSO!")
            print("   A sincronização agora deve estar funcionando corretamente.")
        else:
            print("\n✅ NENHUMA CORREÇÃO NECESSÁRIA!")
            print("   A sincronização já está funcionando corretamente.")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
