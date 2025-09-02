#!/usr/bin/env python3
"""
Script para apagar todas as movimentações de débito da conta corrente de todos os sócios.

ATENÇÃO: Este script remove permanentemente todos os lançamentos de débito (saídas da conta)
da conta corrente. Execute apenas se tiver certeza absoluta da operação.

Definição de débito bancário no sistema:
- Débito = Saída da conta = valor negativo (< 0)
- Crédito = Entrada na conta = valor positivo (> 0)
"""

import os
import sys
import django
from datetime import datetime
from django.db import transaction

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.base import Socio, Empresa


def listar_debitos_existentes():
    """Lista todos os débitos existentes antes da exclusão"""
    print("=" * 80)
    print("LISTAGEM DE DÉBITOS EXISTENTES (antes da exclusão)")
    print("=" * 80)
    
    # Buscar todos os débitos (valores negativos = saídas da conta)
    debitos = MovimentacaoContaCorrente.objects.filter(valor__lt=0).order_by('data_movimentacao')
    
    if not debitos.exists():
        print("⚠ Nenhum débito encontrado na conta corrente")
        return 0
    
    total_debitos = debitos.count()
    total_valor = sum(abs(debito.valor) for debito in debitos)
    
    print(f"📊 Total de débitos encontrados: {total_debitos}")
    print(f"💰 Valor total dos débitos: R$ {total_valor:,.2f}")
    print()
    
    # Agrupar por sócio
    socios_com_debitos = {}
    for debito in debitos:
        socio_nome = "Sem Sócio"
        if debito.socio:
            socio_nome = getattr(getattr(debito.socio, 'pessoa', None), 'name', str(debito.socio))
        
        if socio_nome not in socios_com_debitos:
            socios_com_debitos[socio_nome] = {
                'quantidade': 0,
                'valor_total': 0
            }
        
        socios_com_debitos[socio_nome]['quantidade'] += 1
        socios_com_debitos[socio_nome]['valor_total'] += abs(debito.valor)
    
    print("Resumo por sócio:")
    for socio_nome, dados in socios_com_debitos.items():
        print(f"  👤 {socio_nome}: {dados['quantidade']} débitos, R$ {dados['valor_total']:,.2f}")
    
    print()
    return total_debitos


def confirmar_exclusao():
    """Solicita confirmação do usuário para a exclusão"""
    print("⚠️  ATENÇÃO: OPERAÇÃO DESTRUTIVA ⚠️")
    print("Este script irá APAGAR PERMANENTEMENTE todos os débitos da conta corrente!")
    print("Esta operação NÃO PODE SER DESFEITA!")
    print()
    
    resposta = input("Digite 'CONFIRMO' (em maiúsculas) para prosseguir: ").strip()
    return resposta == "CONFIRMO"


def apagar_todos_os_debitos():
    """Apaga todas as movimentações de débito da conta corrente"""
    print("=" * 80)
    print("EXECUTANDO EXCLUSÃO DOS DÉBITOS")
    print("=" * 80)
    
    try:
        with transaction.atomic():
            # Buscar todos os débitos (valores negativos = saídas da conta)
            debitos = MovimentacaoContaCorrente.objects.filter(valor__lt=0)
            
            if not debitos.exists():
                print("⚠ Nenhum débito encontrado para exclusão")
                return 0
            
            total_debitos = debitos.count()
            total_valor = sum(abs(debito.valor) for debito in debitos)
            
            print(f"🗑️  Apagando {total_debitos} débitos...")
            print(f"💰 Valor total dos débitos: R$ {total_valor:,.2f}")
            
            # Executar a exclusão
            resultado = debitos.delete()
            
            print(f"✅ Exclusão concluída!")
            print(f"📊 Registros apagados: {resultado[0]}")
            print(f"📋 Detalhes: {resultado[1]}")
            
            return resultado[0]
            
    except Exception as e:
        print(f"❌ Erro durante a exclusão: {str(e)}")
        return 0


def validar_exclusao():
    """Valida se a exclusão foi bem-sucedida"""
    print("=" * 80)
    print("VALIDAÇÃO PÓS-EXCLUSÃO")
    print("=" * 80)
    
    # Verificar se ainda existem débitos
    debitos_restantes = MovimentacaoContaCorrente.objects.filter(valor__lt=0)
    
    if debitos_restantes.exists():
        print(f"⚠️  Ainda existem {debitos_restantes.count()} débitos no sistema!")
        return False
    else:
        print("✅ Validação concluída: Nenhum débito encontrado no sistema")
        return True


def main():
    """Função principal do script"""
    print("🚀 Iniciando script de exclusão de débitos da conta corrente...")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Verificar se há argumento de confirmação automática
    confirmar_automaticamente = len(sys.argv) > 1 and sys.argv[1] == "--confirmar"
    
    # 1. Listar débitos existentes
    total_inicial = listar_debitos_existentes()
    
    if total_inicial == 0:
        print("✅ Script finalizado: Nenhum débito para apagar")
        return
    
    # 2. Solicitar confirmação (se não for automática)
    if confirmar_automaticamente:
        print("✅ Confirmação automática ativada (--confirmar)")
    elif not confirmar_exclusao():
        print("❌ Operação cancelada pelo usuário")
        return
    
    print()
    print("🔄 Iniciando exclusão...")
    
    # 3. Executar a exclusão
    registros_apagados = apagar_todos_os_debitos()
    
    if registros_apagados > 0:
        print()
        # 4. Validar exclusão
        validacao_ok = validar_exclusao()
        
        if validacao_ok:
            print()
            print("=" * 80)
            print("RESUMO FINAL")
            print("=" * 80)
            print(f"✅ Exclusão bem-sucedida!")
            print(f"📊 Total de débitos apagados: {registros_apagados}")
            print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print("=" * 80)
        else:
            print("⚠️  Exclusão incompleta - verifique manualmente")
    else:
        print("❌ Nenhum registro foi apagado")


if __name__ == "__main__":
    main()
