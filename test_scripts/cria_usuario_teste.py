from medicos.models import CustomUser, Conta, ContaMembership, Licenca
from django.utils import timezone

# Crie um usuário comum
test_user, created = CustomUser.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'testuser@example.com',
        'is_active': True,
        'is_staff': False,
        'is_superuser': False,
        'first_name': 'Test',
        'last_name': 'User',
    }
)
if created:
    test_user.set_password('testpassword123')
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

print('Usuário testuser criado e vinculado à Conta Teste com senha: testpassword123')
