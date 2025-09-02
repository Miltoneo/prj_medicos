#!/usr/bin/env python
"""
Teste de integração entre DespesaSocio e MovimentacaoContaCorrente
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio, ItemDespesa
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.base import Socio

def test_integracao_despesa_socio():
    print("=== TESTE INTEGRAÇÃO DESPESA SÓCIO ===")
    
    # Buscar um sócio existente
    socio = Socio.objects.first()
    if not socio:
        print("❌ Nenhum sócio encontrado no banco")
        return
    
    print(f"Sócio encontrado: {socio}")
    
    # Buscar um item de despesa SEM rateio
    item = ItemDespesa.objects.filter(
        grupo_despesa__tipo_rateio=2  # SEM_RATEIO
    ).first()
    
    if not item:
        print("❌ Nenhum item de despesa sem rateio encontrado")
        return
    
    print(f"Item de despesa encontrado: {item}")
    
    # Verificar lançamentos antes
    lancamentos_antes = MovimentacaoContaCorrente.objects.filter(socio=socio).count()
    print(f"Lançamentos conta corrente ANTES: {lancamentos_antes}")
    
    try:
        # Criar despesa de sócio
        despesa = DespesaSocio.objects.create(
            socio=socio,
            item_despesa=item,
            data='2025-08-30',
            valor=Decimal('150.00')
        )
        
        print(f"✅ Despesa criada: ID {despesa.id}")
        
        # Verificar lançamentos depois
        lancamentos_depois = MovimentacaoContaCorrente.objects.filter(socio=socio).count()
        print(f"Lançamentos conta corrente DEPOIS: {lancamentos_depois}")
        
        # Buscar o lançamento específico
        lancamento_criado = MovimentacaoContaCorrente.objects.filter(
            socio=socio,
            historico_complementar__contains=f'Despesa Sócio ID: {despesa.id}'
        ).first()
        
        if lancamento_criado:
            print(f"✅ LANÇAMENTO CRIADO:")
            print(f"  - ID: {lancamento_criado.id}")
            print(f"  - Data: {lancamento_criado.data_movimentacao}")
            print(f"  - Valor: R$ {lancamento_criado.valor}")
            print(f"  - Histórico: {lancamento_criado.historico_complementar}")
            print(f"  - Descrição: {lancamento_criado.descricao_movimentacao}")
        else:
            print("❌ Lançamento não foi criado automaticamente")
        
        # Testar atualização
        print("\n=== TESTANDO ATUALIZAÇÃO ===")
        despesa.valor = Decimal('200.00')
        despesa.save()
        
        # Verificar se foi atualizado
        lancamento_atualizado = MovimentacaoContaCorrente.objects.filter(
            socio=socio,
            historico_complementar__contains=f'Despesa Sócio ID: {despesa.id}'
        ).first()
        
        if lancamento_atualizado:
            print(f"✅ LANÇAMENTO ATUALIZADO:")
            print(f"  - Valor atualizado: R$ {lancamento_atualizado.valor}")
        
        # Testar exclusão
        print("\n=== TESTANDO EXCLUSÃO ===")
        despesa.delete()
        
        # Verificar se foi removido
        lancamentos_final = MovimentacaoContaCorrente.objects.filter(socio=socio).count()
        print(f"Lançamentos conta corrente FINAL: {lancamentos_final}")
        
        if lancamentos_final == lancamentos_antes:
            print("✅ Lançamento removido corretamente")
        else:
            print("❌ Lançamento não foi removido")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integracao_despesa_socio()
