#!/usr/bin/env python
"""
Script para verificar estrutura das tabelas
"""
import os
import sys
import django
from django.db import connection

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def main():
    print("=== VERIFICANDO ESTRUTURA DAS TABELAS ===")
    
    try:
        with connection.cursor() as cursor:
            # Verificar tabela customuser
            print("\n1. Estrutura da tabela customuser:")
            cursor.execute("DESCRIBE customuser")
            for row in cursor.fetchall():
                print(f"   {row}")
            
            # Verificar tabela conta
            print("\n2. Estrutura da tabela conta:")
            cursor.execute("DESCRIBE conta")
            for row in cursor.fetchall():
                print(f"   {row}")
            
            # Verificar se conta_membership existe
            print("\n3. Verificando se conta_membership existe:")
            cursor.execute("SHOW TABLES LIKE 'conta_membership'")
            result = cursor.fetchall()
            if result:
                print("   Tabela conta_membership existe")
                cursor.execute("DESCRIBE conta_membership")
                for row in cursor.fetchall():
                    print(f"   {row}")
            else:
                print("   Tabela conta_membership NÃO existe")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
