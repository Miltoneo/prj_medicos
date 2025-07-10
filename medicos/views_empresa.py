from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models.base import Conta, Empresa
from .models.base import ContaMembership
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, DetailView, UpdateView, DeleteView, CreateView
from django_tables2.views import SingleTableView
from .tables import EmpresaTable
from django.contrib.admin.views.decorators import staff_member_required
from .forms import EmpresaForm
from django.contrib import messages
from .filters import EmpresaFilter
import logging

logger = logging.getLogger(__name__)

def get_or_set_conta_id(request):
    conta_id = request.session.get('conta_id')
    if not conta_id:
        membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
        if membership:
            conta_id = membership.conta_id
            request.session['conta_id'] = conta_id
    return conta_id

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
        return context

# Substitua a FBV por CBV no urls.py para empresa_list

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
    return render(request, 'empresa/empresa_create.html', {'form': form})

@login_required
def empresa_detail(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    return render(request, 'empresa/empresa_detail.html', {'empresa': empresa})

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
    return render(request, 'empresa/empresa_update.html', {'form': form, 'empresa': empresa})

@login_required
@staff_member_required
def empresa_delete(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        logger.info(f'Empresa excluída: {empresa.name} (CNPJ: {empresa.cnpj}) por {request.user.email}')
        empresa.delete()
        messages.success(request, 'Empresa excluída com sucesso!')
        return redirect('medicos:empresa_list')
    return render(request, 'empresa/empresa_delete.html', {'empresa': empresa})
