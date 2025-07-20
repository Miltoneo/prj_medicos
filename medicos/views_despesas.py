from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages

# Supondo que existam os models DespesaEmpresa, DespesaSocio
# from .models import DespesaEmpresa, DespesaSocio

# Consolidado de Despesas
class ConsolidadoDespesasView(View):
    def get(self, request, empresa_id):
        # Exemplo de contexto consolidado
        context = {
            'titulo_pagina': 'Consolidado de Despesas',
        }
        return render(request, 'despesas/lista_consolidado.html', context)

# Lista de Despesas da Empresa
class ListaDespesasEmpresaView(View):
    def get(self, request, empresa_id):
        # despesas = DespesaEmpresa.objects.filter(empresa_id=empresa_id, competencia=request.session['mes_ano'])
        context = {
            'titulo_pagina': 'Despesas da Empresa',
            # 'despesas': despesas,
        }
        return render(request, 'despesas/lista_empresa.html', context)

# Lista de Despesas de Sócio
class ListaDespesasSocioView(View):
    def get(self, request, empresa_id):
        # despesas = DespesaSocio.objects.filter(empresa_id=empresa_id, competencia=request.session['mes_ano'])
        context = {
            'titulo_pagina': 'Despesas de Sócio',
            # 'despesas': despesas,
        }
        return render(request, 'despesas/lista_socio.html', context)
