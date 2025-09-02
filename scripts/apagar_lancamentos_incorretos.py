#!/usr/bin/env python3
"""
Script para apagar lançamentos incorretos de despesas apropriadas
"""

import os
import django
from datetime import datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.conta_corrente import MovimentacaoContaCorrente

def apagar_lancamentos_incorretos():
    """Apaga lançamentos com descrição genérica 'Despesas Apropriadas de Sócio'"""
    print("=" * 80)
    print("APAGANDO LANÇAMENTOS INCORRETOS")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Buscar lançamentos com descrição incorreta
    lancamentos_incorretos = MovimentacaoContaCorrente.objects.filter(
        descricao_movimentacao__descricao="Despesas Apropriadas de Sócio"
    )
    
    total = lancamentos_incorretos.count()
    print(f"📊 Lançamentos incorretos encontrados: {total}")
    
    if total == 0:
        print("✅ Nenhum lançamento incorreto encontrado")
        return
    
    # Mostrar detalhes dos lançamentos que serão apagados
    print("\n📝 Lançamentos que serão apagados:")
    for lancamento in lancamentos_incorretos[:10]:  # Mostrar primeiros 10
        socio_nome = getattr(getattr(lancamento.socio, 'pessoa', None), 'name', 'Sem sócio')
        print(f"   • {lancamento.data_movimentacao} | {socio_nome} | R$ {abs(lancamento.valor):,.2f}")
    
    if total > 10:
        print(f"   ... e mais {total - 10} lançamentos")
    
    print(f"\n⚠️  ATENÇÃO: {total} lançamentos serão APAGADOS!")
    
    try:
        with transaction.atomic():
            # Apagar os lançamentos
            resultado = lancamentos_incorretos.delete()
            
            print(f"\n✅ Lançamentos apagados com sucesso!")
            print(f"📊 Total apagado: {resultado[0]} registros")
            print(f"📋 Detalhes: {resultado[1]}")
    
    except Exception as e:
        print(f"\n❌ Erro ao apagar lançamentos: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    apagar_lancamentos_incorretos()
