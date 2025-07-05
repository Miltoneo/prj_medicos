#!/usr/bin/env python
"""
Script para verificar o estado do banco de dados e criar as tabelas necessárias
"""
import os
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def check_database_tables():
    """Verifica quais tabelas existem no banco"""
    print("=== VERIFICANDO TABELAS NO BANCO DE DADOS ===\n")
    
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Tabelas SaaS que deveriam existir
        saas_tables = ['conta', 'licenca', 'conta_membership']
        
        print("Tabelas SaaS necessárias:")
        for table in saas_tables:
            if table in tables:
                print(f"  ✅ {table} - EXISTE")
            else:
                print(f"  ❌ {table} - NÃO EXISTE")
        
        print(f"\nTotal de tabelas no banco: {len(tables)}")
        return tables, saas_tables

def check_migrations():
    """Verifica o estado das migrações"""
    print("\n=== VERIFICANDO MIGRAÇÕES ===\n")
    
    try:
        from django.db.migrations.executor import MigrationExecutor
        from django.db import DEFAULT_DB_ALIAS
        
        executor = MigrationExecutor(connection)
        
        # Verificar migrações aplicadas
        applied = executor.loader.applied_migrations
        print(f"Migrações aplicadas: {len(applied)}")
        
        for migration in applied:
            if migration[0] == 'medicos':
                print(f"  ✅ {migration[0]}.{migration[1]}")
        
        # Verificar migrações pendentes
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            print(f"\nMigrações pendentes: {len(plan)}")
            for migration, backwards in plan:
                print(f"  ⏳ {migration}")
        else:
            print("\n✅ Nenhuma migração pendente")
            
    except Exception as e:
        print(f"❌ Erro ao verificar migrações: {e}")

def create_missing_tables():
    """Tenta criar as tabelas que faltam"""
    print("\n=== CRIANDO TABELAS FALTANTES ===\n")
    
    try:
        # Primeiro, tentar fazer uma nova migração
        print("Tentando criar migração...")
        from django.core.management.commands.makemigrations import Command as MakeMigrationsCommand
        from django.core.management.base import CommandError
        
        # Força a criação de uma nova migração
        os.system('cd f:\\Projects\\Django\\prj_medicos && F:\\Projects\\Django\\prj_medicos\\myenv\\Scripts\\python.exe manage.py makemigrations medicos --verbosity=2')
        
        print("Aplicando migrações...")
        os.system('cd f:\\Projects\\Django\\prj_medicos && F:\\Projects\\Django\\prj_medicos\\myenv\\Scripts\\python.exe manage.py migrate --verbosity=2')
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == '__main__':
    try:
        tables, saas_tables = check_database_tables()
        check_migrations()
        
        # Verificar se as tabelas SaaS estão faltando
        missing_tables = [table for table in saas_tables if table not in tables]
        
        if missing_tables:
            print(f"\n❌ Tabelas faltantes: {missing_tables}")
            create_missing_tables()
        else:
            print(f"\n✅ Todas as tabelas SaaS existem!")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
