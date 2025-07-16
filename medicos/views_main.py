
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.urls import reverse
from medicos.models.base import Empresa, ContaMembership
from medicos.filters import EmpresaFilter
from medicos.contexto import *


@login_required
def main(request):
    memberships = ContaMembership.objects.filter(user=request.user, is_active=True)
    contas_ids = memberships.values_list('conta_id', flat=True)
    empresas_cadastradas = Empresa.objects.filter(conta_id__in=contas_ids)

    request.session['cenario_nome'] = 'Home'
    contexto = {
        'mes_ano': request.GET.get('mes_ano') or request.session.get('mes_ano') or datetime.now().strftime('%Y-%m'),
        'menu_nome': 'Home',
        'titulo_pagina': 'Dashboard Principal',
    }

    return render(request, 'dashboard/home.html', {
        'empresas_cadastradas': empresas_cadastradas,
        'user': request.user,
        **contexto,
    })


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
        empresa = None
        if self.get_queryset().exists():
            empresa = self.get_queryset().first()
        context.update(main(self.request, empresa=empresa, menu_nome='Dashboard', cenario_nome='Dashboard'))
        
        context['empresa_id_atual'] = self.request.session.get('empresa_id')
        return context

