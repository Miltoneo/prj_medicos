#!/usr/bin/env python3
"""
Script para verificar se os débitos da conta corrente foram removidos.
"""

import os
import django
from datetime import datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente

def verificar_status_conta_corrente():
    """Verifica o status atual da conta corrente"""
    print("=" * 80)
    print("VERIFICAÇÃO DO STATUS DA CONTA CORRENTE")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Contar total de movimentações
    total_movimentacoes = MovimentacaoContaCorrente.objects.count()
    print(f"📊 Total de movimentações na conta corrente: {total_movimentacoes}")
    
    # Contar débitos (valores negativos = saídas da conta)
    debitos = MovimentacaoContaCorrente.objects.filter(valor__lt=0)
    total_debitos = debitos.count()
    print(f"🔴 Total de débitos (saídas): {total_debitos}")
    
    # Contar créditos (valores positivos = entradas na conta)
    creditos = MovimentacaoContaCorrente.objects.filter(valor__gt=0)
    total_creditos = creditos.count()
    print(f"🟢 Total de créditos (entradas): {total_creditos}")
    
    # Valores zerados
    zerados = MovimentacaoContaCorrente.objects.filter(valor=0)
    total_zerados = zerados.count()
    print(f"⚪ Total de valores zerados: {total_zerados}")
    
    print()
    
    if total_debitos == 0:
        print("✅ SUCESSO: Nenhum débito encontrado na conta corrente!")
        print("   Todos os lançamentos de débito foram removidos com sucesso.")
    else:
        print(f"⚠️  ATENÇÃO: Ainda existem {total_debitos} débitos na conta corrente")
        print("   Listando os primeiros 10 débitos restantes:")
        
        for i, debito in enumerate(debitos[:10], 1):
            socio_nome = "Sem Sócio"
            if debito.socio:
                socio_nome = getattr(getattr(debito.socio, 'pessoa', None), 'name', str(debito.socio))
            
            print(f"   {i}. {debito.data_movimentacao} | {socio_nome} | R$ {abs(debito.valor):,.2f}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    verificar_status_conta_corrente()
