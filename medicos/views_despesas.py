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
        from .tables_despesas import DespesaSocioTable
        from medicos.models.base import Socio
        from .models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
        competencia = request.GET.get('competencia') or request.session.get('mes_ano')
        socio_id = request.GET.get('socio')
        # Sócios ativos para o filtro
        socios = Socio.objects.filter(empresa_id=empresa_id, ativo=True).values_list('id', 'pessoa__name').order_by('pessoa__name')

        despesas = []
        total_despesas = 0
        if socio_id:
            # Despesas individuais do sócio
            despesas_individuais = DespesaSocio.objects.filter(
                socio_id=socio_id,
                socio__empresa_id=empresa_id
            )
            if competencia:
                try:
                    ano, mes = competencia.split('-')
                    despesas_individuais = despesas_individuais.filter(data__year=ano, data__month=mes)
                except Exception:
                    pass
            despesas_individuais = despesas_individuais.select_related('socio', 'item_despesa', 'item_despesa__grupo_despesa')

            # Despesas rateadas do sócio
            despesas_rateadas = []
            if competencia:
                try:
                    ano, mes = competencia.split('-')
                    data_ref = f"{ano}-{mes}-01"
                except Exception:
                    data_ref = None
            else:
                data_ref = None
            if data_ref:
                # Buscar todas as despesas rateadas da empresa no mês
                rateadas_qs = DespesaRateada.objects.filter(
                    item_despesa__grupo_despesa__empresa_id=empresa_id,
                    data__year=ano, data__month=mes
                ).select_related('item_despesa', 'item_despesa__grupo_despesa')
                for despesa in rateadas_qs:
                    # Para cada despesa rateada, buscar configuração de rateio do sócio
                    rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                        despesa.item_despesa, Socio.objects.get(id=socio_id), despesa.data
                    )
                    if rateio and rateio.percentual_rateio:
                        valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
                        # Cria objeto fake para exibir na tabela
                        class FakeGrupoDespesa:
                            def __init__(self, descricao):
                                self.descricao = descricao
                            def __repr__(self):
                                return f"FakeGrupoDespesa(descricao={self.descricao!r})"

                        class FakeItemDespesa:
                            def __init__(self, descricao, grupo_despesa):
                                self.descricao = descricao
                                self.grupo_despesa = grupo_despesa
                            def __repr__(self):
                                return f"FakeItemDespesa(descricao={self.descricao!r}, grupo_despesa={self.grupo_despesa!r})"

                        class FakeDespesa:
                            def __init__(self, socio, item_despesa, valor_total, taxa_rateio, valor_apropriado):
                                self.socio = socio
                                self.item_despesa = item_despesa
                                self.valor_total = valor_total
                                self.taxa_rateio = taxa_rateio
                                self.valor_apropriado = valor_apropriado
                                self.id = None  # Não permite editar/excluir
                            def __repr__(self):
                                return f"FakeDespesa(socio={self.socio!r}, item_despesa={self.item_despesa!r}, valor_total={self.valor_total!r}, taxa_rateio={self.taxa_rateio!r}, valor_apropriado={self.valor_apropriado!r})"

                        socio_obj = Socio.objects.get(id=socio_id)
                        item_desc = getattr(despesa.item_despesa, 'descricao', None) or '-'
                        grupo_obj = getattr(despesa.item_despesa, 'grupo_despesa', None)
                        grupo_desc = getattr(grupo_obj, 'descricao', None) or '-'
                        fake_item = FakeItemDespesa(item_desc, FakeGrupoDespesa(grupo_desc))
                        fake = FakeDespesa(
                            socio=socio_obj,
                            item_despesa=fake_item,
                            valor_total=despesa.valor,
                            taxa_rateio=rateio.percentual_rateio,
                            valor_apropriado=valor_apropriado
                        )
                        despesas_rateadas.append(fake)
            # Junta despesas individuais e rateadas
            despesas = list(despesas_individuais)
            # Converter objetos fake para dicionários padronizados
            despesas_rateadas_dicts = []
            for fake in despesas_rateadas:
                despesas_rateadas_dicts.append({
                    'socio': fake.socio,
                    'descricao': getattr(fake.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(fake.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'valor_total': fake.valor_total,
                    'taxa_rateio': fake.taxa_rateio,
                    'valor_apropriado': fake.valor_apropriado,
                    'id': None,
                })
            # Para objetos reais, também padronizar para dicionário
            despesas_dicts = []
            for d in despesas:
                despesas_dicts.append({
                    'socio': d.socio,
                    'descricao': getattr(d.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(d.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'valor_total': getattr(d, 'valor', 0),
                    'taxa_rateio': '-',
                    'valor_apropriado': getattr(d, 'valor', 0),
                    'id': d.id,
                })
            despesas = despesas_dicts + despesas_rateadas_dicts
            # Garante que a lista passada para a Table é uma lista de dicionários
            if not all(isinstance(d, dict) for d in despesas):
                despesas = [d if isinstance(d, dict) else d.__dict__ for d in despesas]
            total_despesas = sum([d.get('valor_apropriado', 0) or 0 for d in despesas])
        else:
            # Se não filtrar por sócio, mostra todas as despesas individuais
            despesas_qs = DespesaSocio.objects.filter(
                socio__empresa_id=empresa_id
            )
            if competencia:
                try:
                    ano, mes = competencia.split('-')
                    despesas_qs = despesas_qs.filter(data__year=ano, data__month=mes)
                except Exception:
                    pass
            despesas_qs = despesas_qs.select_related('socio', 'item_despesa', 'item_despesa__grupo_despesa')
            despesas = []
            for d in despesas_qs:
                despesas.append({
                    'socio': d.socio,
                    'descricao': getattr(d.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(d.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'valor_total': getattr(d, 'valor', 0),
                    'taxa_rateio': '-',
                    'valor_apropriado': getattr(d, 'valor', 0),
                    'id': d.id,
                })
            total_despesas = sum([d.get('valor_apropriado', 0) or 0 for d in despesas])

        table = DespesaSocioTable(despesas)
        import django_tables2 as tables
        tables.RequestConfig(request, paginate={'per_page': 20}).configure(table)
        context = {
            'titulo_pagina': 'Despesas Apropriadas dos Sócios',
            'socios': socios,
            'competencia': competencia,
            'socio_id': socio_id,
            'total_despesas': total_despesas,
            'table': table,
        }
        return render(request, 'despesas/despesas_socio_lista.html', context)
