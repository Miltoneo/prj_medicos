#!/usr/bin/env python
"""
Script para verificar vinculações usuário-conta
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import CustomUser, Conta, ContaMembership

def main():
    print("=== VERIFICANDO VINCULAÇÕES USUÁRIO-CONTA ===")
    
    try:
        # Verificar contas
        print("\n1. Contas no sistema:")
        contas = Conta.objects.all()
        for conta in contas:
            print(f"   - {conta.name} (ID: {conta.id})")
        
        # Verificar usuários
        print("\n2. Usuários no sistema:")
        users = CustomUser.objects.all()
        for user in users:
            print(f"   - {user.email} (ID: {user.id})")
        
        # Verificar memberships
        print("\n3. Vinculações (ContaMembership):")
        memberships = ContaMembership.objects.all()
        print(f"   Total de vinculações: {memberships.count()}")
        
        for membership in memberships:
            print(f"   - {membership.user.email} → {membership.conta.name} (role: {membership.role})")
        
        # Testar acesso específico do admin
        print("\n4. Testando acesso do admin@clinicasp.com:")
        try:
            admin_user = CustomUser.objects.get(email='admin@clinicasp.com')
            admin_memberships = ContaMembership.objects.filter(user=admin_user)
            
            print(f"   Usuário admin encontrado: {admin_user.email}")
            print(f"   Contas do admin: {admin_memberships.count()}")
            
            for membership in admin_memberships:
                print(f"     ✓ Acesso à conta: {membership.conta.name} como {membership.role}")
            
            if admin_memberships.count() == 0:
                print("   ❌ Admin não possui acesso a nenhuma conta!")
            else:
                print("   ✅ Admin possui acesso às contas!")
                
        except CustomUser.DoesNotExist:
            print("   ❌ Usuário admin não encontrado!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
