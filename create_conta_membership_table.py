#!/usr/bin/env python
"""
Script para criar a tabela conta_membership diretamente no banco
"""
import os
import sys
import django
import MySQLdb

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.conf import settings

def create_conta_membership_table():
    """Cria a tabela conta_membership diretamente no MySQL"""
    
    db_config = settings.DATABASES['default']
    
    try:
        # Conectar ao banco
        connection = MySQLdb.connect(
            host=db_config['HOST'],
            user=db_config['USER'],
            passwd=db_config['PASSWORD'],
            db=db_config['NAME'],
            port=int(db_config['PORT'])
        )
        
        cursor = connection.cursor()
        
        print("=== CRIANDO TABELA conta_membership ===")
        
        # Verificar se a tabela já existe
        cursor.execute("SHOW TABLES LIKE 'conta_membership';")
        if cursor.fetchone():
            print("   ⚠️  Tabela conta_membership já existe")
            return True
        
        # SQL para criar a tabela conta_membership
        create_table_sql = """
        CREATE TABLE `conta_membership` (
            `id` int NOT NULL AUTO_INCREMENT,
            `role` varchar(20) NOT NULL DEFAULT 'member',
            `date_joined` datetime(6) NOT NULL,
            `user_id` int NOT NULL,
            `conta_id` int NOT NULL,
            `invited_by_id` int DEFAULT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `conta_membership_user_id_conta_id_uniq` (`user_id`,`conta_id`),
            KEY `conta_membership_user_id_idx` (`user_id`),
            KEY `conta_membership_conta_id_idx` (`conta_id`),
            KEY `conta_membership_invited_by_id_idx` (`invited_by_id`),
            CONSTRAINT `conta_membership_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `customuser` (`id`) ON DELETE CASCADE,
            CONSTRAINT `conta_membership_conta_id_fk` FOREIGN KEY (`conta_id`) REFERENCES `conta` (`id`) ON DELETE CASCADE,
            CONSTRAINT `conta_membership_invited_by_id_fk` FOREIGN KEY (`invited_by_id`) REFERENCES `customuser` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Executar a criação da tabela
        cursor.execute(create_table_sql)
        connection.commit()
        
        print("   ✓ Tabela conta_membership criada com sucesso!")
        
        # Verificar se foi criada
        cursor.execute("SHOW TABLES LIKE 'conta_membership';")
        if cursor.fetchone():
            print("   ✓ Tabela confirmada no banco de dados")
            
            # Mostrar estrutura da tabela
            cursor.execute("DESCRIBE conta_membership;")
            columns = cursor.fetchall()
            print("\n   Estrutura da tabela:")
            for column in columns:
                print(f"   - {column[0]}: {column[1]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao criar tabela: {e}")
        return False
        
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    print("=== SCRIPT PARA CRIAR TABELA conta_membership ===")
    
    success = create_conta_membership_table()
    
    if success:
        print("\n✅ Tabela conta_membership criada com sucesso!")
        print("\nAgora você pode:")
        print("1. Executar o script de criação de usuários")
        print("2. Testar o login no sistema")
    else:
        print("\n❌ Falha ao criar a tabela")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
