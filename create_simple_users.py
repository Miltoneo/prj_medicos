#!/usr/bin/env python
"""
Script simples para criar usuários de teste
"""
import os
import sys
import django
from django.conf import settings

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import CustomUser
from django.db import transaction

def main():
    print("=== CRIANDO USUÁRIOS DE TESTE SIMPLES ===")
    
    try:
        # Verificar usuários existentes
        print("\n1. Verificando usuários existentes...")
        users = CustomUser.objects.all()
        print(f"   Usuários no sistema: {users.count()}")
        
        for user in users:
            print(f"   - {user.email} ({user.username})")
        
        # Criar usuários de teste
        print("\n2. Criando usuários de teste...")
        
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
        
        for user_data in usuarios_teste:
            email = user_data['email']
            username = user_data['username']
            
            # Verificar se usuário já existe
            if CustomUser.objects.filter(email=email).exists():
                print(f"   ⚠️  Usuário {email} já existe, atualizando senha...")
                user = CustomUser.objects.get(email=email)
                user.set_password(user_data['password'])
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.save()
                print(f"   ✓ Usuário {email} atualizado")
                
            elif CustomUser.objects.filter(username=username).exists():
                print(f"   ⚠️  Username {username} já existe, atualizando...")
                user = CustomUser.objects.get(username=username)
                user.email = email
                user.set_password(user_data['password'])
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.save()
                print(f"   ✓ Usuário {username} atualizado")
                
            else:
                # Criar novo usuário
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.save()
                print(f"   ✓ Usuário {email} criado com sucesso")
        
        print("\n3. Usuários finais no sistema:")
        users = CustomUser.objects.all()
        for user in users:
            tipo = "Admin" if user.is_superuser else "Staff" if user.is_staff else "Usuário"
            print(f"   - {user.email} ({user.username}) - {tipo}")
        
        print("\n=== USUÁRIOS DE TESTE CONFIGURADOS ===")
        print("\n### Credenciais de Teste:")
        print("- Email: admin@clinicasp.com")
        print("- Senha: 123456")
        print("\n- Email: medico1@clinicasp.com")
        print("- Senha: 123456")
        print("\n- Email: medico2@clinicasp.com")
        print("- Senha: 123456")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
