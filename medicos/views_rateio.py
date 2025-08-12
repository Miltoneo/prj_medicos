
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_tables2 import RequestConfig
from django_filters.views import FilterView
from datetime import date
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from medicos.models.base import Empresa, Socio
from .tables_rateio import NotaFiscalRateioTable
from .forms import NotaFiscalRateioMedicoForm, NotaFiscalRateioMedicoFilter, NotaFiscalRateioFilter

# Mixin para contexto do cenário de faturamento
class RateioContextMixin:
    menu_nome = 'Rateio de Notas'
    cenario_nome = 'Faturamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_nome'] = self.menu_nome
        context['cenario_nome'] = self.cenario_nome
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioListView(RateioContextMixin, FilterView):
    def post(self, request, *args, **kwargs):
        # Use apenas o context processor para obter a empresa
        from core.context_processors import empresa_context
        empresa = empresa_context(request).get('empresa')
        queryset = self.get_queryset()
        nota_id = self.request.GET.get('nota_id')
        nota_fiscal = None
        if nota_id:
            try:
                nota_fiscal = queryset.get(id=nota_id)
            except (NotaFiscal.DoesNotExist, ValueError):
                nota_fiscal = None
        elif queryset.exists():
            nota_fiscal = queryset.first()
        if not nota_fiscal:
            return self.get(request, *args, **kwargs)
        
        # Verificar se a nota fiscal não está cancelada antes de salvar rateio
        if nota_fiscal.status_recebimento == 'cancelado':
            from django.contrib import messages
            messages.error(request, 'Não é possível salvar rateio para nota fiscal cancelada.')
            return self.get(request, *args, **kwargs)
            
        # Get all active medicos for empresa
        medicos_empresa = []
        if empresa:
            medicos_empresa = Socio.objects.filter(empresa=empresa, ativo=True)
        # Save rateio for each medico
        from medicos.models.fiscal import NotaFiscalRateioMedico
        from decimal import Decimal, InvalidOperation
        valores_brutos = []
        for medico in medicos_empresa:
            field_name = f"valor_bruto_medico_{medico.id}"
            valor_bruto = request.POST.get(field_name)
            try:
                valor_bruto = Decimal(valor_bruto) if valor_bruto else Decimal('0')
            except (InvalidOperation, TypeError, ValueError):
                valor_bruto = Decimal('0')
            valores_brutos.append(valor_bruto)
        total_rateio = sum(valores_brutos)
        try:
            val_bruto_nota = Decimal(nota_fiscal.val_bruto)
        except (InvalidOperation, TypeError, ValueError):
            val_bruto_nota = Decimal('0')
        if val_bruto_nota > 0 and total_rateio > val_bruto_nota:
            from django.contrib import messages
            messages.error(request, 'O total do rateio não pode exceder o valor bruto da nota fiscal.')
            return self.get(request, *args, **kwargs)
        # Se não excedeu, salva normalmente
        for idx, medico in enumerate(medicos_empresa):
            valor_bruto = valores_brutos[idx]
            if valor_bruto > 0:
                percentual_participacao = (valor_bruto / val_bruto_nota) * Decimal('100') if val_bruto_nota > 0 else Decimal('0')
                rateio_obj_qs = NotaFiscalRateioMedico.objects.filter(nota_fiscal=nota_fiscal, medico=medico)
                if rateio_obj_qs.exists():
                    rateio_obj = rateio_obj_qs.first()
                    rateio_obj.valor_bruto_medico = valor_bruto
                    rateio_obj.percentual_participacao = percentual_participacao
                    rateio_obj.tipo_rateio = 'valor'
                    rateio_obj.save()
                else:
                    rateio_obj = NotaFiscalRateioMedico(
                        nota_fiscal=nota_fiscal,
                        medico=medico,
                        valor_bruto_medico=valor_bruto,
                        percentual_participacao=percentual_participacao,
                        tipo_rateio='valor'
                    )
                    rateio_obj.save()
            else:
                NotaFiscalRateioMedico.objects.filter(nota_fiscal=nota_fiscal, medico=medico).delete()
        nota_fiscal.rateios_medicos.exclude(medico__in=medicos_empresa).delete()
        
        # Preservar TODOS os filtros originais ao retornar após salvar rateio
        params = []
        for key, value in self.request.GET.items():
            if value and key != 'nota_id':  # Mantém todos os filtros exceto nota_id (será adicionado depois)
                params.append(f'{key}={value}')
        
        # Adiciona a nota_id atual
        params.append(f'nota_id={nota_fiscal.id}')
        
        # Constrói URL com todos os filtros preservados
        url = request.path
        if params:
            url += '?' + '&'.join(params)
        
        return redirect(url)
    model = NotaFiscal
    template_name = 'faturamento/lista_notas_rateio.html'
    context_object_name = 'table'
    filterset_class = NotaFiscalRateioFilter
    table_class = NotaFiscalRateioTable
    paginate_by = 20

    def get_queryset(self):
        # Sempre filtra por empresa da sessão
        empresa_id = self.request.session.get('empresa_id')
        qs = NotaFiscal.objects.all()
        if empresa_id:
            qs = qs.filter(empresa_destinataria_id=empresa_id)
        
        # Filtrar notas com status cancelado - não exibir no rateio
        qs = qs.exclude(status_recebimento='cancelado')
        
        # Aplica o filtro de busca
        filter_params = self.request.GET.copy()
        if 'page' in filter_params:
            filter_params.pop('page')
        if 'nota_id' in filter_params:
            filter_params.pop('nota_id')
            
        # Se não há filtros específicos, aplicar filtro do mês corrente por padrão
        if not filter_params:
            from datetime import date
            mes_corrente = date.today().strftime('%Y-%m')
            filter_params['mes_emissao'] = mes_corrente
            
        self.filter = self.filterset_class(filter_params, queryset=qs)
        # Aplica ordenação padrão por data de emissão descendente se não houver ordenação específica
        filtered_qs = self.filter.qs
        if 'sort' not in self.request.GET:
            filtered_qs = filtered_qs.order_by('-dtEmissao')
        return filtered_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        table = self.table_class(queryset)
        
        # Configurar tabela com parâmetros específicos incluindo ordenação padrão
        request_config = RequestConfig(
            self.request, 
            paginate={'per_page': self.paginate_by}
        )
        
        # Se não há parâmetro de ordenação na URL, usar ordenação padrão da tabela
        if 'sort' not in self.request.GET:
            # Force a ordenação padrão por data de emissão descendente
            table.order_by = '-dtEmissao'
            
        request_config.configure(table)
        nota_id = self.request.GET.get('nota_id')
        context['filter'] = getattr(self, 'filter', None)
        nota_fiscal = None
        if nota_id:
            try:
                nota_fiscal = queryset.get(id=nota_id)
            except (NotaFiscal.DoesNotExist, ValueError):
                nota_fiscal = None
        elif queryset.exists():
            nota_fiscal = queryset.first()
        if nota_fiscal:
            nota_fiscal = NotaFiscal.objects.get(id=nota_fiscal.id)
        medicos_empresa = []
        if nota_fiscal and nota_fiscal.empresa_destinataria:
            medicos_empresa = list(Socio.objects.filter(empresa=nota_fiscal.empresa_destinataria, ativo=True).select_related('pessoa'))
        medicos_rateio = []
        rateios_map = {}
        total_percentual_rateado = None
        if nota_fiscal:
            rateios_qs = nota_fiscal.rateios_medicos.select_related('medico')
            rateios_map = {r.medico_id: r for r in rateios_qs}
            total_percentual_rateado = sum([float(r.percentual_participacao) for r in rateios_qs]) if rateios_qs.exists() else 0.0
        for medico in medicos_empresa:
            rateio = rateios_map.get(medico.id)
            valor_bruto_medico = float(rateio.valor_bruto_medico) if rateio else 0.0
            medicos_rateio.append({
                'medico': medico,
                'valor_bruto_medico': valor_bruto_medico,
                'rateio_id': rateio.id if rateio else None,
            })
        context.update({
            'table': table,
            'nota_fiscal': nota_fiscal,
            'medicos_rateio': medicos_rateio,
            'titulo_pagina': 'Rateio de Notas Fiscais',
            'total_percentual_rateado': total_percentual_rateado,
            'mes_corrente': date.today().strftime('%Y-%m'),  # Para valor padrão do filtro
        })
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoListView(RateioContextMixin, ListView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/lista_rateio_medicos.html'
    context_object_name = 'table'
    paginate_by = 20
    table_class = NotaFiscalRateioTable

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        # Redirecionar se a nota fiscal estiver cancelada
        if self.nota_fiscal.status_recebimento == 'cancelado':
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Não é possível acessar rateio de nota fiscal cancelada.')
            return redirect('medicos:lista_notas_rateio')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return NotaFiscalRateioMedico.objects.filter(nota_fiscal=self.nota_fiscal)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        table = self.table_class(self.get_queryset())
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        context['titulo_pagina'] = 'Rateio de Notas Fiscais por Médico'
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoCreateView(RateioContextMixin, CreateView):
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.nota_fiscal = self.nota_fiscal
        return form
    model = NotaFiscalRateioMedico
    form_class = NotaFiscalRateioMedicoForm
    template_name = 'faturamento/rateio_medico_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        # Redirecionar se a nota fiscal estiver cancelada
        if self.nota_fiscal.status_recebimento == 'cancelado':
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Não é possível criar rateio para nota fiscal cancelada.')
            return redirect('medicos:lista_notas_rateio')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Always set nota_fiscal from dispatch (using nota_id)
        form.instance.nota_fiscal = self.nota_fiscal
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('medicos:lista_rateio_medicos', kwargs={'nota_id': self.nota_fiscal.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        context['titulo_pagina'] = 'Adicionar Rateio Médico'
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoUpdateView(RateioContextMixin, UpdateView):
    model = NotaFiscalRateioMedico
    form_class = NotaFiscalRateioMedicoForm
    template_name = 'faturamento/rateio_medico_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        # Redirecionar se a nota fiscal estiver cancelada
        if self.nota_fiscal.status_recebimento == 'cancelado':
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Não é possível editar rateio de nota fiscal cancelada.')
            return redirect('medicos:lista_notas_rateio')
        self.rateio = get_object_or_404(NotaFiscalRateioMedico, id=self.kwargs['rateio_id'], nota_fiscal=self.nota_fiscal)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.rateio

    def get_success_url(self):
        return reverse('medicos:lista_rateio_medicos', kwargs={'nota_id': self.nota_fiscal.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        context['titulo_pagina'] = 'Editar Rateio Médico'
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoDeleteView(RateioContextMixin, DeleteView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/rateio_medico_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        # Redirecionar se a nota fiscal estiver cancelada
        if self.nota_fiscal.status_recebimento == 'cancelado':
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Não é possível excluir rateio de nota fiscal cancelada.')
            return redirect('medicos:lista_notas_rateio')
        self.rateio = get_object_or_404(NotaFiscalRateioMedico, id=self.kwargs['rateio_id'], nota_fiscal=self.nota_fiscal)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.rateio

    def get_success_url(self):
        return reverse('medicos:lista_rateio_medicos', kwargs={'nota_id': self.nota_fiscal.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nota_fiscal'] = self.nota_fiscal
        context['titulo_pagina'] = 'Excluir Rateio Médico'
        return context
