#!/usr/bin/env python
"""
Script para verificar usuários criados
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import CustomUser

def main():
    print("=== VERIFICANDO USUÁRIOS NO SISTEMA ===")
    
    try:
        users = CustomUser.objects.all()
        print(f"\nTotal de usuários: {users.count()}")
        
        print("\nUsuários encontrados:")
        for user in users:
            tipo = "Superuser" if user.is_superuser else "Staff" if user.is_staff else "User"
            print(f"- Email: {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Nome: {user.first_name} {user.last_name}")
            print(f"  Tipo: {tipo}")
            print(f"  Ativo: {user.is_active}")
            print("")
        
        # Testar credenciais específicas
        print("=== TESTANDO CREDENCIAIS ===")
        test_users = [
            ('admin@clinicasp.com', '123456'),
            ('medico1@clinicasp.com', '123456'),
            ('medico2@clinicasp.com', '123456')
        ]
        
        for email, password in test_users:
            try:
                user = CustomUser.objects.get(email=email)
                if user.check_password(password):
                    print(f"✓ {email} - Credenciais OK")
                else:
                    print(f"❌ {email} - Senha incorreta")
            except CustomUser.DoesNotExist:
                print(f"❌ {email} - Usuário não encontrado")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
