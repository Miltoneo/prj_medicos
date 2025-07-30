from medicos.models import CustomUser, Conta, ContaMembership

def run():
    email = 'admin@admin.com'
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        print(f'Usuário {email} não encontrado.')
        return
    conta = Conta.objects.first()
    if not conta:
        conta = Conta.objects.create(name='Conta Admin')
        print('Conta "Conta Admin" criada.')
    # Verifica se já existe associação
    if not ContaMembership.objects.filter(conta=conta, user=user).exists():
        ContaMembership.objects.create(conta=conta, user=user, role='admin', is_active=True)
        print(f'Usuário {email} vinculado à conta {conta.name} como admin.')
    else:
        print(f'Usuário {email} já está vinculado à conta {conta.name}.')

if __name__ == '__main__':
    run()
