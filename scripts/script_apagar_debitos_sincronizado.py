#!/usr/bin/env python3
"""
SCRIPT MELHORADO: Apagar débitos da conta corrente COM sincronização automática.
Esta versão garante que os signals sejam disparados corretamente.

Usage:
    python script_apagar_debitos_sincronizado.py --empresa_id 5 --confirmar
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.base import Empresa

def listar_debitos(empresa_id=None):
    """Lista todos os débitos da conta corrente."""
    print("=" * 80)
    print("LISTANDO DÉBITOS ATUAIS")
    print("=" * 80)
    
    # Filtrar débitos (valores negativos = saídas da conta)
    debitos = MovimentacaoContaCorrente.objects.filter(valor__lt=0)
    
    if empresa_id:
        # Filtrar por empresa através do sócio
        debitos = debitos.filter(socio__empresa_id=empresa_id)
        empresa = Empresa.objects.get(id=empresa_id)
        print(f"🏢 Empresa: {empresa}")
    
    if not debitos.exists():
        print("✅ Nenhum débito encontrado")
        return [], 0, Decimal('0.00')
    
    total_debitos = debitos.count()
    total_valor = sum(abs(debito.valor) for debito in debitos)
    
    print(f"📊 Total de débitos: {total_debitos}")
    print(f"💰 Valor total: R$ {total_valor:,.2f}")
    print()
    
    # Mostrar os primeiros 10 para referência
    print("📋 Primeiros 10 débitos:")
    for i, debito in enumerate(debitos[:10], 1):
        print(f"   {i:2d}. {debito.data_movimentacao} | {debito.socio} | R$ {debito.valor} | {debito.historico_complementar}")
    
    if total_debitos > 10:
        print(f"   ... e mais {total_debitos - 10} débitos")
    
    return list(debitos), total_debitos, total_valor


def apagar_debitos_com_signals(debitos_list):
    """
    Apaga débitos um por um para garantir que signals sejam disparados.
    IMPORTANTE: Isso permite sincronização automática com despesas.
    """
    print("=" * 80)
    print("EXECUTANDO EXCLUSÃO COM SINCRONIZAÇÃO")
    print("=" * 80)
    
    if not debitos_list:
        print("⚠️ Lista de débitos vazia")
        return 0
    
    total_debitos = len(debitos_list)
    print(f"🗑️ Iniciando exclusão de {total_debitos} débitos...")
    print("⚠️ Usando exclusão individual para disparar signals!")
    
    removidos = 0
    
    try:
        with transaction.atomic():
            for i, debito in enumerate(debitos_list, 1):
                # Mostrar progresso a cada 50 itens
                if i % 50 == 0 or i == total_debitos:
                    print(f"   📊 Progresso: {i}/{total_debitos} ({(i/total_debitos)*100:.1f}%)")
                
                # Excluir individualmente (dispara signals)
                debito.delete()
                removidos += 1
        
        print(f"✅ Exclusão concluída!")
        print(f"📊 Débitos removidos: {removidos}")
        
        return removidos
        
    except Exception as e:
        print(f"❌ Erro durante a exclusão: {str(e)}")
        return removidos


def apagar_debitos_em_lote(debitos_queryset):
    """
    Apaga débitos em lote (MAIS RÁPIDO mas NÃO dispara signals).
    ATENÇÃO: Esta opção pode causar inconsistências na sincronização!
    """
    print("=" * 80)
    print("EXECUTANDO EXCLUSÃO EM LOTE (SEM SINCRONIZAÇÃO)")
    print("=" * 80)
    
    total_debitos = debitos_queryset.count()
    total_valor = sum(abs(debito.valor) for debito in debitos_queryset)
    
    print(f"🗑️ Apagando {total_debitos} débitos em lote...")
    print(f"💰 Valor total: R$ {total_valor:,.2f}")
    print("⚠️ AVISO: Signals NÃO serão disparados!")
    
    try:
        with transaction.atomic():
            resultado = debitos_queryset.delete()
            
        print(f"✅ Exclusão concluída!")
        print(f"📊 Registros apagados: {resultado[0]}")
        print(f"📋 Detalhes: {resultado[1]}")
        
        return resultado[0]
        
    except Exception as e:
        print(f"❌ Erro durante a exclusão: {str(e)}")
        return 0


def validar_exclusao(empresa_id=None):
    """Valida se a exclusão foi bem-sucedida."""
    print("=" * 80)
    print("VALIDAÇÃO PÓS-EXCLUSÃO")
    print("=" * 80)
    
    debitos = MovimentacaoContaCorrente.objects.filter(valor__lt=0)
    
    if empresa_id:
        debitos = debitos.filter(socio__empresa_id=empresa_id)
    
    count_restantes = debitos.count()
    
    if count_restantes == 0:
        print("✅ SUCESSO: Todos os débitos foram removidos")
    else:
        print(f"⚠️ Ainda restam {count_restantes} débitos")
        
        # Mostrar alguns exemplos
        for debito in debitos[:5]:
            print(f"   → {debito.data_movimentacao} | {debito.socio} | R$ {debito.valor}")
    
    return count_restantes


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Apagar débitos da conta corrente com opções de sincronização')
    parser.add_argument('--empresa_id', type=int, help='ID da empresa (opcional, se não informado apaga de todas)')
    parser.add_argument('--metodo', choices=['individual', 'lote'], default='individual', 
                        help='Método de exclusão: individual (com signals) ou lote (sem signals)')
    parser.add_argument('--confirmar', action='store_true', help='Confirma a exclusão sem interação')
    
    args = parser.parse_args()
    
    print("🗑️ SCRIPT DE EXCLUSÃO DE DÉBITOS DA CONTA CORRENTE")
    print(f"📅 Data/Hora: {datetime.now()}")
    print(f"🔧 Método: {args.metodo}")
    if args.empresa_id:
        print(f"🏢 Empresa ID: {args.empresa_id}")
    else:
        print(f"🏢 Escopo: Todas as empresas")
    print()
    
    try:
        # Listar débitos atuais
        debitos_list, total_debitos, total_valor = listar_debitos(args.empresa_id)
        
        if total_debitos == 0:
            print("✅ Nada para fazer - não há débitos para excluir")
            return
        
        # Solicitar confirmação
        if not args.confirmar:
            print("⚠️ ATENÇÃO: OPERAÇÃO DESTRUTIVA ⚠️")
            print("Este script irá APAGAR PERMANENTEMENTE os débitos listados!")
            print("Esta operação NÃO PODE SER DESFEITA!")
            print()
            
            if args.metodo == 'lote':
                print("🚨 MÉTODO LOTE SELECIONADO:")
                print("   → Mais rápido, mas NÃO dispara signals")
                print("   → Pode causar inconsistências na sincronização com despesas")
                print("   → Recomendado apenas se você souber o que está fazendo")
            else:
                print("✅ MÉTODO INDIVIDUAL SELECIONADO:")
                print("   → Dispara signals corretamente")
                print("   → Mantém sincronização com despesas")
                print("   → Recomendado para operação segura")
            
            resposta = input("\nDigite 'CONFIRMO' (em maiúsculas) para prosseguir: ").strip()
            if resposta != "CONFIRMO":
                print("❌ Operação cancelada pelo usuário")
                return
        
        # Executar exclusão conforme método escolhido
        if args.metodo == 'individual':
            removidos = apagar_debitos_com_signals(debitos_list)
        else:
            # Recriar queryset para lote
            debitos_qs = MovimentacaoContaCorrente.objects.filter(valor__lt=0)
            if args.empresa_id:
                debitos_qs = debitos_qs.filter(socio__empresa_id=args.empresa_id)
            removidos = apagar_debitos_em_lote(debitos_qs)
        
        # Validar resultado
        count_restantes = validar_exclusao(args.empresa_id)
        
        # Resultado final
        print("\n" + "=" * 80)
        print("RESULTADO FINAL")
        print("=" * 80)
        print(f"📊 Débitos removidos: {removidos}")
        print(f"📊 Débitos restantes: {count_restantes}")
        
        if count_restantes == 0:
            print("🎉 EXCLUSÃO 100% CONCLUÍDA!")
        else:
            print("⚠️ Exclusão parcial - verifique os débitos restantes")
            
        if args.metodo == 'lote':
            print("\n⚠️ ATENÇÃO: Método lote foi usado!")
            print("   Recomenda-se executar o script de correção de sincronização:")
            print("   → python corrigir_sincronizacao.py")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
