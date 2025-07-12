# contexto.py
# Helpers para contexto de views do app medicos

from datetime import datetime
from django.urls import reverse
from django.shortcuts import redirect

# Variáveis de contexto principais
# CONTEXTO_MAIN é o índice da lista de contexto que contém as variáveis principais
CONTEXTO_MAIN = 0

# Variáveis de contexto principais
#contexto = { 'mes_ano': None, 'menu_nome': 'teste', 'cenario_nome': 'Home' }

def set_contexto(request, contexto):
    """
    Prepara variáveis de contexto essenciais para o sistema e redireciona para a lista de sócios da empresa.
    """

    request.session['mes_ano'] = contexto.get('mes_ano') or datetime.now().strftime('%Y-%m')
    request.session['menu_nome'] = contexto.get('menu_nome')
    request.session['cenario_nome'] = contexto.get('cenario_nome')
    request.session['user_id'] = getattr(request.user, 'id', None)


