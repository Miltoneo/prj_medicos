#!/usr/bin/env python3
"""
Script para ativar todas as empresas no sistema.
Coloca ativo=True em todas as empresas.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa

def main():
    print("=" * 60)
    print("SCRIPT: Ativar Todas as Empresas")
    print("=" * 60)
    
    try:
        # Buscar todas as empresas
        empresas = Empresa.objects.all()
        total_empresas = empresas.count()
        
        if total_empresas == 0:
            print("Nenhuma empresa encontrada no sistema")
            return
        
        print(f"Total de empresas encontradas: {total_empresas}")
        
        # Mostrar status atual
        ativas = empresas.filter(ativo=True).count()
        inativas = empresas.filter(ativo=False).count()
        
        print(f"Empresas ativas: {ativas}")
        print(f"Empresas inativas: {inativas}")
        
        if inativas == 0:
            print("Todas as empresas ja estao ativas!")
            return
        
        print("\nEmpresasĸue serao ativadas:")
        for empresa in empresas.filter(ativo=False):
            print(f"  ID {empresa.id}: {empresa.name}")
        
        # Ativar todas as empresas
        print(f"\nAtivando {inativas} empresas...")
        result = empresas.filter(ativo=False).update(ativo=True)
        
        print(f"Sucesso! {result} empresas ativadas")
        
        # Verificar resultado
        ativas_final = Empresa.objects.filter(ativo=True).count()
        print(f"Total de empresas ativas agora: {ativas_final}")
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
