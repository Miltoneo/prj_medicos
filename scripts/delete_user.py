import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.contrib.auth import get_user_model
from medicos.models.base import Conta, ContaMembership, Empresa, Socio, Pessoa
from medicos.models.financeiro import Financeiro, AplicacaoFinanceira, MeioPagamento, DescricaoMovimentacaoFinanceira
from medicos.models.fiscal import NotaFiscal
from medicos.models.despesas import GrupoDespesa, ItemDespesa, ItemDespesaRateioMensal
from django.db import transaction

User = get_user_model()

email = 'miltoneo@gmail.com'
user = User.objects.filter(email=email).first()

if user:
    print(f'Apagando usuário: {user.email} (id={user.id})')
    with transaction.atomic():
        # ATENÇÃO: Por compliance e continuidade do negócio, NÃO remover empresas, sócios, licenças, registros financeiros, despesas ou notas fiscais.
        # Apenas remove o usuário, memberships e perfil Pessoa diretamente vinculados.
        memberships = ContaMembership.objects.filter(user=user)
        for m in memberships:
            print(f' - Apagando membership: {m}')
            m.delete()
        # Apaga Pessoa vinculada ao usuário (perfil pessoal, não empresas/sócios)
        if hasattr(user, 'pessoa_profile'):
            pessoa = user.pessoa_profile
            print(f' - Apagando perfil Pessoa: {pessoa}')
            pessoa.delete()
        # Apaga memberships restantes (caso algum vínculo extra)
        ContaMembership.objects.filter(user=user).delete()
        # Apaga usuário
        user.delete()
    print('Usuário e vínculos pessoais apagados com sucesso. Dados financeiros, empresariais e fiscais foram preservados conforme compliance.')
else:
    print('Usuário não encontrado.')
