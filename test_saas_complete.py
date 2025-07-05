#!/usr/bin/env python
"""
Script para testar se as tabelas SaaS foram criadas corretamente
"""
import os
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

def test_saas_models():
    """Testa se os modelos SaaS estão funcionando"""
    print("=== TESTANDO MODELOS SAAS ===\n")
    
    try:
        from medicos.models import Conta, ContaMembership, Licenca
        print("✅ Modelos importados com sucesso")
        
        # Testar criação de uma conta
        conta, created = Conta.objects.get_or_create(
            name="Teste SaaS",
            defaults={'cnpj': '12345678000199'}
        )
        print(f"✅ Conta criada/encontrada: {conta.name} (ID: {conta.id})")
        
        # Testar criação de licença
        from datetime import date, timedelta
        licenca, created = Licenca.objects.get_or_create(
            conta=conta,
            defaults={
                'plano': 'Básico',
                'data_inicio': date.today(),
                'data_fim': date.today() + timedelta(days=365),
                'ativa': True,
                'limite_usuarios': 5
            }
        )
        print(f"✅ Licença criada/encontrada: {licenca.plano} - Válida: {licenca.is_valida()}")
        
        # Testar se há usuários para criar membership
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        usuarios = User.objects.all()[:1]
        if usuarios:
            user = usuarios[0]
            membership, created = ContaMembership.objects.get_or_create(
                user=user,
                conta=conta,
                defaults={'role': 'admin'}
            )
            print(f"✅ Membership criado/encontrado: {user.email} -> {conta.name} ({membership.role})")
        else:
            print("⚠️  Nenhum usuário encontrado para criar membership")
        
        print(f"\n📊 Total de contas: {Conta.objects.count()}")
        print(f"📊 Total de licenças: {Licenca.objects.count()}")
        print(f"📊 Total de memberships: {ContaMembership.objects.count()}")
        
        print("\n🎉 MODELOS SAAS FUNCIONANDO CORRETAMENTE!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar modelos SaaS: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_middleware():
    """Testa se o middleware pode ser importado"""
    print("\n=== TESTANDO MIDDLEWARE ===\n")
    
    try:
        from medicos.middleware.tenant_middleware import TenantMiddleware, get_current_account
        print("✅ Middleware importado com sucesso")
        
        middleware = TenantMiddleware()
        print("✅ Middleware instanciado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no middleware: {e}")
        return False

if __name__ == '__main__':
    print("🚀 INICIANDO TESTES DO SISTEMA SAAS\n")
    
    models_ok = test_saas_models()
    middleware_ok = test_middleware()
    
    if models_ok and middleware_ok:
        print("\n✅ SISTEMA SAAS CONFIGURADO CORRETAMENTE!")
        print("\n🌐 Você pode acessar:")
        print("   - Login: http://127.0.0.1:8000/medicos/auth/login/")
        print("   - Dashboard: http://127.0.0.1:8000/medicos/dashboard/")
    else:
        print("\n❌ PROBLEMAS ENCONTRADOS NO SISTEMA SAAS")
