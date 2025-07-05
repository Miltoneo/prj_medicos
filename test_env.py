#!/usr/bin/env python
"""
Teste para verificar variáveis de ambiente
"""
import os
from pathlib import Path
import environ

# Configurar o ambiente Django
BASE_DIR = Path(__file__).resolve().parent

print("=== TESTE DE VARIÁVEIS DE AMBIENTE ===")

print(f"1. BASE_DIR: {BASE_DIR}")

# Verificar se .env existe
env_file = BASE_DIR / '.env'
print(f"2. Arquivo .env existe: {env_file.exists()}")

if env_file.exists():
    print("3. Conteúdo do .env:")
    with open(env_file, 'r') as f:
        content = f.read()
    print(content)

# Testar leitura com environ
try:
    env = environ.Env()
    environ.Env.read_env(env_file)
    
    print("\n4. Variáveis lidas com environ:")
    vars_to_check = ['DEBUG', 'SERVER_HOSTNAME', 'DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD', 'DATABASE_PORT']
    
    for var in vars_to_check:
        try:
            value = env(var)
            if 'PASSWORD' in var:
                value = '*' * len(value) if value else 'VAZIO'
            print(f"   {var}: {value}")
        except Exception as e:
            print(f"   {var}: ERRO - {e}")

except Exception as e:
    print(f"❌ Erro ao ler .env: {e}")

print("\n=== FIM DO TESTE ===")
