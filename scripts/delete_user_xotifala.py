
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()


from django.contrib.auth import get_user_model
from medicos.models.base import Conta, ContaMembership

User = get_user_model()

email = 'xotifala@gmail.com'
user = User.objects.filter(email=email).first()

if user:
    print(f'Apagando usuário: {user.email} (id={user.id})')
    # Apaga memberships
    memberships = ContaMembership.objects.filter(user=user)
    for m in memberships:
        print(f' - Apagando membership: {m}')
        m.delete()
    # Apaga contas associadas ao usuário (admin ou criadas por ele)
    contas = Conta.objects.filter(created_by=user)
    for c in contas:
        print(f' - Apagando conta: {c.name} (id={c.id})')
        c.delete()
    user.delete()
    print('Usuário e dados associados apagados com sucesso.')
else:
    print('Usuário não encontrado.')
