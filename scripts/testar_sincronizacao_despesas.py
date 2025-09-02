#!/usr/bin/env python3
"""
Script para testar a sincronização automática entre despesas e lançamentos bancários.

Testa os seguintes cenários:
1. Criação de DespesaSocio → deve criar lançamento automático
2. Modificação de DespesaSocio → deve atualizar lançamento 
3. Exclusão de DespesaSocio → deve remover lançamento
4. Criação de DespesaRateada → deve criar lançamentos proporcionais
5. Modificação de ItemDespesaRateioMensal → deve recalcular lançamentos
6. Exclusão de DespesaRateada → deve remover todos os lançamentos

Usage:
    python testar_sincronizacao_despesas.py --empresa_id 5
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.base import Socio, Empresa
from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesa, GrupoDespesa, ItemDespesaRateioMensal
from medicos.models.conta_corrente import MovimentacaoContaCorrente


def buscar_lancamentos_relacionados(historico_busca):
    """Busca lançamentos na conta corrente por histórico."""
    return MovimentacaoContaCorrente.objects.filter(
        historico_complementar__contains=historico_busca
    )


def imprimir_resultado_teste(titulo, sucesso, detalhes=""):
    """Imprime resultado de teste formatado."""
    status = "✅ PASSOU" if sucesso else "❌ FALHOU"
    print(f"\n{status} - {titulo}")
    if detalhes:
        print(f"    {detalhes}")


def testar_despesa_socio(empresa_id):
    """Testa sincronização de DespesaSocio."""
    print("\n" + "="*80)
    print("TESTANDO SINCRONIZAÇÃO DE DESPESA SÓCIO")
    print("="*80)
    
    # Buscar dados de teste
    empresa = Empresa.objects.get(id=empresa_id)
    socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
    item_despesa = ItemDespesa.objects.filter(
        grupo_despesa__empresa=empresa,
        grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
    ).first()
    
    if not socio or not item_despesa:
        print("❌ Erro: Não foi possível encontrar sócio ativo ou item de despesa sem rateio")
        return False
    
    print(f"📊 Dados de teste:")
    print(f"   Empresa: {empresa}")
    print(f"   Sócio: {socio}")
    print(f"   Item: {item_despesa}")
    
    # TESTE 1: Criação de despesa deve criar lançamento
    with transaction.atomic():
        despesa = DespesaSocio.objects.create(
            socio=socio,
            item_despesa=item_despesa,
            data=date.today(),
            valor=Decimal('150.00')
        )
        
        # Verificar se lançamento foi criado
        lancamentos = buscar_lancamentos_relacionados(f'Despesa Sócio ID: {despesa.id}')
        sucesso_criacao = lancamentos.count() == 1
        
        if sucesso_criacao:
            lancamento = lancamentos.first()
            detalhes = f"Lançamento ID {lancamento.id}, Valor: R$ {lancamento.valor}, Data: {lancamento.data_movimentacao}"
        else:
            detalhes = f"Esperado 1 lançamento, encontrado {lancamentos.count()}"
        
        imprimir_resultado_teste("Criação de DespesaSocio", sucesso_criacao, detalhes)
        
        # TESTE 2: Modificação deve atualizar lançamento
        despesa.valor = Decimal('200.00')
        despesa.save()
        
        lancamentos = buscar_lancamentos_relacionados(f'Despesa Sócio ID: {despesa.id}')
        if lancamentos.exists():
            lancamento_atualizado = lancamentos.first()
            valor_esperado = -abs(despesa.valor)  # Valor negativo para débito
            sucesso_atualizacao = lancamento_atualizado.valor == valor_esperado
            detalhes = f"Valor atualizado: R$ {lancamento_atualizado.valor} (esperado: R$ {valor_esperado})"
        else:
            sucesso_atualizacao = False
            detalhes = "Lançamento não encontrado após atualização"
        
        imprimir_resultado_teste("Atualização de DespesaSocio", sucesso_atualizacao, detalhes)
        
        # TESTE 3: Exclusão deve remover lançamento
        despesa_id = despesa.id
        despesa.delete()
        
        lancamentos_apos_exclusao = buscar_lancamentos_relacionados(f'Despesa Sócio ID: {despesa_id}')
        sucesso_exclusao = lancamentos_apos_exclusao.count() == 0
        detalhes = f"Lançamentos após exclusão: {lancamentos_apos_exclusao.count()}"
        
        imprimir_resultado_teste("Exclusão de DespesaSocio", sucesso_exclusao, detalhes)
        
        # Rollback para não afetar dados reais
        transaction.set_rollback(True)
    
    return sucesso_criacao and sucesso_atualizacao and sucesso_exclusao


def testar_despesa_rateada(empresa_id):
    """Testa sincronização de DespesaRateada."""
    print("\n" + "="*80)
    print("TESTANDO SINCRONIZAÇÃO DE DESPESA RATEADA")
    print("="*80)
    
    # Buscar dados de teste
    empresa = Empresa.objects.get(id=empresa_id)
    socios = list(Socio.objects.filter(empresa=empresa, ativo=True)[:2])  # Pegar 2 sócios
    item_despesa = ItemDespesa.objects.filter(
        grupo_despesa__empresa=empresa,
        grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
    ).first()
    
    if len(socios) < 2 or not item_despesa:
        print("❌ Erro: Precisamos de pelo menos 2 sócios ativos e 1 item de despesa com rateio")
        return False
    
    print(f"📊 Dados de teste:")
    print(f"   Empresa: {empresa}")
    print(f"   Sócios: {[str(s) for s in socios]}")
    print(f"   Item: {item_despesa}")
    
    # TESTE 1: Configurar rateios e criar despesa
    with transaction.atomic():
        data_ref = date.today().replace(day=1)
        
        # Criar configurações de rateio (60% e 40%)
        rateio1 = ItemDespesaRateioMensal.objects.create(
            item_despesa=item_despesa,
            socio=socios[0],
            data_referencia=data_ref,
            percentual_rateio=60
        )
        rateio2 = ItemDespesaRateioMensal.objects.create(
            item_despesa=item_despesa,
            socio=socios[1],
            data_referencia=data_ref,
            percentual_rateio=40
        )
        
        # Criar despesa rateada
        despesa = DespesaRateada.objects.create(
            item_despesa=item_despesa,
            data=date.today(),
            valor=Decimal('1000.00')
        )
        
        # Verificar se 2 lançamentos foram criados
        lancamentos = buscar_lancamentos_relacionados(f'Despesa Rateada ID: {despesa.id}')
        sucesso_criacao = lancamentos.count() == 2
        
        if sucesso_criacao:
            # Verificar valores proporcionais
            valores_esperados = {socios[0]: -600.00, socios[1]: -400.00}  # Valores negativos para débito
            valores_reais = {l.socio: float(l.valor) for l in lancamentos}
            valores_corretos = valores_esperados == valores_reais
            
            detalhes = f"Lançamentos criados: {lancamentos.count()}, Valores: {valores_reais}"
        else:
            valores_corretos = False
            detalhes = f"Esperado 2 lançamentos, encontrado {lancamentos.count()}"
        
        imprimir_resultado_teste("Criação de DespesaRateada", sucesso_criacao and valores_corretos, detalhes)
        
        # TESTE 2: Modificar percentual de rateio
        rateio1.percentual_rateio = 70
        rateio1.save()
        rateio2.percentual_rateio = 30
        rateio2.save()
        
        # Verificar se lançamentos foram recalculados
        lancamentos_atualizados = buscar_lancamentos_relacionados(f'Despesa Rateada ID: {despesa.id}')
        valores_esperados_novos = {socios[0]: -700.00, socios[1]: -300.00}
        valores_reais_novos = {l.socio: float(l.valor) for l in lancamentos_atualizados}
        sucesso_recalculo = valores_esperados_novos == valores_reais_novos
        
        detalhes = f"Valores recalculados: {valores_reais_novos} (esperado: {valores_esperados_novos})"
        imprimir_resultado_teste("Recálculo por mudança de rateio", sucesso_recalculo, detalhes)
        
        # TESTE 3: Excluir despesa rateada
        despesa_id = despesa.id
        despesa.delete()
        
        lancamentos_apos_exclusao = buscar_lancamentos_relacionados(f'Despesa Rateada ID: {despesa_id}')
        sucesso_exclusao = lancamentos_apos_exclusao.count() == 0
        detalhes = f"Lançamentos após exclusão: {lancamentos_apos_exclusao.count()}"
        
        imprimir_resultado_teste("Exclusão de DespesaRateada", sucesso_exclusao, detalhes)
        
        # Rollback para não afetar dados reais
        transaction.set_rollback(True)
    
    return sucesso_criacao and valores_corretos and sucesso_recalculo and sucesso_exclusao


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Testar sincronização de despesas com conta corrente')
    parser.add_argument('--empresa_id', type=int, required=True, help='ID da empresa para teste')
    
    args = parser.parse_args()
    
    print("🧪 INICIANDO TESTES DE SINCRONIZAÇÃO DESPESAS ↔ CONTA CORRENTE")
    print(f"📅 Data/Hora: {datetime.now()}")
    print(f"🏢 Empresa ID: {args.empresa_id}")
    
    try:
        # Validar empresa
        empresa = Empresa.objects.get(id=args.empresa_id)
        print(f"✅ Empresa encontrada: {empresa}")
        
        # Executar testes
        resultado_socio = testar_despesa_socio(args.empresa_id)
        resultado_rateada = testar_despesa_rateada(args.empresa_id)
        
        # Resultado final
        print("\n" + "="*80)
        print("RESULTADO FINAL DOS TESTES")
        print("="*80)
        
        status_socio = "✅ PASSOU" if resultado_socio else "❌ FALHOU"
        status_rateada = "✅ PASSOU" if resultado_rateada else "❌ FALHOU"
        
        print(f"Despesas de Sócio:   {status_socio}")
        print(f"Despesas Rateadas:   {status_rateada}")
        
        if resultado_socio and resultado_rateada:
            print("\n🎉 TODOS OS TESTES PASSARAM! Sincronização funcionando corretamente.")
            return True
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM! Verifique os signals em medicos/signals_financeiro.py")
            return False
            
    except Empresa.DoesNotExist:
        print(f"❌ Erro: Empresa com ID {args.empresa_id} não encontrada")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
