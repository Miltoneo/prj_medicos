#!/usr/bin/env python3
"""
Script para verificar os lançamentos de despesas apropriadas criados na conta corrente.
"""

import os
import django
from datetime import datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.base import Socio, Empresa

def verificar_lancamentos_despesas_apropriadas(empresa_id=5, socio_id=10, competencia="2025-08"):
    """Verifica os lançamentos de despesas apropriadas criados"""
    print("=" * 80)
    print("VERIFICAÇÃO DOS LANÇAMENTOS DE DESPESAS APROPRIADAS")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🏢 Empresa ID: {empresa_id}")
    print(f"👤 Sócio ID: {socio_id}")
    print(f"📆 Competência: {competencia}")
    print()
    
    try:
        # Obter empresa e sócio
        empresa = Empresa.objects.get(id=empresa_id)
        socio = Socio.objects.get(id=socio_id, empresa=empresa)
        socio_nome = getattr(getattr(socio, 'pessoa', None), 'name', str(socio))
        
        print(f"🏢 Empresa: {empresa.nome_fantasia or f'ID {empresa.id}'}")
        print(f"👤 Sócio: {socio_nome}")
        print()
        
        # Buscar lançamentos que contenham identificadores de despesas apropriadas
        lancamentos = MovimentacaoContaCorrente.objects.filter(
            socio=socio,
            historico_complementar__icontains="Débito"
        ).order_by('-data_movimentacao', '-created_at')
        
        # Filtrar por competência se especificada
        if competencia:
            try:
                ano, mes = competencia.split('-')
                lancamentos = lancamentos.filter(
                    data_movimentacao__year=ano,
                    data_movimentacao__month=mes
                )
            except Exception:
                pass
        
        total_lancamentos = lancamentos.count()
        print(f"📊 Total de lançamentos encontrados: {total_lancamentos}")
        
        if total_lancamentos == 0:
            print("⚠️  Nenhum lançamento de despesa apropriada encontrado")
            return
        
        # Calcular totais
        total_valor = sum(abs(l.valor) for l in lancamentos)
        print(f"💰 Valor total dos lançamentos: R$ {total_valor:,.2f}")
        print()
        
        # Separar por tipo de origem
        lancamentos_socio = lancamentos.filter(historico_complementar__icontains="DespesaSocio ID:")
        lancamentos_rateada = lancamentos.filter(historico_complementar__icontains="DespesaRateada ID:")
        
        print(f"📋 Lançamentos de DespesaSocio: {lancamentos_socio.count()}")
        print(f"📋 Lançamentos de DespesaRateada: {lancamentos_rateada.count()}")
        print()
        
        print("📝 DETALHAMENTO DOS LANÇAMENTOS:")
        print("-" * 80)
        
        for i, lancamento in enumerate(lancamentos[:20], 1):  # Mostrar os primeiros 20
            # Extrair informação do tipo
            if "DespesaSocio ID:" in lancamento.historico_complementar:
                tipo = "SOCIO"
            elif "DespesaRateada ID:" in lancamento.historico_complementar:
                tipo = "RATEADA"
            else:
                tipo = "OUTRO"
            
            # Extrair descrição do débito
            historico_parts = lancamento.historico_complementar.split(" - ")
            descricao_debito = historico_parts[0] if historico_parts else "N/A"
            
            print(f"{i:2d}. {lancamento.data_movimentacao} | {tipo:7s} | R$ {abs(lancamento.valor):>8,.2f} | {descricao_debito}")
        
        if total_lancamentos > 20:
            print(f"... e mais {total_lancamentos - 20} lançamentos")
        
        print("-" * 80)
        
        # Verificar lançamentos mais recentes (criados hoje)
        hoje = datetime.now().date()
        lancamentos_hoje = lancamentos.filter(created_at__date=hoje)
        
        if lancamentos_hoje.exists():
            print(f"✅ Lançamentos criados hoje: {lancamentos_hoje.count()}")
            total_hoje = sum(abs(l.valor) for l in lancamentos_hoje)
            print(f"💰 Valor dos lançamentos de hoje: R$ {total_hoje:,.2f}")
        else:
            print("⚠️  Nenhum lançamento foi criado hoje")
        
        print()
        print("=" * 80)
        
    except Empresa.DoesNotExist:
        print(f"❌ Empresa ID {empresa_id} não encontrada")
    except Socio.DoesNotExist:
        print(f"❌ Sócio ID {socio_id} não encontrado na empresa {empresa_id}")
    except Exception as e:
        print(f"❌ Erro durante a verificação: {e}")

if __name__ == "__main__":
    verificar_lancamentos_despesas_apropriadas()
