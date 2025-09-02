#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import django
import sys
from decimal import Decimal

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Socio, Empresa
from medicos.models.despesas import DespesaSocio, ItemDespesa, GrupoDespesa
from medicos.models.financeiro import MovimentacaoContaCorrente, DescricaoMovimentacaoFinanceira
from datetime import date

def testar_descricao_corrigida():
    """
    Testa se a descrição das despesas está sendo criada corretamente após a correção dos signals.
    """
    print("=== TESTE: DESCRIÇÃO CORRIGIDA SIGNALS ===")
    
    # Buscar dados de teste
    try:
        empresa = Empresa.objects.filter(ativa=True).first()
        if not empresa:
            print("❌ Nenhuma empresa ativa encontrada")
            return
            
        socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
        if not socio:
            print("❌ Nenhum sócio ativo encontrado")
            return
            
        item_despesa = ItemDespesa.objects.filter(
            grupo_despesa__empresa=empresa,
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
        ).first()
        
        if not item_despesa:
            print("❌ Nenhum item de despesa sem rateio encontrado")
            return
            
        print(f"✅ Dados de teste localizados:")
        print(f"   Empresa: {empresa.nome}")
        print(f"   Sócio: {socio.nome}")
        print(f"   Item Despesa: {item_despesa.descricao}")
        print()
        
        # Criar uma despesa de teste
        print("📝 Criando despesa de teste...")
        despesa_teste = DespesaSocio.objects.create(
            socio=socio,
            item_despesa=item_despesa,
            data=date.today(),
            valor=Decimal('100.00')
        )
        
        print(f"✅ Despesa criada: ID {despesa_teste.id}")
        print()
        
        # Verificar se o lançamento foi criado automaticamente
        print("🔍 Verificando lançamento automático na conta corrente...")
        lancamento = MovimentacaoContaCorrente.objects.filter(
            socio=socio,
            historico_complementar__contains=f'Despesa Sócio ID: {despesa_teste.id}'
        ).first()
        
        if not lancamento:
            print("❌ Lançamento não foi criado automaticamente")
            return
            
        print(f"✅ Lançamento criado automaticamente: ID {lancamento.id}")
        print(f"   Data: {lancamento.data_movimentacao}")
        print(f"   Valor: R$ {lancamento.valor}")
        print(f"   Descrição: {lancamento.descricao_movimentacao.descricao}")
        print(f"   Histórico: {lancamento.historico_complementar}")
        print()
        
        # Verificar se a descrição está correta
        descricao_esperada = f"Débito {item_despesa.descricao}"
        descricao_atual = lancamento.descricao_movimentacao.descricao
        
        print("🎯 VERIFICAÇÃO DA DESCRIÇÃO:")
        print(f"   Esperada: '{descricao_esperada}'")
        print(f"   Atual:    '{descricao_atual}'")
        
        if descricao_atual == descricao_esperada:
            print("✅ SUCESSO: Descrição está correta!")
        else:
            print("❌ ERRO: Descrição não confere!")
        print()
        
        # Verificar DescricaoMovimentacaoFinanceira criada
        print("📋 Verificando DescricaoMovimentacaoFinanceira...")
        descricoes = DescricaoMovimentacaoFinanceira.objects.filter(
            empresa=empresa,
            descricao__startswith="Débito "
        ).order_by('-id')[:5]
        
        print(f"   Últimas 5 descrições criadas:")
        for desc in descricoes:
            print(f"   - ID {desc.id}: '{desc.descricao}'")
        print()
        
        # Limpeza: remover dados de teste
        print("🧹 Limpando dados de teste...")
        despesa_teste.delete()  # Isso deve remover automaticamente o lançamento via signal
        print("✅ Dados de teste removidos")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_descricao_corrigida()
