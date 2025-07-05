#!/usr/bin/env python
"""
Script para criar tabela usando Django migrations
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection

def main():
    print("=== CRIANDO TABELA VIA DJANGO MIGRATIONS ===")
    
    try:
        with connection.cursor() as cursor:
            # Verificar se a tabela existe
            cursor.execute("SHOW TABLES LIKE 'conta_membership'")
            if cursor.fetchall():
                print("   ✓ Tabela conta_membership já existe")
                return True
            
            print("   Tabela conta_membership não existe")
        
        # Usar o Django para criar as tabelas
        print("\n1. Executando migrate para criar todas as tabelas...")
        
        # Executar migrate com --fake-initial para ignorar tabelas existentes
        os.system('python manage.py migrate --fake-initial')
        
        print("\n2. Verificando se a tabela foi criada...")
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'conta_membership'")
            if cursor.fetchall():
                print("   ✓ Tabela conta_membership criada com sucesso!")
                
                # Mostrar estrutura
                cursor.execute("DESCRIBE conta_membership")
                for row in cursor.fetchall():
                    print(f"   {row}")
                return True
            else:
                print("   ❌ Tabela ainda não existe")
                return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
