#!/usr/bin/env python
"""
Script para criar usuários de teste no sistema
"""
import os
import sys
import django
from django.conf import settings

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import CustomUser, Conta, Licenca, ContaMembership
from django.db import transaction
from datetime import datetime, date, timedelta

def main():
    print("=== CRIANDO USUÁRIOS DE TESTE ===")
    
    try:
        # Verificar usuários existentes
        print("\n1. Verificando usuários existentes...")
        users = CustomUser.objects.all()
        print(f"   Usuários no sistema: {users.count()}")
        
        for user in users:
            print(f"   - {user.email} ({user.username})")
        
        # Criar conta de teste se não existir
        print("\n2. Criando/Verificando conta de teste...")
        conta_teste, created = Conta.objects.get_or_create(
            name="Clínica São Paulo",
            defaults={
                'cnpj': '12.345.678/0001-90'
            }
        )
        
        if created:
            print(f"   ✓ Conta criada: {conta_teste.name}")
        else:
            print(f"   ✓ Conta existente: {conta_teste.name}")
        
        # Criar licença se não existir
        print("3. Criando/Verificando licença...")
        licenca, created = Licenca.objects.get_or_create(
            conta=conta_teste,
            defaults={
                'plano': 'Premium',
                'data_inicio': date.today(),
                'data_fim': date.today() + timedelta(days=365),
                'ativa': True,
                'limite_usuarios': 10
            }
        )
        
        if created:
            print(f"   ✓ Licença criada para: {conta_teste.name}")
        else:
            print(f"   ✓ Licença existente para: {conta_teste.name}")
        
        # Criar usuários de teste
        print("\n4. Criando usuários de teste...")
        
        usuarios_teste = [
            {
                'username': 'admin',
                'email': 'admin@clinicasp.com',
                'password': '123456',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'medico1',
                'email': 'medico1@clinicasp.com',
                'password': '123456',
                'first_name': 'Dr. João',
                'last_name': 'Silva',
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'medico2',
                'email': 'medico2@clinicasp.com',
                'password': '123456',
                'first_name': 'Dra. Maria',
                'last_name': 'Santos',
                'is_staff': False,
                'is_superuser': False
            }
        ]
        
        with transaction.atomic():
            for user_data in usuarios_teste:
                email = user_data['email']
                username = user_data['username']
                
                # Verificar se usuário já existe por email ou username
                existing_user = None
                if CustomUser.objects.filter(email=email).exists():
                    existing_user = CustomUser.objects.get(email=email)
                    print(f"   - Usuário com email {email} já existe")
                elif CustomUser.objects.filter(username=username).exists():
                    existing_user = CustomUser.objects.get(username=username)
                    print(f"   - Usuário com username {username} já existe")
                
                if existing_user:
                    # Atualizar senha do usuário existente
                    existing_user.set_password(user_data['password'])
                    existing_user.save()
                    print(f"   ✓ Senha atualizada para: {existing_user.email}")
                    user = existing_user
                else:
                    # Criar usuário
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=user_data['password'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_staff=user_data['is_staff'],
                        is_superuser=user_data['is_superuser']
                    )
                    print(f"   ✓ Usuário criado: {email}")
                
                # Criar ContaMembership se não for superuser
                if not user.is_superuser:
                    membership, created = ContaMembership.objects.get_or_create(
                        conta=conta_teste,
                        user=user,
                        defaults={
                            'role': 'member'
                        }
                    )
                    
                    if created:
                        print(f"     ✓ ContaMembership criado para: {user.email}")
                    else:
                        print(f"     - ContaMembership já existe para: {user.email}")
        
        print("\n=== USUÁRIOS CRIADOS COM SUCESSO ===")
        print("\n### **Credenciais de Teste:**")
        print("- **Email**: admin@clinicasp.com")
        print("- **Senha**: 123456")
        print("- **Email**: medico1@clinicasp.com")
        print("- **Senha**: 123456")
        print("- **Email**: medico2@clinicasp.com")
        print("- **Senha**: 123456")
        
        # Verificar usuários finais
        print("\n=== VERIFICAÇÃO FINAL ===")
        users = CustomUser.objects.all()
        print(f"Total de usuários: {users.count()}")
        
        for user in users:
            print(f"- {user.email} | {user.first_name} {user.last_name} | Staff: {user.is_staff} | Super: {user.is_superuser}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
