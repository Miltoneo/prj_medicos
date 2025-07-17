
from django.conf import settings
from medicos.models import Conta, Empresa
from medicos.middleware.tenant_middleware import get_current_account

def app_version(request):
    return {"APP_VERSION": settings.APP_VERSION}

def empresa_context(request):
    """
    DIRETRIZ OBRIGATÓRIA: Contexto de Empresa Multi-tenant
    -----------------------------------------------------
    - Sempre utilize a variável 'empresa' injetada por este context processor em views, forms e templates.
    - Nunca busque manualmente a empresa ativa em request.session ou via query nas views.
    - Toda lógica de obtenção, validação e fallback da empresa deve estar centralizada aqui.
    - Se a empresa não estiver disponível, este context processor já trata o erro e exibe mensagem apropriada.
    - Se precisar de outra variável global (ex: conta, tenant), crie um novo context processor.
    - Este padrão é obrigatório para garantir isolamento multi-tenant, consistência e evitar bugs recorrentes.
    """
    """
    Regra de desenvolvimento para contexto de empresa:
    - A variável 'empresa' deve ser sempre injetada no contexto dos templates via context processor (empresa_context), nunca manualmente nas views.
    - A empresa exibida deve ser explicitamente selecionada pelo usuário (armazenada na sessão como 'empresa_id'). Não deve haver fallback automático para a primeira empresa cadastrada.
    - Os templates devem usar apenas {{ empresa }} para exibir informações da empresa, e tratar o caso em que 'empresa' é None (exibindo alerta ou bloqueando navegação).
    - O cabeçalho padrão deve ser incluído via {% include 'layouts/base_header.html' %}.
    - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto global e o template base para garantir consistência visual e semântica.
    """
    empresas_cadastradas = Empresa.objects.all().order_by('nome_fantasia','name')
    empresa = None
    empresa_context_error = None
    empresa_id = request.session.get('empresa_id')
    if empresa_id:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            empresa = None
            empresa_context_error = 'Empresa selecionada não encontrada. Selecione novamente.'
    else:
        empresa = None
        empresa_context_error = 'Nenhuma empresa selecionada. Selecione uma empresa para continuar.'
    return {
        'empresas_cadastradas': empresas_cadastradas,
        'empresa': empresa,
        'empresa_context_error': empresa_context_error,
    }
