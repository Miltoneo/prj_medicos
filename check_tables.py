#!/usr/bin/env python
"""
Script simples para verificar se as tabelas foram criadas
"""
import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import connection

print("=== VERIFICANDO TABELAS NO BANCO ===\n")

try:
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Tabelas SaaS
        saas_tables = ['conta', 'licenca', 'conta_membership']
        
        print("Status das tabelas SaaS:")
        for table in saas_tables:
            if table in all_tables:
                print(f"  ✅ {table}")
                
                # Verificar estrutura da tabela
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"     Colunas: {len(columns)}")
                for col in columns[:3]:  # Mostrar apenas as primeiras 3 colunas
                    print(f"       - {col[0]} ({col[1]})")
                if len(columns) > 3:
                    print(f"       ... e mais {len(columns) - 3} colunas")
            else:
                print(f"  ❌ {table} - NÃO EXISTE")
        
        print(f"\nTotal de tabelas no banco: {len(all_tables)}")
        
        # Testar se podemos importar os modelos
        print("\n=== TESTANDO IMPORTAÇÕES ===")
        
        from medicos.models import Conta, ContaMembership, Licenca
        print("✅ Modelos SaaS importados com sucesso")
        
        # Verificar se podemos fazer consultas básicas
        print(f"✅ Contas no banco: {Conta.objects.count()}")
        print(f"✅ Licenças no banco: {Licenca.objects.count()}")
        print(f"✅ Memberships no banco: {ContaMembership.objects.count()}")
        
        print("\n🎉 SISTEMA SAAS FUNCIONANDO!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
