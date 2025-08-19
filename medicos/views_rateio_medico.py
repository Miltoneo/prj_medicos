
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django.shortcuts import get_object_or_404
from .tables_rateio_medico import NotaFiscalRateioMedicoTable
from .filters_rateio_medico import NotaFiscalRateioMedicoFilter
from medicos.models.fiscal import NotaFiscalRateioMedico, NotaFiscal
from medicos.models.base import Empresa

@method_decorator(login_required, name='dispatch')
class NotaFiscalRateioMedicoListView(FilterView):
    model = NotaFiscalRateioMedico
    template_name = 'faturamento/lista_notas_rateio_medicos.html'
    filterset_class = NotaFiscalRateioMedicoFilter
    table_class = NotaFiscalRateioMedicoTable
    context_object_name = 'table'
    paginate_by = 20


    def dispatch(self, request, *args, **kwargs):
        self.nota_fiscal = None
        if 'nota_id' in self.kwargs:
            self.nota_fiscal = get_object_or_404(NotaFiscal, id=self.kwargs['nota_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Filtrar pela empresa ativa da sessão
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return NotaFiscalRateioMedico.objects.none()
        
        if self.nota_fiscal:
            # Se há uma nota específica, filtrar apenas por ela (já está implicitamente filtrada por empresa)
            qs = NotaFiscalRateioMedico.objects.filter(nota_fiscal=self.nota_fiscal)
        else:
            # Filtrar rateios de notas fiscais da empresa ativa
            qs = NotaFiscalRateioMedico.objects.filter(
                nota_fiscal__empresa_destinataria__id=int(empresa_id)
            )
            
        # Filtrar rateios de notas com status cancelado - não exibir no rateio
        qs = qs.exclude(nota_fiscal__status_recebimento='cancelado')
        
        filter_params = self.request.GET.copy()
        # Remove parâmetros que não são de filtro
        if 'page' in filter_params:
            filter_params.pop('page')
        
        # Remove o parâmetro clear se existir (usado para detectar ação de limpar)
        is_clear_action = filter_params.pop('clear', None) == ['1']
            
        # Se não há filtros específicos E não é uma ação de limpar, aplicar filtro do mês corrente por padrão
        if not filter_params and not is_clear_action:
            from datetime import date
            mes_corrente = date.today().strftime('%Y-%m')
            filter_params['competencia'] = mes_corrente
            
        self.filter = self.filterset_class(filter_params, queryset=qs, request=self.request)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        """
        Regra de padronização:
        - NÃO injete manualmente a variável 'empresa' no contexto. Ela já estará disponível via context processor.
        - O nome da empresa será exibido automaticamente pelo template base_header.html, que deve ser incluído no template base.
        - Injete apenas 'titulo_pagina' para exibição correta no header.
        """
        context = super().get_context_data(**kwargs)
        
        # Verificar se há empresa selecionada
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            context['erro_empresa'] = 'Nenhuma empresa selecionada. Selecione uma empresa para visualizar os rateios.'
            context['total_bruto'] = 0
            context['total_liquido'] = 0
            context['total_iss'] = 0
            context['total_pis'] = 0
            context['total_cofins'] = 0
            context['total_ir'] = 0
            context['total_csll'] = 0
        else:
            table = self.table_class(self.get_queryset())
            context['table'] = table
            context['filter'] = getattr(self, 'filter', None)
            if self.nota_fiscal:
                context['nota_fiscal'] = self.nota_fiscal
            qs = self.get_queryset()
            context['total_bruto'] = sum(getattr(obj, 'valor_bruto_medico', 0) or 0 for obj in qs)
            context['total_liquido'] = sum(getattr(obj, 'valor_liquido_medico', 0) or 0 for obj in qs)
            context['total_iss'] = sum(getattr(obj, 'valor_iss_medico', 0) or 0 for obj in qs)
            context['total_pis'] = sum(getattr(obj, 'valor_pis_medico', 0) or 0 for obj in qs)
            context['total_cofins'] = sum(getattr(obj, 'valor_cofins_medico', 0) or 0 for obj in qs)
            context['total_ir'] = sum(getattr(obj, 'valor_ir_medico', 0) or 0 for obj in qs)
            context['total_csll'] = sum(getattr(obj, 'valor_csll_medico', 0) or 0 for obj in qs)
        
        context['titulo_pagina'] = 'Notas Fiscais Rateadas por Médico'
        return context
