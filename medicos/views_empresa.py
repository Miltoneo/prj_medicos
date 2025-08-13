from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from medicos.models.base import Socio, Empresa, ContaMembership
from .tables_socio_lista import SocioListaTable, SocioListaDashboardTable
from .filters_socio import SocioFilter
from django_tables2 import RequestConfig
from datetime import datetime
import logging
# Third Party
from django_tables2.views import SingleTableView
# Local
from .models.base import Conta
from .tables import EmpresaTable
from .forms import EmpresaForm
from .filters import EmpresaFilter
# Logger
logger = logging.getLogger(__name__)
from core.context_processors import empresa_context

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
def main(request, empresa_id=None):
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano') or datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano

    empresa_id = empresa_id or request.GET.get('empresa_id') or request.session.get('empresa_id')
    if not empresa_id:
        raise Exception('empresa_id não definido na sessão ou na requisição.')
    # Não busque manualmente a empresa aqui, use apenas o context processor nos templates/views
    request.session['empresa_id'] = int(empresa_id)

    # O context processor já injeta 'empresa' e 'empresas_cadastradas' no contexto global
    # Se precisar de empresa para lógica, use empresa_context(request).get('empresa')
    socios_qs = Socio.objects.none()
    socio_filter = None
    table = None
    if empresa_id:
        empresa = empresa_context(request).get('empresa')
        if empresa:
            socios_qs = Socio.objects.filter(empresa=empresa)
            socio_filter = SocioFilter(request.GET, queryset=socios_qs)
            table = SocioListaDashboardTable(socio_filter.qs)
            RequestConfig(request, paginate={'per_page': 20}).configure(table)
    return {
        'user': request.user,
        'table': table,
        'socio_filter': socio_filter,
        'mes_ano': mes_ano,
        'menu_nome': 'dashboard',
        'titulo_pagina': 'Dashboard',
        'cenario_nome': 'Empresa',
    }

# Nova view para renderizar o dashboard
@login_required
def dashboard_empresa(request, empresa_id=None):
    context = main(request, empresa_id=empresa_id)
    return render(request, 'empresa/dashboard.html', context)


class EmpresaListView(LoginRequiredMixin, SingleTableView):
    model = Empresa
    table_class = EmpresaTable
    template_name = 'empresa/empresa_list.html'
    context_object_name = 'empresas'

    def get_queryset(self):
        conta_id = get_or_set_conta_id(self.request)
        qs = Empresa.objects.none()
        if conta_id:
            qs = Empresa.objects.filter(conta_id=conta_id).order_by('name')
        self.filter = EmpresaFilter(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_filter'] = self.filter
        context['titulo_pagina'] = 'Empresas da Conta'
        return context


@login_required
def empresa_create(request):
    membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
    conta_id = membership.conta_id if membership else None
    if not conta_id:
        messages.error(request, 'Conta não encontrada para este usuário.')
        return redirect('medicos:empresa_create')
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.conta_id = conta_id
            empresa.ativo = False  # Inativa até validação
            empresa.save()
            logger.info(f'Empresa cadastrada: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
            messages.success(request, 'Empresa cadastrada com sucesso! Aguarde validação.')
            return redirect('medicos:empresa_create')
    else:
        form = EmpresaForm()
    contexto = {
        'form': form,
        'titulo_pagina': 'Nova Empresa',
        'menu_nome': 'empresas',
    }
    return render(request, 'empresa/empresa_create.html', contexto)


@login_required
def empresa_detail(request, empresa_id):
    contexto = main(request, empresa_id=empresa_id)
    # contexto['empresa'] já está correto
    if 'cenario_nome' in contexto:
        del contexto['cenario_nome']
    return render(request, 'empresa/empresa_detail.html', contexto)


@login_required
def empresa_update(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    contexto = main(request, empresa_id=empresa_id)
    contexto['empresa'] = empresa
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            logger.info(f'Empresa atualizada: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('medicos:empresa_update', empresa_id=empresa.id)
    else:
        form = EmpresaForm(instance=empresa)
    contexto['form'] = form
    if 'cenario_nome' in contexto:
        del contexto['cenario_nome']
    return render(request, 'empresa/empresa_update.html', contexto)


@login_required
def empresa_delete(request, empresa_id):
    contexto = main(request, empresa_id=empresa_id)
    empresa = contexto['empresa']
    if request.method == 'POST':
        logger.info(f'Empresa excluída: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
        empresa.delete()
        messages.success(request, 'Empresa excluída com sucesso!')
        return redirect('medicos:empresa_delete', empresa_id=empresa.id)
    contexto['empresa'] = empresa
    if 'cenario_nome' in contexto:
        del contexto['cenario_nome']
    return render(request, 'empresa/empresa_delete.html', contexto)
