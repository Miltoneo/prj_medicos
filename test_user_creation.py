#!/usr/bin/env python
"""
Script de teste direto para criar usuários - sem middlewares
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

# Desabilitar middlewares problemáticos temporariamente
os.environ['DISABLE_TENANT_MIDDLEWARE'] = '1'

django.setup()

from medicos.models import CustomUser

def main():
    print("=== TESTE DIRETO DE CRIAÇÃO DE USUÁRIOS ===")
    
    try:
        # Verificar conexão
        print("1. Testando conexão com banco...")
        count = CustomUser.objects.count()
        print(f"   ✓ Conexão OK - {count} usuários existentes")
        
        # Listar usuários existentes
        print("\n2. Usuários existentes:")
        users = CustomUser.objects.all()
        for user in users:
            print(f"   - {user.username} ({user.email})")
        
        # Tentar criar um usuário de teste
        print("\n3. Criando usuário de teste...")
        email = 'admin@clinicasp.com'
        
        if CustomUser.objects.filter(email=email).exists():
            print(f"   ⚠️  Usuário {email} já existe, atualizando...")
            user = CustomUser.objects.get(email=email)
            user.set_password('123456')
            user.save()
            print(f"   ✓ Senha do usuário {email} atualizada")
        else:
            user = CustomUser.objects.create_user(
                username='admin',
                email=email,
                password='123456',
                first_name='Admin',
                last_name='Sistema'
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f"   ✓ Usuário {email} criado com sucesso")
        
        print("\n=== TESTE CONCLUÍDO ===")
        print("Credenciais:")
        print("Email: admin@clinicasp.com")
        print("Senha: 123456")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
