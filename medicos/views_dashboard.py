from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from medicos.models.base import Empresa, ContaMembership
from medicos.filters import EmpresaFilter

class DashboardEmpresaListView(LoginRequiredMixin, ListView):
    model = Empresa
    template_name = 'dashboard/empresa_list.html'
    context_object_name = 'empresas'

    def get_queryset(self):
        memberships = ContaMembership.objects.filter(user=self.request.user, is_active=True)
        contas_ids = memberships.values_list('conta_id', flat=True)
        qs = Empresa.objects.filter(conta_id__in=contas_ids)
        self.filter = EmpresaFilter(self.request.GET, queryset=qs)
        queryset = self.filter.qs
        ordering = self.request.GET.get('ordering')
        if ordering in ['name', '-name', 'cnpj', '-cnpj', 'regime_tributario', '-regime_tributario']:
            queryset = queryset.order_by(ordering)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_filter'] = self.filter
        context['empresa_id_atual'] = self.request.session.get('empresa_id')
        return context

@login_required
def dashboard(request):
    # Recupera empresas disponíveis para o usuário autenticado
    memberships = ContaMembership.objects.filter(user=request.user, is_active=True)
    contas_ids = memberships.values_list('conta_id', flat=True)
    empresas_qs = Empresa.objects.filter(conta_id__in=contas_ids)
    empresa_filter = EmpresaFilter(request.GET, queryset=empresas_qs)
    empresas_disponiveis = empresa_filter.qs
    empresa_id_atual = request.session.get('empresa_id')
    empresa_atual = None
    if empresa_id_atual:
        empresa_atual = empresas_disponiveis.filter(id=empresa_id_atual).first()
    if not empresa_atual:
        empresa_atual = empresas_disponiveis.first()
        if empresa_atual:
            request.session['empresa_id'] = empresa_atual.id
    return render(request, 'dashboard/home.html', {
        'empresas_disponiveis': empresas_disponiveis,
        'empresa_atual': empresa_atual,
        'empresa_filter': empresa_filter,
        'user': request.user,
    })
