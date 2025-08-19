from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.generic import CreateView, UpdateView, DeleteView
from django_tables2.views import SingleTableView
from django.shortcuts import get_object_or_404
from medicos.models.financeiro import MeioPagamento, Conta
from medicos.models.base import Empresa
from .forms_meio_pagamento import MeioPagamentoForm

from medicos.tables_meio_pagamento import MeioPagamentoTable

class MeioPagamentoListView(SingleTableView):
    model = MeioPagamento
    table_class = MeioPagamentoTable
    template_name = 'cadastro/lista_meios_pagamento.html'
    paginate_by = 10

    def get_queryset(self):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        self.empresa_id = empresa.id if empresa else None
        qs = MeioPagamento.objects.filter(empresa=empresa) if empresa else MeioPagamento.objects.none()
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(nome__icontains=nome)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        context['empresa_id'] = empresa.id if empresa else None
        context['titulo_pagina'] = 'Meios de Pagamento'
        return context

class MeioPagamentoCreateView(CreateView):
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/criar_meio_pagamento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        context['empresa_id'] = empresa.id if empresa else None
        context['titulo_pagina'] = 'Novo Meio de Pagamento'
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            form.instance.empresa = empresa
        return form

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        empresa = self.object.empresa
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        return reverse_lazy('medicos:empresas')

class MeioPagamentoUpdateView(UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        context['empresa_id'] = empresa.id if empresa else None
        context['titulo_pagina'] = 'Editar Meio de Pagamento'
        return context
    
    def get_object(self, queryset=None):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        obj = get_object_or_404(MeioPagamento, pk=self.kwargs['pk'], empresa=empresa)
        return obj
    
    model = MeioPagamento
    form_class = MeioPagamentoForm
    template_name = 'cadastro/editar_meio_pagamento.html'

    def get_success_url(self):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        else:
            return reverse_lazy('medicos:empresas')

class MeioPagamentoDeleteView(DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        context['empresa_id'] = empresa.id if empresa else None
        context['titulo_pagina'] = 'Excluir Meio de Pagamento'
        return context
    
    def get_object(self, queryset=None):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        obj = get_object_or_404(MeioPagamento, pk=self.kwargs['pk'], empresa=empresa)
        return obj
    
    model = MeioPagamento
    template_name = 'cadastro/excluir_meio_pagamento.html'

    def get_success_url(self):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            return reverse_lazy('medicos:lista_meios_pagamento', kwargs={'empresa_id': empresa.pk})
        else:
            return reverse_lazy('medicos:empresas')  # Redireciona para lista geral de empresas

@login_required
@require_http_methods(["POST"])
def importar_meios_pagamento(request, empresa_id):
    """
    Importa todos os meios de pagamento de uma empresa origem para a empresa destino
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
                'error': 'Não é possível importar meios de pagamento da mesma empresa'
            })
        
        # Buscar meios de pagamento da empresa origem
        meios_pagamento_origem = MeioPagamento.objects.filter(empresa=empresa_origem)
        
        if not meios_pagamento_origem.exists():
            return JsonResponse({
                'success': False,
                'error': f'Nenhum meio de pagamento encontrado na empresa {empresa_origem.nome_fantasia or empresa_origem.name}'
            })
        
        # Executar importação dentro de uma transação
        with transaction.atomic():
            meios_importados = 0
            meios_ignorados = 0
            
            for meio_origem in meios_pagamento_origem:
                # Verificar se já existe um meio com o mesmo código na empresa destino
                meio_existente = MeioPagamento.objects.filter(
                    empresa=empresa_destino,
                    codigo=meio_origem.codigo
                ).exists()
                
                if meio_existente:
                    meios_ignorados += 1
                    continue
                
                # Criar novo meio de pagamento para a empresa destino
                novo_meio = MeioPagamento(
                    empresa=empresa_destino,
                    codigo=meio_origem.codigo,
                    nome=meio_origem.nome,
                    ativo=meio_origem.ativo,
                    created_by=request.user
                )
                novo_meio.save()
                meios_importados += 1
        
        mensagem = f'Importação concluída! {meios_importados} meio(s) de pagamento importado(s) de {empresa_origem.nome_fantasia or empresa_origem.name}.'
        if meios_ignorados > 0:
            mensagem += f' {meios_ignorados} meio(s) ignorado(s) por já existirem códigos iguais.'
        
        return JsonResponse({
            'success': True,
            'message': mensagem
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno durante a importação: {str(e)}'
        })
