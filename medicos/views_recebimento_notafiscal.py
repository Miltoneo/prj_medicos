from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, View
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from medicos.models.fiscal import NotaFiscal
from .tables_recebimento_notafiscal import NotaFiscalRecebimentoTable
from .filters_recebimento_notafiscal import NotaFiscalRecebimentoFilter
from .forms_notafiscal import NotaFiscalForm

@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoListView(SingleTableMixin, FilterView):
    model = NotaFiscal
    table_class = NotaFiscalRecebimentoTable
    filterset_class = NotaFiscalRecebimentoFilter
    template_name = 'financeiro/recebimento_notas_fiscais.html'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return NotaFiscal.objects.none()
            
        # Carregar relacionamentos necessários para as propriedades de rateio
        qs = NotaFiscal.objects.filter(
            empresa_destinataria__id=int(empresa_id)
        ).select_related(
            'empresa_destinataria', 
            'meio_pagamento'
        ).prefetch_related(
            'rateios_medicos'  # Essencial para tem_rateio e rateio_completo
        ).order_by('-dtEmissao')
        
        # Filtro por mês/ano de emissão - só aplica se explicitamente informado
        mes_ano_emissao = self.request.GET.get('mes_ano_emissao')
        if mes_ano_emissao:
            try:
                ano, mes = mes_ano_emissao.split('-')
                qs = qs.filter(dtEmissao__year=int(ano), dtEmissao__month=int(mes))
            except Exception:
                pass
        
        # Filtro por mês/ano de recebimento
        mes_ano_recebimento = self.request.GET.get('mes_ano_recebimento')
        if mes_ano_recebimento:
            try:
                ano, mes = mes_ano_recebimento.split('-')
                qs = qs.filter(dtRecebimento__year=int(ano), dtRecebimento__month=int(mes))
            except Exception:
                pass
        
        # Filtro por status de recebimento
        status_recebimento = self.request.GET.get('status_recebimento')
        if status_recebimento:
            qs = qs.filter(status_recebimento=status_recebimento)
        
        # Filtro por número da nota fiscal
        numero = self.request.GET.get('numero')
        if numero:
            qs = qs.filter(numero__icontains=numero)
        
        return qs

    def get_context_data(self, **kwargs):
        from django.db.models import Sum, Q
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Recebimento de Notas Fiscais'
        context['cenario_nome'] = 'Financeiro'
        context['menu_nome'] = 'Recebimento de Notas'
        
        # Define valor default para mes_ano_emissao apenas se informado na query string
        mes_ano_emissao = self.request.GET.get('mes_ano_emissao', '')
        context['mes_ano_emissao_default'] = mes_ano_emissao
        
        # Define valor default para mes_ano_recebimento (mantém valor do GET se existir)
        mes_ano_recebimento = self.request.GET.get('mes_ano_recebimento', '')
        context['mes_ano_recebimento_default'] = mes_ano_recebimento
        
        # Calcula totais das notas fiscais filtradas EXCLUINDO notas canceladas
        queryset_filtrado = self.get_queryset()
        queryset_para_totalizacao = queryset_filtrado.exclude(status_recebimento='cancelado')
        
        totais = queryset_para_totalizacao.aggregate(
            total_val_bruto=Sum('val_bruto'),
            total_val_liquido=Sum('val_liquido'),
            total_val_ISS=Sum('val_ISS'),
            total_val_PIS=Sum('val_PIS'),
            total_val_COFINS=Sum('val_COFINS'),
            total_val_IR=Sum('val_IR'),
            total_val_CSLL=Sum('val_CSLL'),
            total_val_outros=Sum('val_outros')
        )
        
        # Calcula quantidade de notas fiscais por status (considera todas, incluindo canceladas)
        status_count = queryset_filtrado.aggregate(
            total_notas=models.Count('id'),
            pendentes=models.Count('id', filter=Q(status_recebimento='pendente')),
            recebidas=models.Count('id', filter=Q(status_recebimento='recebido')),
            canceladas=models.Count('id', filter=Q(status_recebimento='cancelado'))
        )
        
        # Adiciona totais ao contexto, garantindo que valores None sejam convertidos para 0
        context['totais'] = {
            'total_val_bruto': totais['total_val_bruto'] or 0,
            'total_val_liquido': totais['total_val_liquido'] or 0,
            'total_val_ISS': totais['total_val_ISS'] or 0,
            'total_val_PIS': totais['total_val_PIS'] or 0,
            'total_val_COFINS': totais['total_val_COFINS'] or 0,
            'total_val_IR': totais['total_val_IR'] or 0,
            'total_val_CSLL': totais['total_val_CSLL'] or 0,
            'total_val_outros': totais['total_val_outros'] or 0,
            'total_impostos': (
                (totais['total_val_ISS'] or 0) +
                (totais['total_val_PIS'] or 0) +
                (totais['total_val_COFINS'] or 0) +
                (totais['total_val_IR'] or 0) +
                (totais['total_val_CSLL'] or 0) +
                (totais['total_val_outros'] or 0)
            )
        }
        
        context['status_count'] = {
            'total_notas': status_count['total_notas'] or 0,
            'pendentes': status_count['pendentes'] or 0,
            'recebidas': status_count['recebidas'] or 0,
            'canceladas': status_count['canceladas'] or 0,
            'notas_validas': (status_count['pendentes'] or 0) + (status_count['recebidas'] or 0)
        }
        
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoUpdateView(UpdateView):
    model = NotaFiscal
    from .forms_recebimento_notafiscal import NotaFiscalRecebimentoForm
    form_class = NotaFiscalRecebimentoForm
    template_name = 'financeiro/editar_recebimento_nota_fiscal.html'

    def get_success_url(self):
        """Redireciona de volta para a listagem mantendo os filtros originais"""
        from django.http import QueryDict
        
        # Captura os parâmetros de filtro da query string atual
        filtros = self.request.GET.copy()
        
        # Remove parâmetros que não são filtros (se houver)
        parametros_filtro = ['numero', 'mes_ano_emissao', 'mes_ano_recebimento', 'status_recebimento']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        # Constrói a URL de retorno com os filtros
        url_base = reverse_lazy('medicos:recebimento_notas_fiscais')
        if filtros_limpos:
            return f"{url_base}?{filtros_limpos.urlencode()}"
        
        return url_base

    def dispatch(self, request, *args, **kwargs):
        """
        Valida se a nota fiscal pode ter o recebimento editado antes de qualquer processamento.
        REGRA: Apenas notas com rateio COMPLETO podem ser editadas.
        """
        # Primeiro obtém o objeto usando o pk da URL
        try:
            pk = self.kwargs.get('pk')
            nota_fiscal = NotaFiscal.objects.get(pk=pk)
            
            # NOVA REGRA: Apenas notas com rateio completo podem ser editadas
            if not nota_fiscal.tem_rateio:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied(
                    f"Esta nota fiscal não pode ter o recebimento editado porque não possui rateio configurado. "
                    f"Configure o rateio antes de editar o recebimento."
                )
            elif not nota_fiscal.rateio_completo:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied(
                    f"Esta nota fiscal não pode ter o recebimento editado porque o rateio está incompleto. "
                    f"Atual: {nota_fiscal.percentual_total_rateado:.1f}% de 100%. "
                    f"Complete o rateio antes de editar o recebimento."
                )
                
        except NotaFiscal.DoesNotExist:
            from django.http import Http404
            raise Http404("Nota fiscal não encontrada")
        
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        """
        Garantir que temos acesso ao objeto e validar se pode ser editado.
        REGRA: Apenas notas com rateio COMPLETO podem ser editadas.
        """
        obj = super().get_object()
        
        # NOVA REGRA: Apenas notas com rateio completo podem ser editadas
        if not obj.tem_rateio:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                f"Esta nota fiscal não pode ter o recebimento editado porque não possui rateio configurado."
            )
        elif not obj.rateio_completo:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                f"Esta nota fiscal não pode ter o recebimento editado porque o rateio está incompleto. "
                f"Atual: {obj.percentual_total_rateado:.1f}% de 100%. "
                f"Complete o rateio antes de editar o recebimento."
            )
        
        return obj

    def get_form_kwargs(self):
        """Garantir que a instância está disponível para o formulário"""
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Recebimento de Nota Fiscal'
        context['cenario_nome'] = 'Financeiro'
        
        # Adiciona informações sobre os filtros para debug/referência
        filtros_ativos = {}
        for param in ['numero', 'mes_ano_emissao', 'mes_ano_recebimento', 'status_recebimento']:
            if param in self.request.GET:
                filtros_ativos[param] = self.request.GET[param]
        context['filtros_originais'] = filtros_ativos
        
        return context

    def form_valid(self, form):
        # Definir status de recebimento automaticamente baseado na data de recebimento
        if form.cleaned_data.get('dtRecebimento'):
            form.instance.status_recebimento = 'recebido'
        else:
            form.instance.status_recebimento = 'pendente'
            
        messages.success(self.request, 'Recebimento atualizado com sucesso!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoCancelarView(View):
    """
    View para cancelar uma nota fiscal no contexto de recebimento
    Altera o status do recebimento para 'cancelado'
    """
    
    def post(self, request, pk):
        empresa_id = request.session.get('empresa_id')
        if not empresa_id:
            messages.error(request, 'Empresa não selecionada.')
            return redirect('medicos:recebimento_notas_fiscais')
            
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk, empresa_destinataria__id=int(empresa_id))
        
        # Verificar se a nota fiscal pode ser cancelada
        if nota_fiscal.status_recebimento == 'cancelado':
            messages.warning(request, 'Esta nota fiscal já está cancelada.')
        else:
            # Permitir cancelar qualquer nota (pendente ou recebida)
            nota_fiscal.status_recebimento = 'cancelado'
            if nota_fiscal.dtRecebimento:
                # Se tinha data de recebimento, remove ao cancelar
                nota_fiscal.dtRecebimento = None
                messages.success(request, f'Nota fiscal {nota_fiscal.numero} foi cancelada com sucesso. Data de recebimento removida.')
            else:
                messages.success(request, f'Nota fiscal {nota_fiscal.numero} foi cancelada com sucesso.')
            nota_fiscal.save()
        
        # Preservar todos os filtros originais da busca
        from django.http import QueryDict
        filtros = request.GET.copy()
        parametros_filtro = ['numero', 'mes_ano_emissao', 'mes_ano_recebimento', 'status_recebimento']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        url_base = reverse_lazy('medicos:recebimento_notas_fiscais')
        if filtros_limpos:
            return redirect(f"{url_base}?{filtros_limpos.urlencode()}")
        
        return redirect(url_base)


