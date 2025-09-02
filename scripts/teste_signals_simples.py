#!/usr/bin/env python3
"""
Script simples para testar se os signals estão funcionando.
"""

import os
import sys
import django
from datetime import date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def teste_simples():
    """Teste básico de funcionamento."""
    from medicos.models.base import Empresa, Socio
    from medicos.models.despesas import DespesaSocio, ItemDespesa, GrupoDespesa
    from medicos.models.conta_corrente import MovimentacaoContaCorrente
    
    print("🧪 TESTE SIMPLES DE SINCRONIZAÇÃO")
    print("="*50)
    
    # Verificar se empresa existe
    try:
        empresa = Empresa.objects.get(id=5)
        print(f"✅ Empresa encontrada: {empresa}")
    except Empresa.DoesNotExist:
        print("❌ Empresa ID 5 não encontrada")
        return False
    
    # Buscar dados necessários
    socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
    if not socio:
        print("❌ Nenhum sócio ativo encontrado")
        return False
    
    item_sem_rateio = ItemDespesa.objects.filter(
        grupo_despesa__empresa=empresa,
        grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
    ).first()
    
    if not item_sem_rateio:
        print("❌ Nenhum item de despesa sem rateio encontrado")
        return False
    
    print(f"✅ Sócio para teste: {socio}")
    print(f"✅ Item para teste: {item_sem_rateio}")
    
    # Contar lançamentos antes
    count_antes = MovimentacaoContaCorrente.objects.filter(socio=socio).count()
    print(f"📊 Lançamentos na conta corrente antes: {count_antes}")
    
    # Criar despesa de teste
    print("\n🔄 Criando despesa de sócio...")
    despesa = DespesaSocio.objects.create(
        socio=socio,
        item_despesa=item_sem_rateio,
        data=date.today(),
        valor=Decimal('100.00')
    )
    print(f"✅ Despesa criada: ID {despesa.id}")
    
    # Verificar se lançamento foi criado
    count_depois = MovimentacaoContaCorrente.objects.filter(socio=socio).count()
    print(f"📊 Lançamentos na conta corrente depois: {count_depois}")
    
    # Buscar lançamento específico
    lancamentos = MovimentacaoContaCorrente.objects.filter(
        socio=socio,
        historico_complementar__contains=f'Despesa Sócio ID: {despesa.id}'
    )
    
    if lancamentos.exists():
        lancamento = lancamentos.first()
        print(f"✅ Lançamento criado automaticamente!")
        print(f"   ID: {lancamento.id}")
        print(f"   Valor: R$ {lancamento.valor}")
        print(f"   Data: {lancamento.data_movimentacao}")
        print(f"   Histórico: {lancamento.historico_complementar}")
        
        # Limpar teste
        print("\n🧹 Limpando dados de teste...")
        despesa.delete()  # Deve remover o lançamento automaticamente
        
        # Verificar se foi removido
        lancamentos_apos = MovimentacaoContaCorrente.objects.filter(
            historico_complementar__contains=f'Despesa Sócio ID: {despesa.id}'
        )
        
        if not lancamentos_apos.exists():
            print("✅ Lançamento removido automaticamente!")
            return True
        else:
            print("❌ Lançamento não foi removido")
            return False
    else:
        print("❌ Nenhum lançamento foi criado automaticamente")
        # Limpar teste
        despesa.delete()
        return False

if __name__ == "__main__":
    try:
        sucesso = teste_simples()
        if sucesso:
            print("\n🎉 TESTE PASSOU! Signals funcionando corretamente.")
        else:
            print("\n⚠️ TESTE FALHOU! Verifique os signals.")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
