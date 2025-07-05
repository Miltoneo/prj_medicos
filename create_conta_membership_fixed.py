#!/usr/bin/env python
"""
Script corrigido para criar tabela conta_membership
"""
import os
import sys
import django
from django.db import connection

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def main():
    print("=== CRIANDO TABELA conta_membership ===")
    
    try:
        with connection.cursor() as cursor:
            # Primeiro verificar os tipos das colunas nas tabelas existentes
            print("\n1. Verificando tipos de dados das tabelas...")
            
            # Verificar customuser
            print("   Estrutura da tabela customuser:")
            cursor.execute("DESCRIBE customuser")
            customuser_structure = cursor.fetchall()
            for row in customuser_structure:
                if row[0] == 'id':  # campo, tipo, null, key, default, extra
                    print(f"     customuser.id: {row[1]}")
                    customuser_id_type = row[1]
                    break
            
            # Verificar conta
            print("   Estrutura da tabela conta:")
            cursor.execute("DESCRIBE conta")
            conta_structure = cursor.fetchall()
            for row in conta_structure:
                if row[0] == 'id':
                    print(f"     conta.id: {row[1]}")
                    conta_id_type = row[1]
                    break
            
            # Verificar se conta_membership já existe
            cursor.execute("SHOW TABLES LIKE 'conta_membership'")
            if cursor.fetchall():
                print("\n2. Tabela conta_membership já existe, removendo...")
                cursor.execute("DROP TABLE conta_membership")
                print("   ✓ Tabela removida")
            
            print("\n3. Criando tabela conta_membership...")
            
            # SQL corrigido usando os tipos exatos das outras tabelas
            create_table_sql = f"""
            CREATE TABLE conta_membership (
                id {customuser_id_type} AUTO_INCREMENT PRIMARY KEY,
                user_id {customuser_id_type} NOT NULL,
                conta_id {conta_id_type} NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                date_joined DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                invited_by_id {customuser_id_type} NULL,
                UNIQUE KEY unique_user_conta (user_id, conta_id),
                CONSTRAINT conta_membership_user_id_fk 
                    FOREIGN KEY (user_id) REFERENCES customuser(id) ON DELETE CASCADE,
                CONSTRAINT conta_membership_conta_id_fk 
                    FOREIGN KEY (conta_id) REFERENCES conta(id) ON DELETE CASCADE,
                CONSTRAINT conta_membership_invited_by_id_fk 
                    FOREIGN KEY (invited_by_id) REFERENCES customuser(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            print(f"   SQL: {create_table_sql}")
            cursor.execute(create_table_sql)
            print("   ✓ Tabela conta_membership criada com sucesso!")
            
            # Verificar a estrutura criada
            print("\n4. Verificando estrutura criada:")
            cursor.execute("DESCRIBE conta_membership")
            for row in cursor.fetchall():
                print(f"   {row}")
                
            # Verificar se a tabela foi criada
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'prd_milenio' 
                AND table_name = 'conta_membership'
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print("   ✓ Tabela conta_membership confirmada!")
                return True
            else:
                print("   ❌ Tabela conta_membership ainda não existe")
                return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Tabela conta_membership criada com sucesso!")
    else:
        print("\n❌ Falha ao criar a tabela")
    sys.exit(0 if success else 1)
