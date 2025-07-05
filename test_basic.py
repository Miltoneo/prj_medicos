#!/usr/bin/env python
"""
Teste simples para verificar as configurações básicas do Django
"""
import os
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import django
    django.setup()
    print("✅ Django configurado com sucesso")
    
    # Testar importações básicas
    from medicos.models import Conta, Pessoa, ContaMembership, Licenca
    print("✅ Modelos importados com sucesso")
    
    # Testar middleware
    from medicos.middleware.tenant_middleware import TenantMiddleware
    print("✅ Middleware importado com sucesso")
    
    # Testar views
    from medicos import views_auth, views_dashboard
    print("✅ Views importadas com sucesso")
    
    print("\n🎉 Configuração básica está funcionando!")
    
except Exception as e:
    print(f"❌ Erro na configuração: {e}")
    import traceback
    traceback.print_exc()
