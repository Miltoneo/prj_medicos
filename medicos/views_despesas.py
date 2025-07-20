# Imports padrão Python

# Imports de terceiros
from django.views.generic import View, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
import django_tables2 as tables

# Imports do projeto
from .models.despesas import DespesaSocio, DespesaRateada
from .forms_despesas import DespesaSocioForm, DespesaEmpresaForm
from .filters_despesas import DespesaEmpresaFilter
from .tables_despesas import DespesaEmpresaTable


# CRUD Despesa de Sócio
class DespesaSocioCreateView(CreateView):
    model = DespesaSocio
    form_class = DespesaSocioForm
    template_name = 'despesas/despesas_socio_form.html'

    def get_success_url(self):
        empresa_id = self.kwargs.get('empresa_id')
        return reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nova Despesa de Sócio'
        context['cancel_url'] = self.get_success_url()
        return context

class DespesaSocioUpdateView(UpdateView):
    model = DespesaSocio
    form_class = DespesaSocioForm
    template_name = 'despesas/despesas_socio_form.html'

    def get_success_url(self):
        empresa_id = self.kwargs.get('empresa_id')
        return reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Despesa de Sócio'
        context['cancel_url'] = self.get_success_url()
        return context

class DespesaSocioDeleteView(DeleteView):
    model = DespesaSocio
    template_name = 'despesas/despesas_socio_confirm_delete.html'

    def get_success_url(self):
        empresa_id = self.kwargs.get('empresa_id')
        return reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Excluir Despesa de Sócio'
        context['cancel_url'] = self.get_success_url()
        return context


# CRUD Despesa da Empresa
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


class NovaDespesaEmpresaView(View):
    def get(self, request, empresa_id):
        form = DespesaEmpresaForm()
        return render(request, 'despesas/form_empresa.html', {
            'form': form,
            'titulo_pagina': 'Nova Despesa da Empresa',
            'cenario_nome': 'Despesas',
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
            'cenario_nome': 'Despesas',
        })


class ConsolidadoDespesasView(View):
    def get(self, request, empresa_id):
        context = {
            'titulo_pagina': 'Consolidado de Despesas',
            'cenario_nome': 'Despesas',
        }
        return render(request, 'despesas/lista_consolidado.html', context)


class ListaDespesasEmpresaView(View):
    def get(self, request, empresa_id):
        competencia = request.GET.get('competencia') or request.session.get('mes_ano')
        despesas_qs = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa_id=empresa_id
        )
        if competencia:
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
            'cenario_nome': 'Despesas',
            'filtro': filtro,
            'table': table,
            'competencia': competencia,
            'total_despesas': total_despesas,
        }
        return render(request, 'despesas/lista_empresa.html', context)


class ListaDespesasSocioView(View):
    def get(self, request, empresa_id):
        competencia = request.GET.get('competencia') or request.session.get('mes_ano')
        socio_id = request.GET.get('socio')
        despesas_qs = DespesaSocio.objects.filter(
            socio__empresa_id=empresa_id
        )
        if competencia:
            try:
                ano, mes = competencia.split('-')
                despesas_qs = despesas_qs.filter(data__year=ano, data__month=mes)
            except Exception:
                pass
        if socio_id:
            despesas_qs = despesas_qs.filter(socio_id=socio_id)
        despesas = despesas_qs.select_related('socio', 'item_despesa', 'item_despesa__grupo_despesa')
        total_despesas = sum([d.valor for d in despesas])
        socios = despesas_qs.values_list('socio__id', 'socio__pessoa__name').distinct()
        context = {
            'titulo_pagina': 'Despesas Apropriadas dos Sócios',
            'despesas': despesas,
            'socios': socios,
            'competencia': competencia,
            'socio_id': socio_id,
            'total_despesas': total_despesas,
        }
        return render(request, 'despesas/despesas_socio_lista.html', context)
