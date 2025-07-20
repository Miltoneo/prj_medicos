# Editar despesa da empresa
from django.views.generic import UpdateView, DeleteView
from .models.despesas import DespesaRateada
from .forms_despesas import DespesaEmpresaForm

class EditarDespesaEmpresaView(UpdateView):
    model = DespesaRateada
    form_class = DespesaEmpresaForm
    template_name = 'despesas/form_empresa_edit.html'

    def get_success_url(self):
        empresa_id = self.object.item_despesa.grupo_despesa.empresa_id
        return reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Despesa da Empresa'
        return context

class ExcluirDespesaEmpresaView(DeleteView):
    model = DespesaRateada
    template_name = 'despesas/confirm_delete_empresa.html'

    def get_success_url(self):
        empresa_id = self.object.item_despesa.grupo_despesa.empresa_id
        return reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Excluir Despesa da Empresa'
        return context

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages
import django_tables2 as tables
from .models.despesas import DespesaRateada
from .filters_despesas import DespesaEmpresaFilter
from .tables_despesas import DespesaEmpresaTable
from .forms_despesas import DespesaEmpresaForm

# Cadastro de nova despesa da empresa
class NovaDespesaEmpresaView(View):
    def get(self, request, empresa_id):
        form = DespesaEmpresaForm()
        return render(request, 'despesas/form_empresa.html', {
            'form': form,
            'titulo_pagina': 'Nova Despesa da Empresa',
        })

    def post(self, request, empresa_id):
        form = DespesaEmpresaForm(request.POST)
        if form.is_valid():
            despesa = form.save(commit=False)
            # associar empresa via item_despesa.grupo_despesa.empresa
            despesa.save()
            messages.success(request, 'Despesa cadastrada com sucesso!')
            return redirect('medicos:lista_despesas_empresa', empresa_id=empresa_id)
        return render(request, 'despesas/form_empresa.html', {
            'form': form,
            'titulo_pagina': 'Nova Despesa da Empresa',
        })

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
