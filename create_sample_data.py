#!/usr/bin/env python
"""
Script para criar dados de exemplo para testar o SaaS multi-tenant
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
from medicos.models import Conta, ContaMembership, Licenca, Pessoa

User = get_user_model()

def create_sample_data():
    """Cria dados de exemplo para testar a aplicação SaaS"""
    
    print("🚀 Criando dados de exemplo para SaaS Multi-Tenant...\n")
    
    # 1. Criar contas
    print("📊 Criando contas...")
    
    conta1, created = Conta.objects.get_or_create(
        name="Clínica São Paulo",
        defaults={
            'email': 'contato@clinicasp.com',
            'telefone': '(11) 99999-9999'
        }
    )
    if created:
        print(f"✅ Conta criada: {conta1.name}")
    else:
        print(f"ℹ️  Conta já existe: {conta1.name}")
    
    conta2, created = Conta.objects.get_or_create(
        name="Consultório Dr. Silva",
        defaults={
            'email': 'drsilva@email.com',
            'telefone': '(11) 88888-8888'
        }
    )
    if created:
        print(f"✅ Conta criada: {conta2.name}")
    else:
        print(f"ℹ️  Conta já existe: {conta2.name}")
    
    # 2. Criar licenças
    print("\n📋 Criando licenças...")
    
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
        print(f"✅ Licença criada para {conta1.name}: {licenca1.plano}")
    else:
        print(f"ℹ️  Licença já existe para {conta1.name}")
    
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
        print(f"✅ Licença criada para {conta2.name}: {licenca2.plano}")
    else:
        print(f"ℹ️  Licença já existe para {conta2.name}")
    
    # 3. Criar usuários
    print("\n👥 Criando usuários...")
    
    user1, created = User.objects.get_or_create(
        username='admin@clinicasp.com',
        defaults={
            'email': 'admin@clinicasp.com',
            'first_name': 'Admin',
            'last_name': 'Clínica SP',
            'is_staff': False,
            'is_active': True
        }
    )
    if created:
        user1.set_password('123456')
        user1.save()
        print(f"✅ Usuário criado: {user1.username}")
    else:
        print(f"ℹ️  Usuário já existe: {user1.username}")
    
    user2, created = User.objects.get_or_create(
        username='drsilva@email.com',
        defaults={
            'email': 'drsilva@email.com',
            'first_name': 'Dr.',
            'last_name': 'Silva',
            'is_staff': False,
            'is_active': True
        }
    )
    if created:
        user2.set_password('123456')
        user2.save()
        print(f"✅ Usuário criado: {user2.username}")
    else:
        print(f"ℹ️  Usuário já existe: {user2.username}")
    
    # 4. Criar memberships
    print("\n🔗 Criando memberships...")
    
    membership1, created = ContaMembership.objects.get_or_create(
        user=user1,
        conta=conta1,
        defaults={
            'role': 'admin'
        }
    )
    if created:
        print(f"✅ Membership criado: {user1.username} -> {conta1.name} (admin)")
    else:
        print(f"ℹ️  Membership já existe: {user1.username} -> {conta1.name}")
    
    membership2, created = ContaMembership.objects.get_or_create(
        user=user2,
        conta=conta2,
        defaults={
            'role': 'admin'
        }
    )
    if created:
        print(f"✅ Membership criado: {user2.username} -> {conta2.name} (admin)")
    else:
        print(f"ℹ️  Membership já existe: {user2.username} -> {conta2.name}")
    
    # 5. Criar algumas pessoas de exemplo
    print("\n👤 Criando pessoas de exemplo...")
    
    pessoa1, created = Pessoa.objects.get_or_create(
        conta=conta1,
        CPF='123.456.789-01',
        defaults={
            'name': 'João da Silva',
            'profissão': 'Médico',
            'email': 'joao@email.com',
            'phone1': '(11) 77777-7777'
        }
    )
    if created:
        print(f"✅ Pessoa criada: {pessoa1.name} ({conta1.name})")
    else:
        print(f"ℹ️  Pessoa já existe: {pessoa1.name}")
    
    pessoa2, created = Pessoa.objects.get_or_create(
        conta=conta2,
        CPF='987.654.321-09',
        defaults={
            'name': 'Maria Santos',
            'profissão': 'Enfermeira',
            'email': 'maria@email.com',
            'phone1': '(11) 66666-6666'
        }
    )
    if created:
        print(f"✅ Pessoa criada: {pessoa2.name} ({conta2.name})")
    else:
        print(f"ℹ️  Pessoa já existe: {pessoa2.name}")
    
    print("\n" + "="*50)
    print("🎉 DADOS DE EXEMPLO CRIADOS COM SUCESSO!")
    print("="*50)
    print("\n📋 CREDENCIAIS PARA TESTE:")
    print("\n🏥 Clínica São Paulo:")
    print("   Email: admin@clinicasp.com")
    print("   Senha: 123456")
    print("   Plano: Premium (10 usuários)")
    
    print("\n🏥 Consultório Dr. Silva:")
    print("   Email: drsilva@email.com")
    print("   Senha: 123456")
    print("   Plano: Básico (3 usuários)")
    
    print("\n🌐 Acesse: http://127.0.0.1:8000/medicos/auth/login/")

if __name__ == '__main__':
    try:
        create_sample_data()
    except Exception as e:
        print(f"❌ Erro ao criar dados: {e}")
        import traceback
        traceback.print_exc()
