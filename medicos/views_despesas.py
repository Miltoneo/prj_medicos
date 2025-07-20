
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages
from .models.despesas import DespesaRateada
from .filters_despesas import DespesaEmpresaFilter
from .tables_despesas import DespesaEmpresaTable
import django_tables2 as tables

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
        competencia = request.GET.get('competencia') or request.session.get('mes_ano')
        despesas_qs = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa_id=empresa_id
        )
        if competencia:
            # Espera formato yyyy-mm
            try:
                ano, mes = competencia.split('-')
                despesas_qs = despesas_qs.filter(data__year=ano, data__month=mes)
            except Exception:
                pass
        filtro = DespesaEmpresaFilter(request.GET, queryset=despesas_qs)
        despesas = filtro.qs
        total_despesas = sum([d.valor for d in despesas])
        table = DespesaEmpresaTable(despesas)
        tables.RequestConfig(request, paginate={'per_page': 20}).configure(table)
        context = {
            'titulo_pagina': 'Despesas da Empresa',
            'filtro': filtro,
            'table': table,
            'competencia': competencia,
            'total_despesas': total_despesas,
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
