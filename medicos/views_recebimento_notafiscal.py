from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
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
        
        # Filtro por mês/ano de emissão - aplica mês atual como padrão se não especificado
        mes_ano_emissao = self.request.GET.get('mes_ano_emissao')
        if not mes_ano_emissao:
            # Se não há filtro na query string, aplica o mês atual
            import datetime
            now = datetime.date.today()
            mes_ano_emissao = f"{now.year:04d}-{now.month:02d}"
        
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
        return qs

    def get_context_data(self, **kwargs):
        import datetime
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Recebimento de Notas Fiscais'
        context['cenario_nome'] = 'Financeiro'
        context['menu_nome'] = 'Recebimento de Notas'
        
        # Define valor default para mes_ano_emissao se não informado
        mes_ano_emissao = self.request.GET.get('mes_ano_emissao')
        if not mes_ano_emissao:
            now = datetime.date.today()
            mes_ano_emissao = f"{now.year:04d}-{now.month:02d}"
        context['mes_ano_emissao_default'] = mes_ano_emissao
        
        # Define valor default para mes_ano_recebimento (mantém valor do GET se existir)
        mes_ano_recebimento = self.request.GET.get('mes_ano_recebimento', '')
        context['mes_ano_recebimento_default'] = mes_ano_recebimento
        
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalRecebimentoUpdateView(UpdateView):
    model = NotaFiscal
    from .forms_recebimento_notafiscal import NotaFiscalRecebimentoForm
    form_class = NotaFiscalRecebimentoForm
    template_name = 'financeiro/editar_recebimento_nota_fiscal.html'
    success_url = reverse_lazy('medicos:recebimento_notas_fiscais')

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
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Recebimento atualizado com sucesso!')
        return super().form_valid(form)