@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoPendenteView(View):
    """
    View para alterar o status de uma nota fiscal para 'pendente'
    Útil para reverter cancelamentos ou status incorretos
    """
    
    def post(self, request, pk):
        empresa_id = request.session.get('empresa_id')
        if not empresa_id:
            messages.error(request, 'Empresa não selecionada.')
            return redirect('medicos:recebimento_notas_fiscais')
            
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk, empresa_destinataria__id=int(empresa_id))
        
        # Verificar se a nota fiscal pode ter o status alterado para pendente
        if nota_fiscal.status_recebimento == 'pendente':
            messages.info(request, 'Esta nota fiscal já está com status pendente.')
        elif nota_fiscal.status_recebimento == 'recebido':
            # Permitir alterar de recebido para pendente (para correções)
            nota_fiscal.status_recebimento = 'pendente'
            nota_fiscal.dtRecebimento = None  # Remove a data de recebimento
            nota_fiscal.save()
            
            messages.success(request, f'Nota fiscal {nota_fiscal.numero} alterada para status pendente. Data de recebimento removida.')
        elif nota_fiscal.status_recebimento == 'cancelado':
            # Permitir alterar de cancelado para pendente (reativar)
            nota_fiscal.status_recebimento = 'pendente'
            nota_fiscal.save()
            
            messages.success(request, f'Nota fiscal {nota_fiscal.numero} reativada e alterada para status pendente.')
        
        # Preservar todos os filtros originais da busca
        from django.http import QueryDict
        filtros = request.GET.copy()
        parametros_filtro = ['numero', 'mes_ano_emissao', 'mes_ano_recebimento', 'status_recebimento']
        filtros_limpos = QueryDict(mutable=True)
        
        for param in parametros_filtro:
            if param in filtros:
                filtros_limpos[param] = filtros[param]
        
        url_base = reverse_lazy('medicos:recebimento_notas_fiscais')
        if filtros_limpos:
            return redirect(f"{url_base}?{filtros_limpos.urlencode()}")
        
        return redirect(url_base)
