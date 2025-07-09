from django.conf import settings
from medicos.models import Conta, Empresa
from medicos.middleware.tenant_middleware import get_current_account

def app_version(request):
    return {"APP_VERSION": settings.APP_VERSION}

def empresa_context(request):
    """
    Injeta empresas_disponiveis, empresa_atual e conta_atual no contexto global.
    - empresas_disponiveis: todas as empresas da conta ativa
    - empresa_atual: empresa selecionada (por sessão ou primeira da lista)
    - conta_atual: conta ativa (tenant)
    """
    conta_atual = get_current_account()
    empresas_disponiveis = []
    empresa_atual = None
    if conta_atual:
        empresas_disponiveis = Empresa.objects.filter(conta=conta_atual, ativo=True).order_by('nome_fantasia','name')
        empresa_id = request.session.get('empresa_atual_id')
        if empresa_id:
            try:
                empresa_atual = empresas_disponiveis.get(id=empresa_id)
            except Empresa.DoesNotExist:
                empresa_atual = empresas_disponiveis.first() if empresas_disponiveis else None
        else:
            empresa_atual = empresas_disponiveis.first() if empresas_disponiveis else None
    return {
        'empresas_disponiveis': empresas_disponiveis,
        'empresa_atual': empresa_atual,
        'conta_atual': conta_atual,
    }
