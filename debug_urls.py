#!/usr/bin/env python
"""
Script para testar especificamente o problema de URL resolution
"""
import os
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import django
    django.setup()
    
    from django.urls import reverse, NoReverseMatch
    from django.conf import settings
    
    print("=== TESTANDO URLs ESPECÍFICAS ===\n")
    
    # Teste 1: URLs diretas
    direct_urls = [
        '/medicos/auth/login/',
        '/medicos/auth/logout/',
        '/medicos/auth/select-account/',
        '/medicos/dashboard/',
        '/admin/',
    ]
    
    print("URLs diretas (sem reverse):")
    for url in direct_urls:
        print(f"  ✅ {url}")
    
    # Teste 2: URLs com namespace
    named_urls = [
        ('medicos:auth:login_tenant', 'Login Tenant'),
        ('medicos:auth:logout', 'Logout'),
        ('medicos:auth:select_account', 'Select Account'),
        ('medicos:dashboard:home', 'Dashboard Home'),
    ]
    
    print("\nURLs nomeadas (com reverse):")
    for url_name, description in named_urls:
        try:
            url_path = reverse(url_name)
            print(f"  ✅ {description}: {url_name} -> {url_path}")
        except NoReverseMatch as e:
            print(f"  ❌ {description}: {url_name} -> ERRO: {e}")
        except Exception as e:
            print(f"  ❌ {description}: {url_name} -> ERRO: {e}")
    
    # Teste 3: URLs sem namespace completo
    simple_named_urls = [
        ('auth:login_tenant', 'Login Tenant'),
        ('auth:logout', 'Logout'),
        ('dashboard:home', 'Dashboard Home'),
    ]
    
    print("\nURLs com namespace simples:")
    for url_name, description in simple_named_urls:
        try:
            url_path = reverse(url_name)
            print(f"  ✅ {description}: {url_name} -> {url_path}")
        except NoReverseMatch as e:
            print(f"  ❌ {description}: {url_name} -> ERRO: {e}")
        except Exception as e:
            print(f"  ❌ {description}: {url_name} -> ERRO: {e}")
    
    # Teste 4: Listar todas as URLs disponíveis
    from django.urls import get_resolver
    resolver = get_resolver()
    
    print("\n=== TODAS AS URLs DISPONÍVEIS ===")
    
    def print_urls(url_patterns, prefix=''):
        for pattern in url_patterns:
            if hasattr(pattern, 'url_patterns'):
                print_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                if hasattr(pattern, 'name') and pattern.name:
                    print(f"  {prefix}{pattern.pattern} -> {pattern.name}")
    
    print_urls(resolver.url_patterns)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
