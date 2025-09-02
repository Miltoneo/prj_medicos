#!/usr/bin/env python3
"""
Teste rápido para validar signals de despesas rateadas.
"""

import os
import sys
import django
from datetime import date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.base import Socio, Empresa
from medicos.models.despesas import DespesaRateada, ItemDespesa, GrupoDespesa, ItemDespesaRateioMensal
from medicos.models.conta_corrente import MovimentacaoContaCorrente

def main():
    empresa_id = 5
    print("🧪 TESTE RÁPIDO - DESPESAS RATEADAS")
    print("="*50)
    
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        print(f"✅ Empresa: {empresa}")
        
        # Buscar sócios ativos
        socios = list(Socio.objects.filter(empresa=empresa, ativo=True)[:2])
        if len(socios) < 2:
            print("❌ Erro: Precisamos de pelo menos 2 sócios ativos")
            return
        
        print(f"✅ Sócios: {[str(s) for s in socios]}")
        
        # Buscar item com rateio
        item = ItemDespesa.objects.filter(
            grupo_despesa__empresa=empresa,
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
        ).first()
        
        if not item:
            print("❌ Erro: Nenhum item de despesa com rateio encontrado")
            return
        
        print(f"✅ Item para teste: {item}")
        
        # Contar lançamentos antes
        count_antes = MovimentacaoContaCorrente.objects.count()
        print(f"📊 Lançamentos antes: {count_antes}")
        
        with transaction.atomic():
            # Configurar rateios
            data_ref = date.today().replace(day=1)
            
            rateio1 = ItemDespesaRateioMensal.objects.create(
                item_despesa=item,
                socio=socios[0],
                data_referencia=data_ref,
                percentual_rateio=60
            )
            print(f"✅ Rateio 1 criado: {socios[0]} - 60%")
            
            rateio2 = ItemDespesaRateioMensal.objects.create(
                item_despesa=item,
                socio=socios[1],
                data_referencia=data_ref,
                percentual_rateio=40
            )
            print(f"✅ Rateio 2 criado: {socios[1]} - 40%")
            
            # Criar despesa rateada
            print("\n🔄 Criando despesa rateada...")
            despesa = DespesaRateada.objects.create(
                item_despesa=item,
                data=date.today(),
                valor=Decimal('1000.00')
            )
            print(f"✅ Despesa rateada criada: ID {despesa.id}")
            
            # Verificar lançamentos
            count_depois = MovimentacaoContaCorrente.objects.count()
            print(f"📊 Lançamentos depois: {count_depois}")
            print(f"📊 Novos lançamentos: {count_depois - count_antes}")
            
            # Buscar lançamentos específicos
            lancamentos = MovimentacaoContaCorrente.objects.filter(
                historico_complementar__contains=f'Despesa Rateada ID: {despesa.id}'
            )
            
            print(f"\n📋 Lançamentos encontrados: {lancamentos.count()}")
            for lancamento in lancamentos:
                print(f"   → {lancamento.socio}: R$ {lancamento.valor} em {lancamento.data_movimentacao}")
                print(f"     Histórico: {lancamento.historico_complementar}")
            
            # Rollback para não afetar dados
            transaction.set_rollback(True)
            print("\n🔄 Rollback executado - dados não foram salvos")
        
        print("\n🎉 TESTE CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
