#!/usr/bin/env python3
"""
Script de teste para validar o lançamento automático de impostos integrado ao builder.
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from medicos.models import (
    Conta, Empresa, Socio, MovimentacaoContaCorrente, 
    MeioPagamento, DescricaoMovimentacaoFinanceira
)
from medicos.relatorios.builders import montar_relatorio_mensal_socio

def test_lancamento_automatico():
    """
    Testa o fluxo completo de lançamento automático de impostos.
    """
    print("=" * 80)
    print("TESTE: Lançamento Automático de Impostos Integrado ao Builder")
    print("=" * 80)
    
    try:
        # Buscar dados de teste
        conta = Conta.objects.filter(ativo=True).first()
        if not conta:
            print("❌ Erro: Nenhuma conta ativa encontrada")
            return
            
        empresa = Empresa.objects.filter(conta=conta, ativo=True).first()
        if not empresa:
            print("❌ Erro: Nenhuma empresa ativa encontrada")
            return
            
        socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
        if not socio:
            print("❌ Erro: Nenhum sócio ativo encontrado")
            return
            
        print(f"📋 Dados do teste:")
        print(f"   Conta: {conta.nome}")
        print(f"   Empresa: {empresa.nome}")
        print(f"   Sócio: {socio.pessoa.name}")
        print()
        
        # Contar movimentações antes
        count_antes = MovimentacaoContaCorrente.objects.filter(
            empresa=empresa,
            descricao__nome__icontains='PIS'
        ).count()
        
        print(f"� Movimentações PIS antes: {count_antes}")
        print()
        
        # Executar builder com lançamento automático
        print("🔄 Executando builder com lançamento automático...")
        resultado = montar_relatorio_mensal_socio(
            request=None,  # Simular request None para teste
            empresa=empresa,
            socio_id=socio.id,
            competencia=date.today().replace(day=1),
            auto_lancar_impostos=True,
            atualizar_lancamentos_existentes=True
        )
        
        print(f"✅ Builder executado com sucesso")
        
        # Verificar resultado do lançamento automático
        if 'resultado_lancamento_automatico' in resultado:
            resultado_lancamento = resultado['resultado_lancamento_automatico']
            
            if resultado_lancamento.get('success'):
                print(f"✅ Lançamento automático executado com sucesso!")
                print(f"� Resumo:")
                
                for imposto, dados in resultado_lancamento.get('impostos_lancados', {}).items():
                    status = "✅ Criado" if dados.get('criado') else "� Atualizado"
                    valor = dados.get('valor', 0)
                    print(f"   {imposto}: {status} - R$ {valor:,.2f}")
                    
            else:
                error = resultado_lancamento.get('error', 'Erro desconhecido')
                print(f"❌ Erro no lançamento automático: {error}")
        else:
            print("⚠️  Nenhum resultado de lançamento automático encontrado")
        
        # Contar movimentações depois
        count_depois = MovimentacaoContaCorrente.objects.filter(
            empresa=empresa,
            descricao__nome__icontains='PIS'
        ).count()
        
        print()
        print(f"📊 Movimentações PIS depois: {count_depois}")
        print(f"📈 Diferença: +{count_depois - count_antes}")
        
        # Verificar algumas movimentações criadas
        if count_depois > count_antes:
            print("\n🔍 Últimas movimentações PIS criadas:")
            movimentacoes = MovimentacaoContaCorrente.objects.filter(
                empresa=empresa,
                descricao__nome__icontains='PIS'
            ).order_by('-created_at')[:3]
            
            for mov in movimentacoes:
                print(f"   📌 {mov.descricao.nome}: R$ {mov.valor:,.2f} ({mov.created_at})")
        
        print("\n" + "=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_lancamento_automatico()
