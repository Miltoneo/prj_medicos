from medicos.models import CustomUser

# Garante que o usuário admin@admin.com está ativo, é staff e superuser
def run():
    email = 'admin@admin.com'
    try:
        user = CustomUser.objects.get(email=email)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f'Usuário {email} atualizado com sucesso!')
    except CustomUser.DoesNotExist:
        print(f'Usuário {email} não encontrado.')

if __name__ == '__main__':
    run()
