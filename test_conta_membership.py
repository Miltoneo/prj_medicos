#!/usr/bin/env python
"""
Script para verificar se a tabela conta_membership foi criada
"""
import os
import sys
import django
from django.db import connection

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def main():
    print("=== VERIFICANDO TABELA conta_membership ===")
    
    try:
        with connection.cursor() as cursor:
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'prd_milenio' 
                AND table_name = 'conta_membership'
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print("✓ Tabela conta_membership existe!")
                
                # Mostrar estrutura
                print("\nEstrutura da tabela:")
                cursor.execute("DESCRIBE conta_membership")
                for row in cursor.fetchall():
                    print(f"   {row}")
                
                # Testar se o modelo Django funciona
                print("\n=== TESTANDO MODELO DJANGO ===")
                from medicos.models import ContaMembership, CustomUser, Conta
                
                # Verificar se conseguimos consultar
                count = ContaMembership.objects.count()
                print(f"   Registros na tabela: {count}")
                
                # Verificar usuários e contas disponíveis
                users_count = CustomUser.objects.count()
                contas_count = Conta.objects.count()
                print(f"   Usuários disponíveis: {users_count}")
                print(f"   Contas disponíveis: {contas_count}")
                
                return True
            else:
                print("❌ Tabela conta_membership NÃO existe")
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Tabela conta_membership está funcionando!")
    else:
        print("\n❌ Problemas com a tabela conta_membership")
    sys.exit(0 if success else 1)
