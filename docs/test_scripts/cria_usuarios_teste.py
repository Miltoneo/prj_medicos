import os
import django
import sys
from datetime import date, timedelta

# Inicializa o Django para scripts fora do manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.contrib.auth import get_user_model
from medicos.models import Conta, ContaMembership, Licenca

User = get_user_model()

CONTA_TESTE_NOME = 'Conta Teste MultiTenant'

# Cria Conta de teste se não existir
def get_or_create_conta_teste():
    conta, created = Conta.objects.get_or_create(
        name=CONTA_TESTE_NOME,
        defaults={'created_by': None}
    )
    if created:
        print('Conta de teste criada.')
    else:
        print('Conta de teste já existe.')
    return conta

# Cria Licença válida para a conta de teste
def get_or_create_licenca(conta, user):
    if not hasattr(conta, 'licenca'):
        hoje = date.today()
        licenca = Licenca.objects.create(
            conta=conta,
            plano='BASICO',
            data_inicio=hoje - timedelta(days=1),
            data_fim=hoje + timedelta(days=365),
            ativa=True,
            limite_usuarios=10,
            created_by=user
        )
        print('Licença criada para a conta de teste.')
    else:
        print('Licença já existe para a conta de teste.')

# Cria usuários e vincula à conta de teste
def create_users_and_memberships():
    conta = get_or_create_conta_teste()
    users = [
        {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass123', 'role': 'readonly', 'is_staff': False, 'is_superuser': False},
        {'username': 'staffuser', 'email': 'staff@example.com', 'password': 'staffpass123', 'role': 'contabilidade', 'is_staff': True, 'is_superuser': False},
        {'username': 'adminuser', 'email': 'admin@example.com', 'password': 'adminpass123', 'role': 'admin', 'is_staff': True, 'is_superuser': True},
    ]
    for u in users:
        user, created = User.objects.get_or_create(username=u['username'], defaults={
            'email': u['email'],
            'is_staff': u['is_staff'],
            'is_superuser': u['is_superuser']
        })
        if created:
            if u['is_superuser']:
                user.set_password(u['password'])
                user.is_staff = True
                user.is_superuser = True
                user.save()
                print(f"Superusuário {u['username']} criado.")
            else:
                user.set_password(u['password'])
                user.save()
                print(f"Usuário {u['username']} criado.")
        else:
            print(f"Usuário {u['username']} já existe.")
        # Vincula à conta de teste
        membership, m_created = ContaMembership.objects.get_or_create(
            conta=conta, user=user,
            defaults={'role': u['role'], 'created_by': user}
        )
        if m_created:
            print(f"Vínculo criado: {user.username} -> {conta.name} ({u['role']})")
        else:
            print(f"Vínculo já existe: {user.username} -> {conta.name}")
        # Garante licença válida
        if u['role'] == 'admin':
            get_or_create_licenca(conta, user)

if __name__ == '__main__':
    create_users_and_memberships()
