#!/usr/bin/env python
"""
Script para verificar e criar usuários de teste
"""
import os
import sys
from datetime import date, timedelta

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth import get_user_model
from medicos.models import Conta, ContaMembership, Licenca

User = get_user_model()

def check_existing_users():
    """Verifica quais usuários existem"""
    print("👥 USUÁRIOS EXISTENTES:")
    users = User.objects.all()
    if users:
        for user in users:
            print(f"  - {user.email} (username: {user.username})")
            # Verificar memberships
            memberships = ContaMembership.objects.filter(user=user)
            for membership in memberships:
                print(f"    → {membership.conta.name} ({membership.role})")
    else:
        print("  ❌ Nenhum usuário encontrado")
    
    return users.count()

def create_superuser():
    """Cria um superusuário para acesso ao admin"""
    print("\n🔑 CRIANDO SUPERUSUÁRIO...")
    
    try:
        superuser, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@admin.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            superuser.set_password('admin123')
            superuser.save()
            print(f"✅ Superusuário criado: {superuser.email}")
            print("   Username: admin")
            print("   Password: admin123")
        else:
            print(f"ℹ️  Superusuário já existe: {superuser.email}")
            
        return superuser
        
    except Exception as e:
        print(f"❌ Erro ao criar superusuário: {e}")
        return None

def create_test_accounts():
    """Cria contas e usuários de teste"""
    print("\n🏢 CRIANDO CONTAS DE TESTE...")
    
    # Conta 1
    conta1, created = Conta.objects.get_or_create(
        name="Clínica São Paulo",
        defaults={'cnpj': '12345678000199'}
    )
    if created:
        print(f"✅ Conta criada: {conta1.name}")
    else:
        print(f"ℹ️  Conta já existe: {conta1.name}")
    
    # Licença para conta 1
    licenca1, created = Licenca.objects.get_or_create(
        conta=conta1,
        defaults={
            'plano': 'Premium',
            'data_inicio': date.today(),
            'data_fim': date.today() + timedelta(days=365),
            'ativa': True,
            'limite_usuarios': 10
        }
    )
    if created:
        print(f"✅ Licença criada: {licenca1.plano}")
    
    # Usuário 1
    user1, created = User.objects.get_or_create(
        email='admin@clinicasp.com',
        defaults={
            'username': 'admin_clinica',
            'first_name': 'Admin',
            'last_name': 'Clínica',
            'is_active': True
        }
    )
    if created:
        user1.set_password('123456')
        user1.save()
        print(f"✅ Usuário criado: {user1.email}")
    else:
        # Atualizar senha caso o usuário já exista
        user1.set_password('123456')
        user1.save()
        print(f"ℹ️  Usuário já existe: {user1.email} (senha atualizada)")
    
    # Membership 1
    membership1, created = ContaMembership.objects.get_or_create(
        user=user1,
        conta=conta1,
        defaults={'role': 'admin'}
    )
    if created:
        print(f"✅ Membership criado: {user1.email} -> {conta1.name}")
    
    # Conta 2
    conta2, created = Conta.objects.get_or_create(
        name="Consultório Dr. Silva",
        defaults={'cnpj': '98765432000188'}
    )
    if created:
        print(f"✅ Conta criada: {conta2.name}")
    
    # Licença para conta 2
    licenca2, created = Licenca.objects.get_or_create(
        conta=conta2,
        defaults={
            'plano': 'Básico',
            'data_inicio': date.today(),
            'data_fim': date.today() + timedelta(days=365),
            'ativa': True,
            'limite_usuarios': 3
        }
    )
    if created:
        print(f"✅ Licença criada: {licenca2.plano}")
    
    # Usuário 2
    user2, created = User.objects.get_or_create(
        email='drsilva@email.com',
        defaults={
            'username': 'dr_silva',
            'first_name': 'Dr.',
            'last_name': 'Silva',
            'is_active': True
        }
    )
    if created:
        user2.set_password('123456')
        user2.save()
        print(f"✅ Usuário criado: {user2.email}")
    else:
        # Atualizar senha caso o usuário já exista
        user2.set_password('123456')
        user2.save()
        print(f"ℹ️  Usuário já existe: {user2.email} (senha atualizada)")
    
    # Membership 2
    membership2, created = ContaMembership.objects.get_or_create(
        user=user2,
        conta=conta2,
        defaults={'role': 'admin'}
    )
    if created:
        print(f"✅ Membership criado: {user2.email} -> {conta2.name}")

def main():
    print("🚀 CONFIGURANDO USUÁRIOS DE TESTE\n")
    
    # Verificar usuários existentes
    user_count = check_existing_users()
    
    # Criar superusuário
    create_superuser()
    
    # Criar contas e usuários de teste
    create_test_accounts()
    
    print("\n" + "="*60)
    print("🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("="*60)
    
    print("\n📋 CREDENCIAIS PARA TESTE:")
    print("\n🔑 ADMIN DO SISTEMA:")
    print("   URL: http://127.0.0.1:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
    
    print("\n🏥 USUÁRIOS SAAS:")
    print("   1. Clínica São Paulo:")
    print("      Email: admin@clinicasp.com")
    print("      Senha: 123456")
    
    print("   2. Consultório Dr. Silva:")
    print("      Email: drsilva@email.com") 
    print("      Senha: 123456")
    
    print("\n🌐 ACESSE: http://127.0.0.1:8000/medicos/auth/login/")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
