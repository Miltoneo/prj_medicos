from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
# View para copiar despesas do mês anterior para o mês atual
from .models.despesas import DespesaRateada, DespesaSocio, ItemDespesa
from django.db import transaction

def copiar_despesas_mes_anterior(request, empresa_id):
    """
    Copia todas as despesas do mês anterior para o mês atual para a empresa informada.
    O contexto temporal é obtido de request.session['mes_ano'] (formato MM/YYYY).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuário não autenticado.'}, status=403)

    # Prioriza parametro competencia (POST ou GET), depois session['mes_ano']
    mes_ano = request.POST.get('competencia') or request.GET.get('competencia') or request.session.get('mes_ano')
    if not mes_ano:
        return JsonResponse({'success': False, 'message': 'Contexto temporal não definido.'}, status=400)
    # Aceita tanto MM/YYYY quanto YYYY-MM
    formatos = ['%m/%Y', '%Y-%m']
    ano = mes = None
    for fmt in formatos:
        try:
            dt = datetime.strptime(mes_ano, fmt)
            ano, mes = dt.year, dt.month
            break
        except Exception:
            continue
    if ano is None or mes is None:
        return JsonResponse({'success': False, 'message': f'Formato de mês/ano inválido: {mes_ano}. Use MM/YYYY ou YYYY-MM.'}, status=400)

    destino_primeiro_dia = datetime(ano, mes, 1)
    if mes == 1:
        origem_ano, origem_mes = ano - 1, 12
    else:
        origem_ano, origem_mes = ano, mes - 1
    print(f"[COPIA DESPESAS] Origem: {origem_mes:02d}/{origem_ano}, Destino: {mes:02d}/{ano}")

    with transaction.atomic():
        # Apaga todas as despesas do mês de competência (destino)
        DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa_id=empresa_id,
            data=destino_primeiro_dia
        ).delete()
        DespesaSocio.objects.filter(
            item_despesa__grupo_despesa__empresa_id=empresa_id,
            data=destino_primeiro_dia
        ).delete()

        # Copia todas as despesas do mês anterior (origem) para o mês de competência (destino)
        despesas_rateadas = DespesaRateada.objects.filter(
            item_despesa__grupo_despesa__empresa_id=empresa_id,
            data__year=origem_ano,
            data__month=origem_mes
        )
        despesas_socios = DespesaSocio.objects.filter(
            item_despesa__grupo_despesa__empresa_id=empresa_id,
            data__year=origem_ano,
            data__month=origem_mes
        )
        print(f"[COPIA DESPESAS] Rateadas encontradas: {despesas_rateadas.count()} | Socios encontradas: {despesas_socios.count()}")
        total_copiadas = 0
        for despesa in despesas_rateadas:
            DespesaRateada.objects.create(
                item_despesa=despesa.item_despesa,
                data=destino_primeiro_dia,
                valor=despesa.valor,
                possui_rateio=despesa.possui_rateio,
                created_by=request.user
            )
        total_copiadas += despesas_rateadas.count()
        for despesa in despesas_socios:
            DespesaSocio.objects.create(
                item_despesa=despesa.item_despesa,
                socio=despesa.socio,
                data=destino_primeiro_dia,
                valor=despesa.valor,
                possui_rateio=despesa.possui_rateio,
                created_by=request.user
            )
        total_copiadas += despesas_socios.count()
        print(f"[COPIA DESPESAS] Total copiadas: {total_copiadas}")

    return JsonResponse({'success': True, 'copiadas': total_copiadas, 'message': f'{total_copiadas} despesas copiadas para o mês atual.'})
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa_id'] = self.kwargs.get('empresa_id')
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        socio_id = self.request.GET.get('socio')
        if socio_id:
            initial['socio_id'] = socio_id
        return initial

    def form_valid(self, form):
        from medicos.models.base import Socio
        
        socio_id = self.request.GET.get('socio')
        if not socio_id:
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest('Sócio não informado')
        
        socio = Socio.objects.get(id=socio_id)
        form.instance.socio = socio
        
        # Salvar apenas a despesa, sem criar lançamento financeiro
        return super().form_valid(form)

    def get_success_url(self):
        empresa_id = self.kwargs.get('empresa_id')
        # Tenta obter da querystring, senão do POST
        socio = self.request.GET.get('socio') or self.request.POST.get('socio') or ''
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})
        params = []
        if socio:
            params.append(f'socio={socio}')
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nova Despesa de Sócio'
        empresa_id = self.kwargs.get('empresa_id')
        # Tenta obter da querystring, senão do POST
        socio = self.request.GET.get('socio') or self.request.POST.get('socio') or ''
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})
        params = []
        if socio:
            params.append(f'socio={socio}')
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        context['cancel_url'] = url
        return context

class DespesaSocioUpdateView(UpdateView):
    model = DespesaSocio
    form_class = DespesaSocioForm
    template_name = 'despesas/despesas_socio_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa_id'] = self.kwargs.get('empresa_id')
        return kwargs

    def get_success_url(self):
        empresa_id = self.kwargs.get('empresa_id')
        socio = self.request.GET.get('socio') or self.request.POST.get('socio') or ''
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})
        params = []
        if socio:
            params.append(f'socio={socio}')
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Despesa de Sócio'
        empresa_id = self.kwargs.get('empresa_id')
        socio = self.request.GET.get('socio') or self.request.POST.get('socio') or ''
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})
        params = []
        if socio:
            params.append(f'socio={socio}')
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        context['cancel_url'] = url
        return context

class DespesaSocioDeleteView(DeleteView):
    model = DespesaSocio
    template_name = 'despesas/despesas_socio_confirm_delete.html'

    def get_success_url(self):
        empresa_id = self.kwargs.get('empresa_id')
        socio = self.request.GET.get('socio') or self.request.POST.get('socio') or ''
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})
        params = []
        if socio:
            params.append(f'socio={socio}')
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Excluir Despesa de Sócio'
        empresa_id = self.kwargs.get('empresa_id')
        socio = self.request.GET.get('socio') or self.request.POST.get('socio') or ''
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:despesas_socio_lista', kwargs={'empresa_id': empresa_id})
        params = []
        if socio:
            params.append(f'socio={socio}')
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        context['cancel_url'] = url
        return context


# CRUD Despesa da Empresa
class EditarDespesaEmpresaView(UpdateView):
    model = DespesaRateada
    form_class = DespesaEmpresaForm
    template_name = 'despesas/form_empresa_edit.html'

    def get_success_url(self):
        empresa_id = self.object.item_despesa.grupo_despesa.empresa_id
        # Prioriza GET, depois POST, igual ao fluxo de sócio
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa_id})
        params = []
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Garante que competencia do GET seja propagada para o template
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        self.competencia = competencia
        # Passa empresa_id para o form, garantindo que o widget funcione
        if self.object and self.object.item_despesa and self.object.item_despesa.grupo_despesa:
            kwargs['empresa_id'] = self.object.item_despesa.grupo_despesa.empresa_id
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Despesa da Empresa'
        empresa_id = self.object.item_despesa.grupo_despesa.empresa_id
        competencia = getattr(self, 'competencia', None)
        if competencia is None:
            competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa_id})
        params = []
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        context['cancel_url'] = url
        context['competencia'] = competencia
        return context

class ExcluirDespesaEmpresaView(DeleteView):
    model = DespesaRateada
    template_name = 'despesas/confirm_delete_empresa.html'

    def get_success_url(self):
        empresa_id = self.object.item_despesa.grupo_despesa.empresa_id
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa_id})
        params = []
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Excluir Despesa da Empresa'
        empresa_id = self.object.item_despesa.grupo_despesa.empresa_id
        competencia = self.request.GET.get('competencia') or self.request.POST.get('competencia') or ''
        url = reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa_id})
        params = []
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        context['cancel_url'] = url
        return context


class NovaDespesaEmpresaView(View):
    def get(self, request, empresa_id):
        competencia = request.GET.get('competencia') or ''
        from core.context_processors import empresa_context
        empresa = empresa_context(request)['empresa']
        form = DespesaEmpresaForm(empresa_id=empresa.id)
        url = reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa.id})
        params = []
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        return render(request, 'despesas/form_empresa.html', {
            'form': form,
            'titulo_pagina': 'Nova Despesa da Empresa',
            'cenario_nome': 'Despesas',
            'cancel_url': url,
            'competencia': competencia,
        })

    def post(self, request, empresa_id):
        competencia = request.GET.get('competencia') or request.POST.get('competencia') or ''
        from core.context_processors import empresa_context
        empresa = empresa_context(request)['empresa']
        form = DespesaEmpresaForm(request.POST, empresa_id=empresa.id)
        url = reverse('medicos:lista_despesas_empresa', kwargs={'empresa_id': empresa.id})
        params = []
        if competencia:
            params.append(f'competencia={competencia}')
        if params:
            url += '?' + '&'.join(params)
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.save()
            messages.success(request, 'Despesa cadastrada com sucesso!')
            return redirect(url)
        return render(request, 'despesas/form_empresa.html', {
            'form': form,
            'titulo_pagina': 'Nova Despesa da Empresa',
            'cenario_nome': 'Despesas',
            'cancel_url': url,
            'competencia': competencia,
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
        ).order_by('tipo_classificacao', '-data')  # Ordenação aplicada no queryset
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
        socios = Socio.objects.filter(empresa_id=empresa_id, ativo=True).values_list('id', 'pessoa__name').order_by('pessoa__name')
        socio_id = request.GET.get('socio')
        # Se não houver sócio selecionado, filtra pelo primeiro sócio ativo
        if not socio_id and socios:
            socio_id = str(socios[0][0])
            # Redireciona para a mesma URL já filtrando pelo primeiro sócio
            import urllib.parse
            params = request.GET.copy()
            params['socio'] = socio_id
            url = request.path + '?' + urllib.parse.urlencode(params)
            return redirect(url)

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
                    if rateio is not None:
                        valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
                        # Cria objeto fake para exibir na tabela, mesmo se percentual for 0%
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
                            def __init__(self, socio, item_despesa, valor_total, taxa_rateio, valor_apropriado, data):
                                self.socio = socio
                                self.item_despesa = item_despesa
                                self.valor_total = valor_total
                                self.taxa_rateio = taxa_rateio
                                self.valor_apropriado = valor_apropriado
                                self.data = data
                                self.id = None  # Não permite editar/excluir
                            def __repr__(self):
                                return f"FakeDespesa(socio={self.socio!r}, item_despesa={self.item_despesa!r}, valor_total={self.valor_total!r}, taxa_rateio={self.taxa_rateio!r}, valor_apropriado={self.valor_apropriado!r}, data={self.data!r})"

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
                            valor_apropriado=valor_apropriado,
                            data=despesa.data
                        )
                        # Adicionar campo tipo_classificacao
                        fake.tipo_classificacao = getattr(despesa, 'tipo_classificacao', 1)
                        despesas_rateadas.append(fake)
            # Junta despesas individuais e rateadas, ambos como dicionários padronizados
            despesas = []
            for fake in despesas_rateadas:
                despesas.append({
                    'data': getattr(fake, 'data', None),
                    'socio': fake.socio,
                    'descricao': getattr(fake.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(fake.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'tipo_classificacao': getattr(fake, 'tipo_classificacao', 1),
                    'valor_total': fake.valor_total,
                    'taxa_rateio': fake.taxa_rateio,
                    'valor_apropriado': fake.valor_apropriado,
                    'id': getattr(fake, 'id', None),
                })
            for d in despesas_individuais:
                despesas.append({
                    'data': getattr(d, 'data', None),
                    'socio': d.socio,
                    'descricao': getattr(d.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(d.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'tipo_classificacao': getattr(d, 'tipo_classificacao', 1),
                    'valor_total': getattr(d, 'valor', 0),
                    'taxa_rateio': '-',
                    'valor_apropriado': getattr(d, 'valor', 0),
                    'id': d.id
                })
            total_despesas = sum([d.get('valor_apropriado', 0) or 0 for d in despesas])
            
            # Ordenar lista mista por classificação e data decrescente
            from datetime import date
            despesas.sort(key=lambda x: (
                x.get('tipo_classificacao', 1), 
                -(x.get('data') or date.today()).toordinal()
            ))
        else:
            # Se não filtrar por sócio, mostra todas as despesas individuais
            despesas_qs = DespesaSocio.objects.filter(
                socio__empresa_id=empresa_id
            ).order_by('tipo_classificacao', '-data')  # Ordenação aplicada no queryset
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
                    'data': getattr(d, 'data', None),
                    'socio': d.socio,
                    'descricao': getattr(d.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(d.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'tipo_classificacao': getattr(d, 'tipo_classificacao', 1),
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
