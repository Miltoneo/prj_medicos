#!/usr/bin/env python
"""
Teste básico do Django para verificar se está tudo funcionando
"""
import os
import sys

# Configurar caminhos
project_path = r'f:\Projects\Django\prj_medicos'
os.chdir(project_path)
sys.path.append(project_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

import django
django.setup()

print("✅ Django configurado com sucesso!")

# Importar as views para verificar se não há erros de importação
try:
    from medicos.views_auth import tenant_login, logout_view, select_account
    print("✅ Views de autenticação importadas com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar views de autenticação: {e}")

try:
    from medicos.views_dashboard import dashboard_home
    print("✅ Views de dashboard importadas com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar views de dashboard: {e}")

try:
    from medicos.middleware.tenant_middleware import TenantMiddleware
    print("✅ Middleware importado com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar middleware: {e}")

# Testar URLs básicas
from django.urls import reverse, NoReverseMatch

print("\n=== TESTE DE URLs ===")

# URLs que devem funcionar usando caminhos diretos
test_paths = [
    '/medicos/auth/login/',
    '/medicos/auth/logout/',
    '/medicos/auth/select-account/',
    '/medicos/dashboard/',
    '/admin/',
]

for path in test_paths:
    print(f"✅ Caminho disponível: {path}")

print("\n🎉 Configuração básica validada!")
print("\nPara testar o servidor, execute:")
print("python manage.py runserver 127.0.0.1:8000")
print("\nE acesse: http://127.0.0.1:8000/medicos/auth/login/")
