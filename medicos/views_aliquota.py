
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas
from django.contrib.auth.decorators import login_required
from medicos.forms import AliquotaForm
from django.contrib import messages
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from .tables import AliquotasTable
from .filters import AliquotasFilter

def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'erro'
    request.session['cenario_nome'] = cenario_nome or 'CADASTRO'
    request.session['user_id'] = request.user.id
    
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome,
        'empresa': empresa,
        'user': request.user,
        'titulo_pagina': 'Aliquotas',
    }
    return context

class ListaAliquotasView(SingleTableMixin, FilterView):
    table_class = AliquotasTable
    model = Aliquotas
    template_name = 'empresa/lista_aliquotas.html'
    filterset_class = AliquotasFilter  
    paginate_by = 20

    def get_queryset(self):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            return Aliquotas.objects.none()
        return Aliquotas.objects.filter(empresa=empresa).order_by('-ativa', '-data_vigencia_inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        context.update(main(self.request, empresa=empresa, menu_nome='Aliquotas'))
        return context

@login_required
def aliquota_edit(request, empresa_id, aliquota_id):
    from core.context_processors import empresa_context
    empresa = empresa_context(request).get('empresa')
    aliquota = None
    form_kwargs = {'empresa': empresa}
    if aliquota_id != 0:
        aliquota = get_object_or_404(Aliquotas, id=aliquota_id, empresa=empresa)
        form_kwargs['instance'] = aliquota
    form = AliquotaForm(request.POST or None, **form_kwargs)
    # Sempre garantir empresa antes da validação
    form.instance.empresa = empresa
    if request.method == 'POST' and form.is_valid():
        aliquota = form.save()
        return redirect('medicos:lista_aliquotas', empresa_id=empresa.id)
    context = main(request, empresa=empresa, menu_nome='Aliquotas', cenario_nome='Aliquota')
    context['form'] = form
    context['aliquota'] = aliquota
    return render(request, 'empresa/aliquota_form.html', context)

@login_required
@require_http_methods(["GET"])
def api_empresas_conta(request):
    """
    API para listar empresas da conta do usuário atual (exceto a empresa ativa)
    """
    try:
        from core.context_processors import empresa_context
        empresa_ativa = empresa_context(request).get('empresa')
        
        if not empresa_ativa:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma empresa ativa selecionada'
            })
        
        # Buscar todas as empresas da mesma conta, exceto a empresa ativa
        empresas = Empresa.objects.filter(
            conta=empresa_ativa.conta
        ).exclude(
            id=empresa_ativa.id
        ).values('id', 'name', 'nome_fantasia').order_by('nome_fantasia', 'name')
        
        empresas_list = []
        for empresa in empresas:
            empresas_list.append({
                'id': empresa['id'],
                'name': empresa['name'],
                'nome_fantasia': empresa['nome_fantasia'] or empresa['name']
            })
        
        return JsonResponse({
            'success': True,
            'empresas': empresas_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def importar_aliquotas(request, empresa_id):
    """
    Importa todas as alíquotas de uma empresa origem para a empresa destino
    """
    try:
        from core.context_processors import empresa_context
        empresa_destino = empresa_context(request).get('empresa')
        
        if not empresa_destino or str(empresa_destino.id) != str(empresa_id):
            return JsonResponse({
                'success': False,
                'error': 'Empresa destino inválida'
            })
        
        empresa_origem_id = request.POST.get('empresa_origem_id')
        if not empresa_origem_id:
            return JsonResponse({
                'success': False,
                'error': 'ID da empresa origem é obrigatório'
            })
        
        # Verificar se a empresa origem pertence à mesma conta
        try:
            empresa_origem = Empresa.objects.get(
                id=empresa_origem_id,
                conta=empresa_destino.conta
            )
        except Empresa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Empresa origem não encontrada ou não pertence à sua conta'
            })
        
        # Verificar se não é a mesma empresa
        if empresa_origem.id == empresa_destino.id:
            return JsonResponse({
                'success': False,
                'error': 'Não é possível importar alíquotas da mesma empresa'
            })
        
        # Buscar alíquotas da empresa origem
        aliquotas_origem = Aliquotas.objects.filter(empresa=empresa_origem)
        
        if not aliquotas_origem.exists():
            return JsonResponse({
                'success': False,
                'error': f'Nenhuma alíquota encontrada na empresa {empresa_origem.nome_fantasia or empresa_origem.name}'
            })
        
        # Executar importação dentro de uma transação
        with transaction.atomic():
            aliquotas_importadas = 0
            
            for aliquota_origem in aliquotas_origem:
                # Criar nova alíquota para a empresa destino
                nova_aliquota = Aliquotas(
                    empresa=empresa_destino,
                    ISS=aliquota_origem.ISS,
                    PIS=aliquota_origem.PIS,
                    COFINS=aliquota_origem.COFINS,
                    IRPJ_ALIQUOTA=aliquota_origem.IRPJ_ALIQUOTA,
                    IRPJ_PRESUNCAO_OUTROS=aliquota_origem.IRPJ_PRESUNCAO_OUTROS,
                    IRPJ_PRESUNCAO_CONSULTA=aliquota_origem.IRPJ_PRESUNCAO_CONSULTA,
                    IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL=aliquota_origem.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL,
                    IRPJ_ADICIONAL=aliquota_origem.IRPJ_ADICIONAL,
                    CSLL_ALIQUOTA=aliquota_origem.CSLL_ALIQUOTA,
                    CSLL_PRESUNCAO_OUTROS=aliquota_origem.CSLL_PRESUNCAO_OUTROS,
                    CSLL_PRESUNCAO_CONSULTA=aliquota_origem.CSLL_PRESUNCAO_CONSULTA,
                    ativa=aliquota_origem.ativa,
                    data_vigencia_inicio=aliquota_origem.data_vigencia_inicio,
                    data_vigencia_fim=aliquota_origem.data_vigencia_fim,
                    created_by=request.user,
                    observacoes=f"Importado de {empresa_origem.nome_fantasia or empresa_origem.name} - {aliquota_origem.observacoes}"
                )
                nova_aliquota.save()
                aliquotas_importadas += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Importação concluída com sucesso! {aliquotas_importadas} alíquota(s) importada(s) de {empresa_origem.nome_fantasia or empresa_origem.name}.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno durante a importação: {str(e)}'
        })
