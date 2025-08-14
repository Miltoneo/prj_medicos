"""
Views para Descrição de Movimentação Financeira
Arquivo correto: views_descricao_movimentacao.py
"""
# =========================
# Imports
# =========================
# Python Standard
from datetime import datetime

from medicos.models.base import Empresa

# Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db import transaction

# Third Party
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

# Local
from .models.financeiro import DescricaoMovimentacaoFinanceira
from .forms import DescricaoMovimentacaoFinanceiraForm
from .tables import DescricaoMovimentacaoFinanceiraTable
from .filters import DescricaoMovimentacaoFinanceiraFilter

# =========================
# Helpers
# =========================
def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    """
    Helper para contexto global das views financeiras.
    """
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'Financeiro'
    request.session['cenario_nome'] = cenario_nome or 'Financeiro'
    request.session['user_id'] = request.user.id if hasattr(request, 'user') else None
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Financeiro',
        'user': getattr(request, 'user', None),
    }
    return context

##############################
# Views
##############################

class DescricaoMovimentacaoFinanceiraListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = DescricaoMovimentacaoFinanceira
    table_class = DescricaoMovimentacaoFinanceiraTable
    template_name = 'financeiro/lista_descricoes_movimentacao.html'
    filterset_class = DescricaoMovimentacaoFinanceiraFilter
    context_object_name = 'descricoes'
    paginate_by = 20

    def get_queryset(self):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            return DescricaoMovimentacaoFinanceira.objects.none()
        return DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        # Contexto global (sem empresa manual)
        main_context = main(self.request, menu_nome='Financeiro', cenario_nome='Lista de Movimentações')
        context.update(main_context)
        context['titulo_pagina'] = 'Descrições de Movimentação Financeira'
        context['empresa_id'] = empresa_id
        context['table'] = context.get('table')
        context['filter'] = context.get('filter')
        # 'empresa' será fornecida pelo context processor
        return context

class DescricaoMovimentacaoFinanceiraCreateView(LoginRequiredMixin, CreateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'

    def form_valid(self, form):
        from core.context_processors import empresa_context
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            messages.error(self.request, 'Empresa não encontrada no contexto.')
            return self.form_invalid(form)
        form.empresa = empresa
        descricao = form.save(commit=False)
        descricao.created_by = self.request.user
        descricao.save()
        messages.success(self.request, 'Descrição cadastrada com sucesso!')
        return redirect('medicos:lista_descricoes_movimentacao', empresa_id=empresa.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        # Contexto global (sem empresa manual)
        main_context = main(self.request, menu_nome='Financeiro', cenario_nome='Nova Movimentação')
        context.update(main_context)
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Nova Descrição de Movimentação Financeira'
        return context

class DescricaoMovimentacaoFinanceiraUpdateView(LoginRequiredMixin, UpdateView):
    model = DescricaoMovimentacaoFinanceira
    form_class = DescricaoMovimentacaoFinanceiraForm
    template_name = 'financeiro/descricao_movimentacao_form.html'


    def form_valid(self, form):
        from core.context_processors import empresa_context
        descricao = form.save(commit=False)
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            messages.error(self.request, 'Empresa não encontrada no contexto.')
            return self.form_invalid(form)
        descricao.empresa = empresa
        descricao.save()
        messages.success(self.request, 'Descrição atualizada com sucesso!')
        return redirect('medicos:lista_descricoes_movimentacao', empresa_id=empresa.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        # Contexto global (sem empresa manual)
        main_context = main(self.request, menu_nome='Financeiro', cenario_nome='Editar Movimentação')
        context.update(main_context)
        context['empresa_id'] = empresa_id
        context['titulo_pagina'] = 'Editar Descrição de Movimentação Financeira'
        return context

    def get_success_url(self):
        empresa_id = self.object.empresa.id
        return reverse_lazy('medicos:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})

class DescricaoMovimentacaoFinanceiraDeleteView(LoginRequiredMixin, DeleteView):
    model = DescricaoMovimentacaoFinanceira
    template_name = 'financeiro/descricao_movimentacao_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        # Contexto global (sem empresa manual)
        main_context = main(self.request, menu_nome='Financeiro', cenario_nome='Excluir Movimentação')
        context.update(main_context)
        context['empresa_id'] = empresa_id
        return context

    def get_success_url(self):
        empresa_id = self.object.empresa.id
        return reverse_lazy('medicos:lista_descricoes_movimentacao', kwargs={'empresa_id': empresa_id})


@login_required
def importar_descricoes_movimentacao(request, empresa_id):
    """
    View para importar descrições de movimentação de outra empresa para a empresa atual.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        # Empresa de destino (atual)
        empresa_destino = get_object_or_404(Empresa, id=empresa_id)
        
        # Empresa de origem
        empresa_origem_id = request.POST.get('empresa_origem_id')
        if not empresa_origem_id:
            return JsonResponse({'success': False, 'error': 'Empresa de origem não informada'})
        
        empresa_origem = get_object_or_404(Empresa, id=empresa_origem_id)
        
        # Verificar se as empresas são diferentes
        if empresa_origem.id == empresa_destino.id:
            return JsonResponse({'success': False, 'error': 'Não é possível importar da mesma empresa'})
        
        # Buscar descrições de movimentação da empresa origem
        descricoes_origem = DescricaoMovimentacaoFinanceira.objects.filter(empresa=empresa_origem)
        
        if not descricoes_origem.exists():
            return JsonResponse({'success': False, 'error': 'Nenhuma descrição de movimentação encontrada na empresa de origem'})
        
        # Importar descrições em transação
        with transaction.atomic():
            contador_criadas = 0
            contador_duplicadas = 0
            
            for descricao_origem in descricoes_origem:
                # Verificar se já existe descrição com o mesmo código na empresa destino
                existe_duplicata = DescricaoMovimentacaoFinanceira.objects.filter(
                    empresa=empresa_destino,
                    codigo_contabil=descricao_origem.codigo_contabil
                ).exists()
                
                if existe_duplicata:
                    contador_duplicadas += 1
                    continue
                
                # Criar nova descrição na empresa destino
                DescricaoMovimentacaoFinanceira.objects.create(
                    empresa=empresa_destino,
                    descricao=descricao_origem.descricao,
                    codigo_contabil=descricao_origem.codigo_contabil
                )
                contador_criadas += 1
        
        # Preparar mensagem de sucesso
        if contador_criadas > 0:
            mensagem = f'{contador_criadas} descrição(ões) de movimentação importada(s) com sucesso'
            if contador_duplicadas > 0:
                mensagem += f' ({contador_duplicadas} duplicada(s) ignorada(s))'
        else:
            if contador_duplicadas > 0:
                mensagem = f'Todas as {contador_duplicadas} descrição(ões) já existem na empresa de destino'
            else:
                mensagem = 'Nenhuma descrição foi importada'
        
        return JsonResponse({
            'success': True,
            'message': mensagem,
            'criadas': contador_criadas,
            'duplicadas': contador_duplicadas
        })
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Empresa não encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})
