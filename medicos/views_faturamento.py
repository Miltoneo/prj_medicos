# Django imports
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator

# Third-party imports
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from medicos.models.fiscal import NotaFiscal, Aliquotas
from .tables_notafiscal_lista import NotaFiscalListaTable
from .filters_notafiscal import NotaFiscalFilter
from .forms_notafiscal import NotaFiscalForm
from core.context_processors import empresa_context

class NotaFiscalCreateView(CreateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/criar_nota_fiscal.html'

    def get_success_url(self):
        # Preservar TODOS os filtros originais da busca (vindos da tela de lista)
        params = []
        
        # Preserva todos os parâmetros GET que vieram da tela de lista
        for key, value in self.request.GET.items():
            if value:
                params.append(f'{key}={value}')
        
        url = reverse('medicos:lista_notas_fiscais')
        if params:
            url += '?' + '&'.join(params)
        return url


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nova Nota Fiscal'
        context['cenario_nome'] = 'Faturamento'
        
        # Empresa sempre existe
        empresa = empresa_context(self.request)['empresa']
        aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa)
        
        # Configurar campos do formulário
        context.update({
            'campos_topo': [
                'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
            ],
            'campos_excluir': [
                'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento', 'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
            ]
        })
        
        # Verificar se há data de emissão específica
        dt_emissao = self.request.POST.get('dtEmissao') or self.request.GET.get('dtEmissao')
        if dt_emissao:
            aliquota_para_data = Aliquotas.obter_aliquota_vigente(empresa, dt_emissao)
            if not aliquota_para_data:
                context['erro_aliquota'] = 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.'
                context['aliquota_vigente'] = False
                aliquota_vigente = None
            else:
                aliquota_vigente = aliquota_para_data
        
        # Definir alíquotas no contexto
        if aliquota_vigente:
            context.update({
                'aliquota_ISS': getattr(aliquota_vigente, 'ISS', 0),
                'aliquota_PIS': getattr(aliquota_vigente, 'PIS', 0),
                'aliquota_COFINS': getattr(aliquota_vigente, 'COFINS', 0),
                'aliquota_IR': getattr(aliquota_vigente, 'IRPJ_RETENCAO_FONTE', 0),
                'aliquota_CSLL': getattr(aliquota_vigente, 'CSLL_RETENCAO_FONTE', 0),
            })
        else:
            context.update({
                'aliquota_ISS': 0,
                'aliquota_PIS': 0,
                'aliquota_COFINS': 0,
                'aliquota_IR': 0,
                'aliquota_CSLL': 0,
            })
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Empresa sempre existe
        empresa = empresa_context(self.request)['empresa']
        form.empresa_sessao = empresa
        return form

    def form_valid(self, form):
        # Empresa sempre existe
        empresa = empresa_context(self.request)['empresa']
        form.instance.empresa_destinataria = empresa
        
        # Verificar alíquota vigente
        dt_emissao = form.cleaned_data.get('dtEmissao')
        aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa, dt_emissao) if dt_emissao else Aliquotas.obter_aliquota_vigente(empresa)
        
        if not aliquota_vigente:
            form.add_error(None, 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.')
            return self.form_invalid(form)
            
        form.instance.aliquotas = aliquota_vigente
        return super().form_valid(form)
 
class NotaFiscalUpdateView(UpdateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/editar_nota_fiscal.html'

    def get_success_url(self):
        # Preservar TODOS os filtros originais da busca (vindos da tela de lista)
        params = []
        
        # Preserva todos os parâmetros GET que vieram da tela de lista
        for key, value in self.request.GET.items():
            if value:
                params.append(f'{key}={value}')
        
        url = reverse('medicos:lista_notas_fiscais')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Nota Fiscal'
        context['cenario_nome'] = 'Faturamento'
        
        # Empresa sempre existe
        empresa = empresa_context(self.request)['empresa']
        dt_emissao = self.object.dtEmissao if hasattr(self.object, 'dtEmissao') else None
        
        # Obter alíquota vigente
        aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa, dt_emissao) if dt_emissao else Aliquotas.obter_aliquota_vigente(empresa)
        
        # Definir alíquotas no contexto
        if aliquota_vigente:
            context.update({
                'aliquota_ISS': getattr(aliquota_vigente, 'ISS', 0),
                'aliquota_PIS': getattr(aliquota_vigente, 'PIS', 0),
                'aliquota_COFINS': getattr(aliquota_vigente, 'COFINS', 0),
                'aliquota_IR': getattr(aliquota_vigente, 'IRPJ_RETENCAO_FONTE', 0),
                'aliquota_CSLL': getattr(aliquota_vigente, 'CSLL_RETENCAO_FONTE', 0),
            })
        else:
            context.update({
                'aliquota_ISS': 0,
                'aliquota_PIS': 0,
                'aliquota_COFINS': 0,
                'aliquota_IR': 0,
                'aliquota_CSLL': 0,
            })
            
        context.update({
            'campos_topo': [
                'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
            ],
            'campos_excluir': [
                'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
            ]
        })
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Empresa sempre existe
        empresa = empresa_context(self.request)['empresa']
        form.empresa_sessao = empresa
        
        # Verificar se existe recebimento para configurar campos readonly
        if self.object and self.object.dtRecebimento:
            form.has_recebimento = True
        return form

    def form_valid(self, form):
        # Salvar sem recalcular impostos automaticamente (preserva valores editados manualmente)
        return super().form_valid(form)

class NotaFiscalDeleteView(DeleteView):
    model = NotaFiscal
    template_name = 'faturamento/excluir_nota_fiscal.html'

    def delete(self, request, *args, **kwargs):
        """
        Override do método delete para adicionar logging e verificações antes da exclusão
        """
        import logging
        logger = logging.getLogger('medicos.views_faturamento')
        
        self.object = self.get_object()
        
        # Log das movimentações financeiras antes da exclusão
        movimentacoes_count = self.object.lancamentos_financeiros.count()
        rateios_count = self.object.rateios_medicos.count()
        
        logger.info(f"Excluindo Nota Fiscal {self.object.numero} (ID: {self.object.id})")
        logger.info(f"Movimentações financeiras associadas: {movimentacoes_count}")
        logger.info(f"Rateios associados: {rateios_count}")
        
        # Executa a exclusão (signals serão disparados automaticamente)
        result = super().delete(request, *args, **kwargs)
        
        logger.info(f"Nota Fiscal {self.object.numero} excluída com sucesso")
        logger.info("Signals post_delete foram disparados automaticamente para limpeza")
        
        return result

    def get_success_url(self):
        # Preservar TODOS os filtros originais da busca (vindos da tela de lista)
        params = []
        
        # Preserva todos os parâmetros GET que vieram da tela de lista
        for key, value in self.request.GET.items():
            if value:
                params.append(f'{key}={value}')
        
        url = reverse('medicos:lista_notas_fiscais')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

@method_decorator(login_required, name='dispatch')
class NotaFiscalListView(SingleTableMixin, FilterView):
    model = NotaFiscal
    table_class = NotaFiscalListaTable
    filterset_class = NotaFiscalFilter
    template_name = 'faturamento/lista_notas_fiscais.html'
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        import datetime
        # Empresa sempre existe
        empresa_id = self.request.session['empresa_id']
        qs = NotaFiscal.objects.filter(empresa_destinataria__id=int(empresa_id)).order_by('-dtEmissao')
        
        # Filtrar por mês/ano de emissão
        mes_ano_emissao = self.request.GET.get('mes_ano_emissao')
        if not mes_ano_emissao:
            now = datetime.date.today()
            ano = now.year
            mes = now.month
            qs = qs.filter(dtEmissao__year=ano, dtEmissao__month=mes)
        else:
            try:
                ano, mes = mes_ano_emissao.split('-')
                qs = qs.filter(dtEmissao__year=int(ano), dtEmissao__month=int(mes))
            except Exception:
                pass
        return qs

    def get_context_data(self, **kwargs):
        import datetime
        from django.db.models import Sum
        context = super().get_context_data(**kwargs)
        mes_ano_emissao = self.request.GET.get('mes_ano_emissao')
        if not mes_ano_emissao:
            now = datetime.date.today()
            mes_ano_emissao = f"{now.year:04d}-{now.month:02d}"
        
        # Calcular totalizações usando o queryset filtrado do filterset
        # Isso garante que os totais reflitam exatamente os registros exibidos na tabela
        # EXCLUINDO notas fiscais canceladas da totalização
        if hasattr(self, 'filterset') and self.filterset is not None:
            queryset_filtrado = self.filterset.qs.exclude(status_recebimento='cancelado')
        else:
            queryset_filtrado = self.get_queryset().exclude(status_recebimento='cancelado')
            
        totais = queryset_filtrado.aggregate(
            total_bruto=Sum('val_bruto'),
            total_iss=Sum('val_ISS'),
            total_pis=Sum('val_PIS'),
            total_cofins=Sum('val_COFINS'),
            total_ir=Sum('val_IR'),
            total_csll=Sum('val_CSLL'),
            total_outros=Sum('val_outros'),
            total_liquido=Sum('val_liquido')
        )
        
        # Contar notas canceladas para informação adicional
        if hasattr(self, 'filterset') and self.filterset is not None:
            queryset_base = self.filterset.qs
        else:
            queryset_base = self.get_queryset()
            
        total_notas = queryset_base.count()
        notas_canceladas = queryset_base.filter(status_recebimento='cancelado').count()
        notas_validas = total_notas - notas_canceladas
        
        # Garantir que valores None sejam convertidos para 0
        for key, value in totais.items():
            if value is None:
                totais[key] = 0
        
        context.update({
            'titulo_pagina': 'Lista de notas fiscais',
            'menu_nome': 'Notas Fiscais',
            'mes_ano': self.request.session.get('mes_ano'),
            'mes_ano_emissao_default': mes_ano_emissao,
            'totais': totais,
            'total_notas': total_notas,
            'notas_canceladas': notas_canceladas,
            'notas_validas': notas_validas,
            # Variáveis de filtro para a tabela (seguindo padrão das despesas)
            'mes_ano_emissao': self.request.GET.get('mes_ano_emissao'),
            'status_recebimento': self.request.GET.get('status_recebimento')
        })
        context['cenario_nome'] = 'Faturamento'
        return context
