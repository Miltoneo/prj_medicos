#!/usr/bin/env python3
"""
Script de teste para identificar e corrigir o problema da descrição.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa
from medicos.models.financeiro import DescricaoMovimentacaoFinanceira

def testar_descricao():
    """Testa a criação de descrição de movimentação."""
    print("=== TESTE DE DESCRIÇÃO ===")
    
    # Buscar uma empresa
    empresa = Empresa.objects.filter(ativo=True).first()
    if not empresa:
        print("ERRO: Nenhuma empresa ativa encontrada")
        return
    
    print(f"Empresa: {empresa.name}")
    
    # Verificar campos do modelo
    print("\nCampos do modelo DescricaoMovimentacaoFinanceira:")
    for field in DescricaoMovimentacaoFinanceira._meta.fields:
        print(f"  {field.name}: {field.__class__.__name__}")
    
    # Tentar criar uma descrição
    try:
        descricao_texto = "Débito Teste"
        
        print(f"\nCriando descrição: {descricao_texto}")
        
        descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
            empresa=empresa,
            descricao=descricao_texto,
            defaults={
                'observacoes': 'Teste de criação de descrição'
            }
        )
        
        if created:
            print(f"✅ Descrição criada com sucesso: ID {descricao.id}")
        else:
            print(f"✅ Descrição já existia: ID {descricao.id}")
            
        print(f"Descrição: {descricao.descricao}")
        print(f"Empresa: {descricao.empresa}")
        
    except Exception as e:
        print(f"❌ Erro ao criar descrição: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_descricao()
