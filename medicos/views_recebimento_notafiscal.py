from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
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
        qs = NotaFiscal.objects.filter(empresa_destinataria__id=int(empresa_id)).order_by('-dtEmissao')
        
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
        
        # Calcula totais das notas fiscais filtradas
        queryset_filtrado = self.get_queryset()
        totais = queryset_filtrado.aggregate(
            total_val_bruto=Sum('val_bruto'),
            total_val_liquido=Sum('val_liquido'),
            total_val_ISS=Sum('val_ISS'),
            total_val_PIS=Sum('val_PIS'),
            total_val_COFINS=Sum('val_COFINS'),
            total_val_IR=Sum('val_IR'),
            total_val_CSLL=Sum('val_CSLL'),
            total_val_outros=Sum('val_outros')
        )
        
        # Calcula quantidade de notas fiscais por status
        status_count = queryset_filtrado.aggregate(
            total_notas=models.Count('id'),
            pendentes=models.Count('id', filter=Q(status_recebimento='pendente')),
            recebidas=models.Count('id', filter=Q(status_recebimento='recebido'))
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
            'recebidas': status_count['recebidas'] or 0
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

    def get_object(self):
        """Garantir que temos acesso ao objeto antes de instanciar o formulário"""
        obj = super().get_object()
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
        messages.success(self.request, 'Recebimento atualizado com sucesso!')
        return super().form_valid(form)
