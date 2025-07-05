#!/usr/bin/env python
"""
Teste do banco de dados após as migrações
"""
import os
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

print("=== TESTANDO ACESSO AOS MODELOS SaaS ===\n")

try:
    from medicos.models import Conta, ContaMembership, Licenca, Pessoa
    
    # Testar se podemos acessar as tabelas
    print(f"✅ Contas disponíveis: {Conta.objects.count()}")
    print(f"✅ Memberships disponíveis: {ContaMembership.objects.count()}")
    print(f"✅ Licenças disponíveis: {Licenca.objects.count()}")
    print(f"✅ Pessoas disponíveis: {Pessoa.objects.count()}")
    
    print("\n=== TESTANDO MIDDLEWARE ===")
    
    from medicos.middleware.tenant_middleware import TenantMiddleware, get_current_account
    middleware = TenantMiddleware()
    print("✅ Middleware importado com sucesso")
    
    print("\n=== TESTANDO VIEWS ===")
    
    from medicos.views_auth import tenant_login, select_account
    from medicos.views_dashboard import dashboard_home
    print("✅ Views importadas com sucesso")
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")
    print("\n🚀 Aplicação pronta para uso!")
    print("Acesse: http://127.0.0.1:8000/medicos/auth/login/")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
