#!/usr/bin/env python
"""
Script para executar limpeza de movimentações órfãs
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.financeiro import Financeiro
from medicos.signals_financeiro import limpar_movimentacoes_orfas

def main():
    print("=== ANÁLISE DE MOVIMENTAÇÕES ÓRFÃS ===")
    
    # Verificar movimentações órfãs
    movimentacoes_orfas = Financeiro.objects.filter(
        nota_fiscal__isnull=True,
        descricao_movimentacao_financeira__descricao='Credito de Nota Fiscal'
    )
    
    count_orfas = movimentacoes_orfas.count()
    print(f"Movimentações órfãs encontradas: {count_orfas}")
    
    if count_orfas > 0:
        print("\nDetalhes das movimentações órfãs:")
        for mov in movimentacoes_orfas:
            print(f"  - ID: {mov.id}, Sócio: {mov.socio.pessoa.name}, Valor: R$ {mov.valor}, Data: {mov.data_movimentacao}")
        
        resposta = input("\nDeseja remover essas movimentações órfãs? (s/N): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            print("\nExecutando limpeza...")
            count_removidas = limpar_movimentacoes_orfas()
            print(f"✅ Limpeza concluída! {count_removidas} movimentação(ões) removida(s).")
        else:
            print("❌ Limpeza cancelada pelo usuário.")
    else:
        print("✅ Nenhuma movimentação órfã encontrada. Dados já estão limpos!")

if __name__ == "__main__":
    main()
