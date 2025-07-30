import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Conta, ContaMembership
from django.db import transaction

def cleanup_orphaned_contas():
    """
    Remove todas as contas e memberships que não possuem nenhum usuário vinculado.
    Isso corrige o banco para permitir o registro de novos usuários sem conflitos de integridade.
    """
    with transaction.atomic():
        # Apaga memberships sem usuário vinculado
        orphaned_memberships = ContaMembership.objects.filter(user__isnull=True)
        count_memberships = orphaned_memberships.count()
        if count_memberships:
            print(f'Removendo {count_memberships} ContaMembership(s) sem usuário...')
            orphaned_memberships.delete()

        # Apaga contas sem nenhum membership vinculado
        orphaned_contas = Conta.objects.filter(memberships__isnull=True)
        count_contas = orphaned_contas.count()
        if count_contas:
            print(f'Removendo {count_contas} Conta(s) sem nenhum usuário vinculado...')
            orphaned_contas.delete()

        print('Limpeza concluída. Contas e memberships órfãos removidos.')

if __name__ == '__main__':
    cleanup_orphaned_contas()
