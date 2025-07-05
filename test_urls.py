#!/usr/bin/env python
"""
Script de teste para verificar as URLs do projeto Django SaaS
"""
import os
import sys
import django

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.urls import reverse, NoReverseMatch

def test_urls():
    """Testa as principais URLs do projeto"""
    
    print("=== TESTE DE URLs DO PROJETO ===\n")
    
    # Lista de URLs para testar
    urls_to_test = [
        # URLs de autenticação
        ('auth:login_tenant', 'Login Tenant'),
        ('auth:logout', 'Logout'),
        ('auth:select_account', 'Seleção de Conta'),
        ('auth:license_expired', 'Licença Expirada'),
        
        # URLs de dashboard
        ('dashboard:home', 'Dashboard Home'),
        ('dashboard:relatorio_executivo', 'Relatório Executivo'),
        
        # URLs principais
        ('medicos:index_old', 'Index Antigo'),
    ]
    
    for url_name, description in urls_to_test:
        try:
            url_path = reverse(url_name)
            print(f"✅ {description:20} -> {url_name:25} -> {url_path}")
        except NoReverseMatch as e:
            print(f"❌ {description:20} -> {url_name:25} -> ERRO: {e}")
        except Exception as e:
            print(f"❌ {description:20} -> {url_name:25} -> ERRO: {e}")
    
    print("\n=== TESTE DE MIDDLEWARE ===\n")
    
    # Testar importação dos middlewares
    try:
        from medicos.middleware.tenant_middleware import TenantMiddleware, LicenseValidationMiddleware, UserLimitMiddleware
        print("✅ Middlewares importados com sucesso")
        
        # Testar instanciação
        tenant_mw = TenantMiddleware()
        license_mw = LicenseValidationMiddleware()
        user_limit_mw = UserLimitMiddleware()
        
        print("✅ Middlewares instanciados com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao importar middlewares: {e}")
    
    print("\n=== TESTE DE MODELOS ===\n")
    
    # Testar importação dos modelos
    try:
        from medicos.models import Conta, ContaMembership, Licenca, Pessoa
        print("✅ Modelos principais importados com sucesso")
        
        # Verificar se as tabelas existem
        print(f"✅ Total de Contas: {Conta.objects.count()}")
        print(f"✅ Total de Pessoas: {Pessoa.objects.count()}")
        print(f"✅ Total de Licenças: {Licenca.objects.count()}")
        print(f"✅ Total de Memberships: {ContaMembership.objects.count()}")
        
    except Exception as e:
        print(f"❌ Erro ao acessar modelos: {e}")

if __name__ == '__main__':
    test_urls()
