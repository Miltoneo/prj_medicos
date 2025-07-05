#!/usr/bin/env python
"""
Script para testar URLs do dashboard
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.urls import reverse
from django.test import RequestFactory

def test_urls():
    print("=== TESTANDO URLs DO DASHBOARD ===")
    
    try:
        # Testar se o namespace dashboard existe
        print("\n1. Testando URLs com namespace...")
        
        urls_to_test = [
            ('medicos:dashboard:home', 'Dashboard Home'),
            ('medicos:dashboard:widgets', 'Dashboard Widgets'),
            ('medicos:dashboard:relatorio_executivo', 'Relatório Executivo'),
        ]
        
        for url_name, description in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"   ✓ {description}: {url}")
            except Exception as e:
                print(f"   ❌ {description}: {e}")
        
        # Testar URLs diretas
        print("\n2. Testando URLs diretas...")
        direct_urls = [
            ('medicos:home', 'Home direta'),
            ('medicos:auth:login_tenant', 'Login Tenant'),
            ('medicos:auth:logout', 'Logout'),
        ]
        
        for url_name, description in direct_urls:
            try:
                url = reverse(url_name)
                print(f"   ✓ {description}: {url}")
            except Exception as e:
                print(f"   ❌ {description}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_urls()
