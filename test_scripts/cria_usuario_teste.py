import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import CustomUser, Conta, ContaMembership, Licenca
from django.utils import timezone

# Crie um usuário comum
test_user, created = CustomUser.objects.get_or_create(
    username='mileniocontabilidade',
    defaults={
        'email': 'teste@mileniocontabilidade.com',
        'is_active': True,
        'is_staff': True,
        'is_superuser': False,
        'first_name': 'Milênio',
        'last_name': 'Contabilidade',
    }
)
if created:
    test_user.set_password('milenio123')
    test_user.save()

# Crie uma conta, se não existir
conta, _ = Conta.objects.get_or_create(name='Conta Teste')

# Vincule o usuário à conta
ContaMembership.objects.get_or_create(conta=conta, user=test_user, role='admin', is_active=True)

# Crie uma licença para a conta, se não existir
if not hasattr(conta, 'licenca'):
    hoje = timezone.now().date()
    Licenca.objects.create(
        conta=conta,
        plano='Teste',
        data_inicio=hoje,
        data_fim=hoje.replace(year=hoje.year + 10),
        ativa=True,
        limite_usuarios=10,
        created_by=test_user
    )
    print('Licença criada para Conta Teste.')

print('Usuário mileniocontabilidade criado e vinculado à Conta Teste com senha: milenio123')
