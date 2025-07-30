
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from medicos.models.base import Empresa

@login_required
def cenario_faturamento(request):
    """
    Regra de padronização:
    - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']).
    - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
    - Injete também 'titulo_pagina' para exibição do título padrão no header.
    - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
    """
    from core.context_processors import empresa_context
    empresa = empresa_context(request).get('empresa')
    request.session['menu_nome'] = 'Faturamento'
    request.session['cenario_nome'] = 'Faturamento'
    request.session['titulo_pagina'] = 'Notas Fiscais'
    request.session['empresa_nome'] = empresa.name if empresa else ''
    return redirect('medicos:lista_notas_fiscais')

@login_required
def cenario_cadastro(request):
    """
    Regra de padronização:
    - Injete no contexto a variável 'empresa' usando o ID salvo na sessão (request.session['empresa_id']).
    - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
    - Injete também 'titulo_pagina' para exibição do título padrão no header.
    - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto da view e o template base_header.html para garantir consistência visual e semântica.
    """
    from core.context_processors import empresa_context
    empresa = empresa_context(request).get('empresa')
    request.session['cenario_nome'] = 'Cadastro'
    request.session['titulo_pagina'] = 'Cadastro de Sócios'
    request.session['empresa_nome'] = empresa.name if empresa else ''
    return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id if empresa else None)


