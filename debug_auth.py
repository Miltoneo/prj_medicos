#!/usr/bin/env python
"""
Script para diagnosticar problemas de autenticação
"""
import os
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth import get_user_model, authenticate
from medicos.models import Conta, ContaMembership, Licenca

User = get_user_model()

def check_users():
    """Verifica todos os usuários no sistema"""
    print("👥 USUÁRIOS NO BANCO DE DADOS:")
    users = User.objects.all()
    
    if not users:
        print("  ❌ Nenhum usuário encontrado!")
        return False
    
    for user in users:
        print(f"\n  📧 Email: {user.email}")
        print(f"     Username: {user.username}")
        print(f"     Ativo: {user.is_active}")
        print(f"     Staff: {user.is_staff}")
        print(f"     Superuser: {user.is_superuser}")
        
        # Verificar se tem senha
        if user.password:
            print(f"     Senha hash: {user.password[:20]}...")
        else:
            print("     ❌ SEM SENHA!")
        
        # Verificar memberships
        memberships = ContaMembership.objects.filter(user=user)
        if memberships:
            print("     Contas:")
            for membership in memberships:
                print(f"       - {membership.conta.name} ({membership.role})")
        else:
            print("     ❌ Sem acesso a contas")
    
    return True

def test_authentication():
    """Testa autenticação com credenciais específicas"""
    print("\n🔐 TESTANDO AUTENTICAÇÃO:")
    
    test_credentials = [
        ('admin@clinicasp.com', '123456'),
        ('drsilva@email.com', '123456'),
        ('admin', 'admin123'),
    ]
    
    for email, password in test_credentials:
        print(f"\n  Testando: {email} / {password}")
        
        # Tentar autenticar por email
        user = authenticate(username=email, password=password)
        if user:
            print(f"    ✅ SUCESSO! Usuário: {user.email}")
        else:
            print(f"    ❌ FALHOU!")
            
            # Verificar se o usuário existe
            try:
                user_obj = User.objects.get(email=email)
                print(f"    ℹ️  Usuário existe: {user_obj.email}")
                print(f"    ℹ️  Ativo: {user_obj.is_active}")
                
                # Tentar por username também
                user_by_username = authenticate(username=user_obj.username, password=password)
                if user_by_username:
                    print(f"    ✅ SUCESSO por username: {user_obj.username}")
                else:
                    print(f"    ❌ Falhou também por username: {user_obj.username}")
                    
            except User.DoesNotExist:
                print(f"    ❌ Usuário não existe: {email}")

def check_accounts():
    """Verifica contas e licenças"""
    print("\n🏢 CONTAS E LICENÇAS:")
    
    contas = Conta.objects.all()
    if not contas:
        print("  ❌ Nenhuma conta encontrada!")
        return
    
    for conta in contas:
        print(f"\n  🏢 {conta.name}")
        print(f"     ID: {conta.id}")
        
        # Verificar licença
        try:
            licenca = conta.licenca
            print(f"     📋 Licença: {licenca.plano}")
            print(f"     📅 Válida: {licenca.is_valida()}")
            print(f"     👥 Limite usuários: {licenca.limite_usuarios}")
        except:
            print("     ❌ SEM LICENÇA!")
        
        # Verificar memberships
        memberships = ContaMembership.objects.filter(conta=conta)
        print(f"     👥 Membros: {memberships.count()}")
        for membership in memberships:
            print(f"       - {membership.user.email} ({membership.role})")

def fix_users():
    """Tenta corrigir usuários com problemas"""
    print("\n🔧 CORRIGINDO USUÁRIOS:")
    
    # Criar/corrigir usuário principal
    user, created = User.objects.get_or_create(
        email='admin@clinicasp.com',
        defaults={
            'username': 'admin_clinica',
            'first_name': 'Admin',
            'last_name': 'Clínica',
            'is_active': True
        }
    )
    
    # Sempre definir senha
    user.set_password('123456')
    user.save()
    
    print(f"✅ Usuário configurado: {user.email}")
    print(f"   Username: {user.username}")
    print(f"   Ativo: {user.is_active}")
    
    # Verificar se tem conta
    conta, created = Conta.objects.get_or_create(
        name="Clínica São Paulo",
        defaults={'cnpj': '12345678000199'}
    )
    
    # Criar licença se não existir
    licenca, created = Licenca.objects.get_or_create(
        conta=conta,
        defaults={
            'plano': 'Premium',
            'data_inicio': '2025-01-01',
            'data_fim': '2025-12-31',
            'ativa': True,
            'limite_usuarios': 10
        }
    )
    
    # Criar membership se não existir
    membership, created = ContaMembership.objects.get_or_create(
        user=user,
        conta=conta,
        defaults={'role': 'admin'}
    )
    
    print(f"✅ Membership configurado: {user.email} -> {conta.name}")
    
    # Testar autenticação
    auth_user = authenticate(username=user.email, password='123456')
    if auth_user:
        print("✅ AUTENTICAÇÃO FUNCIONANDO!")
    else:
        print("❌ Autenticação ainda não funciona")
        
        # Tentar por username
        auth_user = authenticate(username=user.username, password='123456')
        if auth_user:
            print("✅ AUTENTICAÇÃO POR USERNAME FUNCIONANDO!")
        else:
            print("❌ Autenticação não funciona nem por username")

def main():
    print("🔍 DIAGNÓSTICO DE AUTENTICAÇÃO\n")
    
    check_users()
    test_authentication()
    check_accounts()
    
    print("\n🔧 TENTANDO CORRIGIR...")
    fix_users()
    
    print("\n" + "="*50)
    print("📋 CREDENCIAIS CORRETAS:")
    print("Email: admin@clinicasp.com")
    print("Senha: 123456")
    print("="*50)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
