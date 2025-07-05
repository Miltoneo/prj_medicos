#!/usr/bin/env python
"""
Script para vincular usuários às contas via ContaMembership
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import CustomUser, Conta, ContaMembership, Licenca
from django.db import transaction
from datetime import datetime, date, timedelta

def main():
    print("=== VINCULANDO USUÁRIOS ÀS CONTAS ===")
    
    try:
        with transaction.atomic():
            # 1. Criar ou verificar conta de teste
            print("\n1. Criando/Verificando conta de teste...")
            conta_teste, created = Conta.objects.get_or_create(
                name="Clínica São Paulo",
                defaults={
                    'cnpj': '12.345.678/0001-90'
                }
            )
            
            if created:
                print(f"   ✓ Conta criada: {conta_teste.name}")
            else:
                print(f"   ✓ Conta existente: {conta_teste.name} (ID: {conta_teste.id})")
            
            # 2. Criar ou verificar licença
            print("\n2. Criando/Verificando licença...")
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
            
            # 3. Verificar usuários existentes
            print("\n3. Verificando usuários...")
            usuarios = [
                ('admin@clinicasp.com', 'admin'),
                ('medico1@clinicasp.com', 'member'),
                ('medico2@clinicasp.com', 'member')
            ]
            
            for email, role in usuarios:
                try:
                    user = CustomUser.objects.get(email=email)
                    print(f"   ✓ Usuário encontrado: {email}")
                    
                    # Verificar se já existe membership
                    membership, created = ContaMembership.objects.get_or_create(
                        conta=conta_teste,
                        user=user,
                        defaults={
                            'role': role,
                            'date_joined': datetime.now()
                        }
                    )
                    
                    if created:
                        print(f"     ✓ ContaMembership criado: {email} como {role}")
                    else:
                        # Atualizar role se necessário
                        if membership.role != role:
                            membership.role = role
                            membership.save()
                            print(f"     ✓ Role atualizado: {email} para {role}")
                        else:
                            print(f"     - ContaMembership já existe: {email} como {role}")
                    
                except CustomUser.DoesNotExist:
                    print(f"   ❌ Usuário não encontrado: {email}")
            
            # 4. Verificar vinculações criadas
            print("\n4. Verificação final...")
            memberships = ContaMembership.objects.filter(conta=conta_teste)
            print(f"   Total de memberships na conta: {memberships.count()}")
            
            for membership in memberships:
                print(f"   - {membership.user.email} ({membership.role}) em {membership.conta.name}")
            
            print("\n=== USUÁRIOS VINCULADOS COM SUCESSO ===")
            print("\n### Credenciais de Teste Atualizadas:")
            print("- Email: admin@clinicasp.com")
            print("- Senha: 123456")
            print("- Role: admin")
            print("")
            print("- Email: medico1@clinicasp.com")
            print("- Senha: 123456")
            print("- Role: member")
            print("")
            print("- Email: medico2@clinicasp.com")
            print("- Senha: 123456")
            print("- Role: member")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Usuários vinculados às contas com sucesso!")
    else:
        print("\n❌ Falha ao vincular usuários")
    sys.exit(0 if success else 1)
