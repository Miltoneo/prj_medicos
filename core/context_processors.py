from django.conf import settings
from medicos.models import Conta, Empresa
from medicos.middleware.tenant_middleware import get_current_account

def app_version(request):
    return {"APP_VERSION": settings.APP_VERSION}

def empresa_context(request):
    """
    Injeta empresas_cadastradas, empresa e conta_atual no contexto global.
    - empresas_cadastradas: todas as empresas da conta ativa
    - empresa: empresa selecionada (por sessão ou primeira da lista)
    - conta_atual: conta ativa (tenant)
    """
    conta_atual = get_current_account()
    empresas_cadastradas = []
    empresa = None
    
    if conta_atual:
        empresas_cadastradas = Empresa.objects.filter(conta=conta_atual, ativo=True).order_by('nome_fantasia','name')
        empresa_id = request.session.get('empresa_atual_id')
        if empresa_id:
            try:
                empresa = empresas_cadastradas.get(id=empresa_id)
            except Empresa.DoesNotExist:
                empresa = empresas_cadastradas.first() if empresas_cadastradas else None
        else:
            empresa = empresas_cadastradas.first() if empresas_cadastradas else None
    return {
        'empresas_cadastradas': empresas_cadastradas,
        'empresa': empresa,
        'conta_atual': conta_atual,
    }
