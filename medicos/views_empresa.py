
# Standard Library
from datetime import datetime
import logging

# Django
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Third Party
from django_tables2.views import SingleTableView

# Local
from .models.base import Conta, Empresa, ContaMembership
from .tables import EmpresaTable
from .forms import EmpresaForm
from .filters import EmpresaFilter

# Logger
logger = logging.getLogger(__name__)

# Helper para obter ou definir conta_id na sessão
def get_or_set_conta_id(request):
    conta_id = request.session.get('conta_id')
    if not conta_id:
        membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
        if membership:
            conta_id = membership.conta_id
            request.session['conta_id'] = conta_id
    return conta_id

# Helpers
def main(request):
    # Preparar variáveis de contexto essenciais para o sistema
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano

    # Empresas disponíveis para o usuário
    memberships = ContaMembership.objects.filter(user=request.user, is_active=True)
    contas_ids = memberships.values_list('conta_id', flat=True)
    empresas_disponiveis = Empresa.objects.filter(conta_id__in=contas_ids)

    # Empresa atual
    empresa_id_atual = request.session.get('empresa_id')
    empresa_atual = None
    if empresa_id_atual:
        empresa_atual = empresas_disponiveis.filter(id=empresa_id_atual).first()
    if not empresa_atual:
        empresa_atual = empresas_disponiveis.first()
        if empresa_atual:
            request.session['empresa_id'] = empresa_atual.id

    # Filtro de empresas
    empresa_filter = EmpresaFilter(request.GET, queryset=empresas_disponiveis)

    # Menu e cenário
    request.session['menu_nome'] = 'Dashboard'
    request.session['cenario_nome'] = 'Empresas'

    # Usuário
    request.session['user_id'] = request.user.id

    # Redireciona para a lista de empresas
    return redirect(reverse('medicos:empresa_list'))

# Views
@login_required
def set_empresa(request):
    empresa_id = request.GET.get('empresa_id')
    if empresa_id:
        request.session['empresa_id'] = int(empresa_id)
        # Redireciona diretamente para o dashboard da empresa selecionada
        return redirect('medicos:dashboard_empresa', empresa_id=empresa_id)
    # Redireciona para a página anterior ou dashboard
    next_url = request.META.get('HTTP_REFERER') or reverse('medicos:dashboard')
    return redirect(next_url)


class EmpresaListView(LoginRequiredMixin, SingleTableView):
    model = Empresa
    table_class = EmpresaTable
    template_name = 'empresa/empresa_list.html'
    context_object_name = 'empresas'

    def get_queryset(self):
        conta_id = get_or_set_conta_id(self.request)
        qs = Empresa.objects.none()
        if conta_id:
            qs = Empresa.objects.filter(conta_id=conta_id)
        self.filter = EmpresaFilter(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_filter'] = self.filter
        context.update(main(self.request))
        return context


@staff_member_required
def empresa_create(request):
    membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
    conta_id = membership.conta_id if membership else None
    if not conta_id:
        messages.error(request, 'Conta não encontrada para este usuário.')
        return redirect('medicos:empresa_list')
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.conta_id = conta_id
            empresa.ativo = False  # Inativa até validação
            empresa.save()
            logger.info(f'Empresa cadastrada: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
            messages.success(request, 'Empresa cadastrada com sucesso! Aguarde validação.')
            return redirect('medicos:empresa_list')
    else:
        form = EmpresaForm()
    context = main(request)
    context['form'] = form
    return render(request, 'empresa/empresa_create.html', context)


@login_required
def empresa_detail(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    context = main(request)
    return render(request, 'empresa/empresa_detail.html', context)


@staff_member_required
def empresa_update(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            logger.info(f'Empresa atualizada: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('medicos:empresa_list')
    else:
        form = EmpresaForm(instance=empresa)
    context = main(request)
    context['form'] = form
    return render(request, 'empresa/empresa_update.html', context)


@login_required
@staff_member_required
def empresa_delete(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        logger.info(f'Empresa excluída: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
        empresa.delete()
        messages.success(request, 'Empresa excluída com sucesso!')
        return redirect('medicos:empresa_list')
    context = main(request)
    return render(request, 'empresa/empresa_delete.html', context)
