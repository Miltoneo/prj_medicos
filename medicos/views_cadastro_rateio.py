


from datetime import date
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_filters.views import FilterView
import django_tables2 as tables
from django_tables2.views import SingleTableMixin
from medicos.models.despesas import ItemDespesaRateioMensal, ItemDespesa, GrupoDespesa, Socio
from medicos.forms import ItemDespesaRateioMensalForm
from medicos.filters_rateio_medico import ItemDespesaRateioMensalFilter


def converter_percentual_seguro(valor_str):
    """
    Converte string de percentual para Decimal com exatamente 2 casas decimais
    
    Args:
        valor_str: String com o valor do percentual
        
    Returns:
        Decimal: Valor convertido com 2 casas decimais ou None se inválido
    """
    if not valor_str or valor_str.strip() == '':
        return None
    
    try:
        # Substitui vírgula por ponto para aceitar formato brasileiro
        valor_limpo = str(valor_str).strip().replace(',', '.')
        
        # Converte para Decimal diretamente, garantindo precisão
        decimal_valor = Decimal(valor_limpo)
        
        # Arredonda para exatamente 2 casas decimais
        return decimal_valor.quantize(Decimal('0.01'))
        
    except (InvalidOperation, ValueError, TypeError):
        return None


def cadastro_rateio_list(request):
    # Mês padrão
    default_mes = date.today().strftime('%Y-%m')
    # Suporte a GET e POST para manter filtros
    if request.method == 'POST':
        # Recupera filtros do POST (hidden ou session, se necessário)
        mes_competencia = request.POST.get('mes_competencia')
        selected_item_id = request.POST.get('item_despesa')
    else:
        mes_competencia = request.GET.get('mes_competencia')
        selected_item_id = request.GET.get('item_despesa')
    from datetime import datetime
    if not mes_competencia:
        mes_competencia = default_mes
    if len(mes_competencia) == 7:
        mes_competencia = mes_competencia + '-01'
    # Converter para objeto date
    try:
        mes_competencia_date = datetime.strptime(mes_competencia, '%Y-%m-%d').date()
    except Exception:
        mes_competencia_date = date.today().replace(day=1)
    # Garante que sempre será o primeiro dia do mês
    mes_competencia_date = mes_competencia_date.replace(day=1)
    # Exibir apenas itens de grupos com tipo_rateio=COM_RATEIO
    grupos_com_rateio = GrupoDespesa.objects.filter(tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO)
    itens_despesa = ItemDespesa.objects.filter(grupo_despesa__in=grupos_com_rateio)
    # Itens de despesa com rateio para o mês selecionado
    itens_com_rateio_ids = ItemDespesaRateioMensal.objects.filter(data_referencia=mes_competencia).values_list('item_despesa_id', flat=True).distinct()
    itens_com_rateio_ids = list(itens_com_rateio_ids)
    rateios = []
    total_percentual = 0
    if selected_item_id:
        try:
            item = ItemDespesa.objects.select_related('grupo_despesa').get(id=selected_item_id)
            grupo = getattr(item, 'grupo_despesa', None)
            empresa = getattr(grupo, 'empresa', None) if grupo else None
            permite_rateio = True
        except ItemDespesa.DoesNotExist:
            item = None
            grupo = None
            empresa = None
            permite_rateio = False
        if empresa:
            socios_empresa = Socio.objects.filter(empresa=empresa, ativo=True)
        else:
            socios_empresa = Socio.objects.none()
        # Só processa rateio se o item permitir
        if permite_rateio:
            if request.method == 'POST':
                # Validação do total do rateio usando Decimal para precisão
                total_percentual_post = Decimal('0.00')
                valores_validos = {}  # Para armazenar valores convertidos
                
                for socio in socios_empresa:
                    r_id = None
                    val = None
                    # Verifica se já existe rateio para esse sócio
                    rateio_existente = ItemDespesaRateioMensal.objects.filter(item_despesa_id=selected_item_id, data_referencia=mes_competencia_date, socio=socio).first()
                    if rateio_existente:
                        r_id = rateio_existente.id
                        val = request.POST.get(f'percentual_{r_id}')
                        chave = f'percentual_{r_id}'
                    else:
                        val = request.POST.get(f'percentual_socio_{socio.id}')
                        chave = f'percentual_socio_{socio.id}'
                    
                    if val is not None and val != '':
                        val_decimal = converter_percentual_seguro(val)
                        if val_decimal is not None:
                            valores_validos[chave] = val_decimal
                            total_percentual_post += val_decimal
                
                # Permite pequena margem de erro de ponto flutuante (0.01)
                cem_percent = Decimal('100.00')
                if abs(total_percentual_post - cem_percent) > Decimal('0.01'):
                    messages.error(request, f'O total do rateio deve ser exatamente 100%. Total atual: {total_percentual_post:.2f}%. Corrija os percentuais antes de salvar.')
                    # Monta rateios para reexibir na tela com os valores do POST
                    rateios = []
                    for socio in socios_empresa:
                        rateio_existente = ItemDespesaRateioMensal.objects.filter(item_despesa_id=selected_item_id, data_referencia=mes_competencia_date, socio=socio).first()
                        if rateio_existente:
                            r_id = rateio_existente.id
                            val = request.POST.get(f'percentual_{r_id}')
                        else:
                            val = request.POST.get(f'percentual_socio_{socio.id}')
                        
                        percentual = converter_percentual_seguro(val)
                        
                        fake = ItemDespesaRateioMensal(
                            item_despesa_id=selected_item_id,
                            socio=socio,
                            percentual_rateio=percentual,
                            observacoes=getattr(rateio_existente, 'observacoes', ''),
                            data_referencia=mes_competencia_date,
                            ativo=True
                        )
                        # Adiciona ID fictício para rateios existentes
                        if rateio_existente:
                            fake.id = rateio_existente.id
                        rateios.append(fake)
                    total_percentual = float(total_percentual_post)
                    context = {
                        'default_mes': default_mes,
                        'mes_competencia': mes_competencia[:7] if mes_competencia else '',
                        'itens_despesa': itens_despesa,
                        'itens_com_rateio_ids': itens_com_rateio_ids,
                        'selected_item_id': int(selected_item_id) if selected_item_id else None,
                        'rateios': rateios,
                        'socios_empresa_debug': list(socios_empresa) if selected_item_id else [],
                        'rateios_debug': rateios,
                        'total_percentual': '{:.2f}'.format(total_percentual),
                        'item_debug': item,
                        'grupo_debug': grupo,
                        'empresa_debug': empresa,
                        'permite_rateio': permite_rateio,
                    }
                    return render(request, 'cadastro/rateio_list.html', context)
                # Se passou na validação, salva normalmente usando valores já validados
                rateios_qs = ItemDespesaRateioMensal.objects.filter(item_despesa_id=selected_item_id, data_referencia=mes_competencia_date)
                rateios_dict = {r.socio_id: r for r in rateios_qs}
                
                for socio in socios_empresa:
                    # Atualiza existentes
                    r = rateios_dict.get(socio.id)
                    if r:
                        chave = f'percentual_{r.id}'
                        if chave in valores_validos:
                            r.percentual_rateio = valores_validos[chave]
                            r.save()
                    else:
                        # Cria novos
                        chave = f'percentual_socio_{socio.id}'
                        if chave in valores_validos:
                            ItemDespesaRateioMensal.objects.create(
                                item_despesa_id=selected_item_id,
                                socio=socio,
                                percentual_rateio=valores_validos[chave],
                                data_referencia=mes_competencia_date
                            )
                # Após salvar, redireciona para GET com filtros (PRG pattern)
                from django.urls import reverse
                url = reverse('medicos:cadastro_rateio') + f'?mes_competencia={mes_competencia[:7]}&item_despesa={selected_item_id}'
                return redirect(url)
            # Monta contexto para GET
            rateios_qs = ItemDespesaRateioMensal.objects.filter(item_despesa_id=selected_item_id, data_referencia=mes_competencia_date, ativo=True).select_related('socio__pessoa')
            # Garante que todos os sócios ativos da empresa aparecem, mesmo sem rateio cadastrado
            rateios_dict = {r.socio_id: r for r in rateios_qs}
            rateios = []
            for socio in socios_empresa:
                r = rateios_dict.get(socio.id)
                if r:
                    rateios.append(r)
                else:
                    fake = ItemDespesaRateioMensal(
                        item_despesa_id=selected_item_id,
                        socio=socio,
                        percentual_rateio=None,
                        observacoes='',
                        data_referencia=mes_competencia_date,
                        ativo=True
                    )
                    rateios.append(fake)
            # Calcula total percentual usando Decimal para precisão
            total_percentual = sum([
                Decimal(str(r.percentual_rateio)) for r in rateios 
                if r.percentual_rateio is not None
            ], Decimal('0.00'))
            total_percentual = float(total_percentual)  # Converte para float apenas para exibição
        else:
            # Item não permite rateio, não processa POST nem busca rateios
            pass
    else:
        item = None
        grupo = None
        empresa = None
        permite_rateio = False
    context = {
        'default_mes': default_mes,
        'mes_competencia': mes_competencia[:7] if mes_competencia else '',
        'itens_despesa': itens_despesa,
        'itens_com_rateio_ids': itens_com_rateio_ids,
        'selected_item_id': int(selected_item_id) if selected_item_id else None,
        'rateios': rateios,
        'socios_empresa_debug': list(socios_empresa) if selected_item_id else [],
        'rateios_debug': rateios,
        'total_percentual': '{:.2f}'.format(total_percentual),
        'item_debug': item,
        'grupo_debug': grupo,
        'empresa_debug': empresa,
        'permite_rateio': permite_rateio,
        'titulo_pagina': 'Configuração de Rateio',
    }
    return render(request, 'cadastro/rateio_list.html', context)


