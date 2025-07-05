#!/usr/bin/env python
"""
Script para criar migrações automaticamente com valores padrão
"""
import os
import sys
import subprocess
from datetime import datetime
from django.utils import timezone

# Configurar o ambiente
project_path = r'f:\Projects\Django\prj_medicos'
python_path = r'F:\Projects\Django\prj_medicos\myenv\Scripts\python.exe'

def create_migration_with_defaults():
    """Cria a migração fornecendo valores padrão quando necessário"""
    
    print("🔄 Criando migração com valores padrão...")
    
    # Mudar para o diretório do projeto
    os.chdir(project_path)
    
    try:
        # Executar makemigrations de forma interativa
        process = subprocess.Popen([
            python_path, 'manage.py', 'makemigrations', 'medicos'
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Fornecer respostas para as perguntas do Django
        inputs = [
            "1",  # Escolher opção 1 (fornecer valor padrão)
            "timezone.now",  # Valor padrão para created_at
        ]
        
        stdout, stderr = process.communicate(input="\n".join(inputs))
        
        print("STDOUT:")
        print(stdout)
        
        if stderr:
            print("STDERR:")
            print(stderr)
            
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ Erro ao criar migração: {e}")
        return False

def run_migrations():
    """Executa as migrações"""
    
    print("🔄 Executando migrações...")
    
    try:
        result = subprocess.run([
            python_path, 'manage.py', 'migrate'
        ], cwd=project_path, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Erro ao executar migrações: {e}")
        return False

if __name__ == '__main__':
    print("🚀 INICIANDO PROCESSO DE MIGRAÇÃO\n")
    
    # Criar migração
    if create_migration_with_defaults():
        print("✅ Migração criada com sucesso!")
        
        # Executar migração
        if run_migrations():
            print("✅ Migrações executadas com sucesso!")
            print("\n🎉 Banco de dados atualizado!")
        else:
            print("❌ Erro ao executar migrações")
    else:
        print("❌ Erro ao criar migração")
