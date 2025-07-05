#!/usr/bin/env python
"""
Script para testar autenticação diretamente
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
from datetime import date, timedelta

User = get_user_model()

def reset_test_user():
    """Remove e recria o usuário de teste"""
    print("🔄 RESETANDO USUÁRIO DE TESTE...\n")
    
    # Remover usuário se existir
    try:
        old_user = User.objects.get(email='admin@clinicasp.com')
        print(f"🗑️  Removendo usuário existente: {old_user.email}")
        old_user.delete()
    except User.DoesNotExist:
        print("ℹ️  Usuário não existia")
    
    # Criar conta
    conta, created = Conta.objects.get_or_create(
        name="Clínica São Paulo",
        defaults={'cnpj': '12345678000199'}
    )
    print(f"🏢 Conta: {conta.name} (ID: {conta.id})")
    
    # Criar licença
    licenca, created = Licenca.objects.get_or_create(
        conta=conta,
        defaults={
            'plano': 'Premium',
            'data_inicio': date.today(),
            'data_fim': date.today() + timedelta(days=365),
            'ativa': True,
            'limite_usuarios': 10
        }
    )
    print(f"📋 Licença: {licenca.plano} - Válida: {licenca.is_valida()}")
    
    # Criar usuário
    user = User.objects.create_user(
        username='admin_clinica',
        email='admin@clinicasp.com',
        password='123456',
        first_name='Admin',
        last_name='Clínica'
    )
    print(f"👤 Usuário criado: {user.email}")
    print(f"   Username: {user.username}")
    print(f"   ID: {user.id}")
    print(f"   Ativo: {user.is_active}")
    
    # Criar membership
    membership = ContaMembership.objects.create(
        user=user,
        conta=conta,
        role='admin'
    )
    print(f"🔗 Membership criado: {membership.role}")
    
    return user, conta

def test_authentication_methods():
    """Testa diferentes métodos de autenticação"""
    print("\n🔐 TESTANDO AUTENTICAÇÃO...\n")
    
    # Método 1: Por email
    print("1. Autenticação por email:")
    user1 = authenticate(username='admin@clinicasp.com', password='123456')
    if user1:
        print(f"   ✅ SUCESSO! {user1.email}")
    else:
        print("   ❌ FALHOU")
    
    # Método 2: Por username
    print("\n2. Autenticação por username:")
    user2 = authenticate(username='admin_clinica', password='123456')
    if user2:
        print(f"   ✅ SUCESSO! {user2.email}")
    else:
        print("   ❌ FALHOU")
    
    # Método 3: Verificar se usuário existe
    print("\n3. Verificação de usuário:")
    try:
        user_obj = User.objects.get(email='admin@clinicasp.com')
        print(f"   ✅ Usuário existe: {user_obj.email}")
        print(f"   Username: {user_obj.username}")
        print(f"   Ativo: {user_obj.is_active}")
        print(f"   Has Password: {bool(user_obj.password)}")
        
        # Testar senha manualmente
        print(f"\n4. Verificação manual de senha:")
        if user_obj.check_password('123456'):
            print("   ✅ Senha está correta!")
        else:
            print("   ❌ Senha está incorreta!")
            
    except User.DoesNotExist:
        print("   ❌ Usuário não existe")
    
    return user1 or user2

def test_form_validation():
    """Testa a validação do formulário"""
    print("\n📝 TESTANDO FORMULÁRIO...\n")
    
    from medicos.forms import TenantLoginForm
    
    form_data = {
        'email': 'admin@clinicasp.com',
        'password': '123456'
    }
    
    form = TenantLoginForm(data=form_data)
    if form.is_valid():
        print("✅ Formulário é válido!")
        print(f"   Email: {form.cleaned_data['email']}")
    else:
        print("❌ Formulário inválido!")
        print(f"   Erros: {form.errors}")

def main():
    print("🧪 TESTE COMPLETO DE AUTENTICAÇÃO\n")
    print("="*50)
    
    # Resetar usuário
    user, conta = reset_test_user()
    
    # Testar autenticação
    auth_user = test_authentication_methods()
    
    # Testar formulário
    test_form_validation()
    
    print("\n" + "="*50)
    if auth_user:
        print("🎉 AUTENTICAÇÃO FUNCIONANDO!")
        print("\n📋 CREDENCIAIS:")
        print("Email: admin@clinicasp.com")
        print("Senha: 123456")
        print("\n🌐 Teste em: http://127.0.0.1:8000/medicos/auth/login/")
    else:
        print("❌ AUTENTICAÇÃO COM PROBLEMAS!")
    print("="*50)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