class ItemDespesaRateioMensalTable(tables.Table):
    class Meta:
        model = ItemDespesaRateioMensal
        template_name = "django_tables2/bootstrap4.html"
        fields = ("data_referencia", "item_despesa", "socio", "percentual_rateio", "observacoes", "ativo")
        attrs = {"class": "table table-striped table-bordered"}

class CadastroRateioView(SingleTableMixin, FilterView):
    model = ItemDespesaRateioMensal
    table_class = ItemDespesaRateioMensalTable
    template_name = "cadastro/rateio_list.html"
    filterset_class = ItemDespesaRateioMensalFilter
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = _(u"Configuração de Rateio Mensal")
        context['itens_despesa'] = ItemDespesa.objects.all()
        context['socios'] = Socio.objects.all()
        # Adiciona mes_competencia e default_mes ao contexto para compatibilidade com o template
        from datetime import date
        default_mes = date.today().strftime('%Y-%m')
        mes_competencia = self.request.GET.get('mes_competencia', default_mes)
        context['default_mes'] = default_mes
        context['mes_competencia'] = mes_competencia
        return context

class CadastroRateioCreateView(CreateView):
    model = ItemDespesaRateioMensal
    form_class = ItemDespesaRateioMensalForm
    template_name = "cadastro/rateio_form.html"
    success_url = reverse_lazy('cadastro_rateio')

    def form_valid(self, form):
        messages.success(self.request, _(u"Configuração de rateio criada com sucesso."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Configuração de Rateio"
        return context

class CadastroRateioUpdateView(UpdateView):
    model = ItemDespesaRateioMensal
    form_class = ItemDespesaRateioMensalForm
    template_name = "cadastro/rateio_form.html"
    success_url = reverse_lazy('cadastro_rateio')

    def form_valid(self, form):
        messages.success(self.request, _(u"Configuração de rateio atualizada com sucesso."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Configuração de Rateio"
        return context

class CadastroRateioDeleteView(DeleteView):
    model = ItemDespesaRateioMensal
    template_name = "cadastro/rateio_confirm_delete.html"
    success_url = reverse_lazy('cadastro_rateio')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _(u"Configuração de rateio removida com sucesso."))
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Configuração de Rateio"
        return context
