#!/usr/bin/env python
"""
Teste simples de conexão com banco de dados
"""
import os
import sys
import django
from django.conf import settings

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

print("=== TESTE DE CONEXÃO ===")

try:
    from django.db import connection
    
    print("1. Configurações do banco:")
    db_settings = settings.DATABASES['default']
    print(f"   - ENGINE: {db_settings['ENGINE']}")
    print(f"   - HOST: {db_settings['HOST']}")
    print(f"   - PORT: {db_settings['PORT']}")
    print(f"   - NAME: {db_settings['NAME']}")
    print(f"   - USER: {db_settings['USER']}")
    print(f"   - PASSWORD: {'*' * len(db_settings['PASSWORD']) if db_settings['PASSWORD'] else 'VAZIO'}")
    
    print("\n2. Testando conexão...")
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"   ✓ Conexão OK! Resultado: {result}")
    
    print("\n3. Testando banco de dados...")
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    print(f"   ✓ Banco atual: {db_name}")
    
    print("\n4. Listando tabelas...")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"   ✓ Número de tabelas: {len(tables)}")
    
    for table in tables[:10]:  # Mostrar apenas as primeiras 10
        print(f"     - {table[0]}")
    
    if len(tables) > 10:
        print(f"     ... e mais {len(tables) - 10} tabelas")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n=== FIM DO TESTE ===")
