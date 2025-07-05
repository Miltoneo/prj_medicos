#!/usr/bin/env python
"""
Script simples para criar tabela conta_membership usando SQL direto
"""
import os
import sys
import django
from django.db import connection

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def main():
    print("=== CRIANDO TABELA conta_membership COM SQL DIRETO ===")
    
    try:
        with connection.cursor() as cursor:
            # Verificar se conta_membership já existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'prd_milenio' 
                AND table_name = 'conta_membership'
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print("   ⚠️  Tabela conta_membership já existe, removendo...")
                cursor.execute("DROP TABLE conta_membership")
                print("   ✓ Tabela removida")
            
            print("\n1. Verificando nome correto da tabela de usuários...")
            cursor.execute("SHOW TABLES LIKE '%user%'")
            user_tables = cursor.fetchall()
            print(f"   Tabelas de usuário encontradas: {user_tables}")
            
            # Verificar estrutura da tabela customuser
            print("\n2. Verificando estrutura da tabela customuser...")
            try:
                cursor.execute("DESCRIBE customuser")
                user_structure = cursor.fetchall()
                print("   Estrutura customuser:")
                for row in user_structure:
                    print(f"     {row}")
                user_table = "customuser"
            except:
                try:
                    cursor.execute("DESCRIBE customUser")
                    user_structure = cursor.fetchall()
                    print("   Estrutura customUser:")
                    for row in user_structure:
                        print(f"     {row}")
                    user_table = "customUser"
                except:
                    print("   ❌ Não foi possível encontrar tabela de usuários")
                    return False
            
            # Verificar estrutura da tabela conta
            print("\n3. Verificando estrutura da tabela conta...")
            cursor.execute("DESCRIBE conta")
            conta_structure = cursor.fetchall()
            print("   Estrutura conta:")
            for row in conta_structure:
                print(f"     {row}")
            
            print(f"\n4. Criando tabela conta_membership referenciando '{user_table}'...")
            
            # SQL para criar a tabela
            create_table_sql = f"""
            CREATE TABLE conta_membership (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                conta_id INT NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                date_joined DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                invited_by_id INT NULL,
                UNIQUE KEY unique_user_conta (user_id, conta_id),
                INDEX idx_user_id (user_id),
                INDEX idx_conta_id (conta_id),
                INDEX idx_invited_by_id (invited_by_id),
                CONSTRAINT conta_membership_user_id_fk 
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id) ON DELETE CASCADE,
                CONSTRAINT conta_membership_conta_id_fk 
                    FOREIGN KEY (conta_id) REFERENCES conta(id) ON DELETE CASCADE,
                CONSTRAINT conta_membership_invited_by_id_fk 
                    FOREIGN KEY (invited_by_id) REFERENCES {user_table}(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_sql)
            print("   ✓ Tabela conta_membership criada com sucesso!")
            
            # Verificar a estrutura criada
            print("\n5. Verificando estrutura criada:")
            cursor.execute("DESCRIBE conta_membership")
            for row in cursor.fetchall():
                print(f"   {row}")
                
            # Testar se o modelo funciona
            print("\n6. Testando acesso ao modelo...")
            from medicos.models import ContaMembership
            count = ContaMembership.objects.count()
            print(f"   ✓ Modelo funcionando. Registros: {count}")
                
        return True
        
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
