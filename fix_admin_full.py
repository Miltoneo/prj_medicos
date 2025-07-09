from medicos.models import CustomUser, Conta, ContaMembership

def main():
    email = 'admin@admin.com'
    try:
        user = CustomUser.objects.get(email=email)
        print(f'Usuário encontrado: {email}')
    except CustomUser.DoesNotExist:
        print(f'Usuário {email} não encontrado.')
        return
    conta = Conta.objects.first()
    if not conta:
        conta = Conta.objects.create(name='Conta Admin')
        print('Conta "Conta Admin" criada.')
    else:
        print(f'Conta encontrada: {conta.name}')
    if not ContaMembership.objects.filter(conta=conta, user=user).exists():
        ContaMembership.objects.create(conta=conta, user=user, role='admin', is_active=True)
        print(f'Usuário {email} vinculado à conta {conta.name} como admin.')
    else:
        print(f'Usuário {email} já está vinculado à conta {conta.name}.')
    # Garante permissões
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print('Permissões do usuário admin garantidas.')

main()
