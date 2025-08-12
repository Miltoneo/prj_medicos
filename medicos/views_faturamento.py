from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

# Django imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator

# Third-party imports
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from medicos.models.fiscal import NotaFiscal, Aliquotas
from .tables_notafiscal_lista import NotaFiscalListaTable
from .filters_notafiscal import NotaFiscalFilter
from medicos.models.base import Empresa
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
        # Use empresa do context processor
        empresa = empresa_context(self.request).get('empresa')
        aliquota_vigente = None
        if empresa:
            aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa)
            context.update({
                'aliquota_ISS': getattr(aliquota_vigente, 'ISS', 0) if aliquota_vigente else 0,
                'aliquota_PIS': getattr(aliquota_vigente, 'PIS', 0) if aliquota_vigente else 0,
                'aliquota_COFINS': getattr(aliquota_vigente, 'COFINS', 0) if aliquota_vigente else 0,
                'aliquota_IR_BASE': getattr(aliquota_vigente, 'IRPJ_ALIQUOTA', 0) if aliquota_vigente else 0,
                'aliquota_IR': getattr(aliquota_vigente, 'IRPJ_PRESUNCAO_OUTROS', 0) if aliquota_vigente else 0,
                'aliquota_CSLL_BASE': getattr(aliquota_vigente, 'CSLL_PRESUNCAO_OUTROS', 0) if aliquota_vigente else 0,
                'aliquota_CSLL': getattr(aliquota_vigente, 'CSLL_ALIQUOTA', 0) if aliquota_vigente else 0,
                'campos_topo': [
                    'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
                ],
                'campos_excluir': [
                    'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento', 'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
                ]
            })
            dt_emissao = self.request.POST.get('dtEmissao') or self.request.GET.get('dtEmissao')
            if dt_emissao:
                aliquota_para_data = Aliquotas.obter_aliquota_vigente(empresa, dt_emissao)
                if not aliquota_para_data:
                    context['erro_aliquota'] = 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.'
                    context['aliquota_vigente'] = False
                else:
                    context.update({
                        'aliquota_ISS': getattr(aliquota_para_data, 'ISS', 0),
                        'aliquota_PIS': getattr(aliquota_para_data, 'PIS', 0),
                        'aliquota_COFINS': getattr(aliquota_para_data, 'COFINS', 0),
                        'aliquota_IR_BASE': getattr(aliquota_para_data, 'IRPJ_ALIQUOTA', 0),
                        'aliquota_IR': getattr(aliquota_para_data, 'IRPJ_PRESUNCAO_OUTROS', 0),
                        'aliquota_CSLL_BASE': getattr(aliquota_para_data, 'CSLL_PRESUNCAO_OUTROS', 0),
                        'aliquota_CSLL': getattr(aliquota_para_data, 'CSLL_ALIQUOTA', 0),
                    })
        else:
            context.update({
                'aliquota_ISS': 0,
                'aliquota_PIS': 0,
                'aliquota_COFINS': 0,
                'aliquota_IR_BASE': 0,
                'aliquota_IR': 0,
                'aliquota_CSLL_BASE': 0,
                'aliquota_CSLL': 0,
            })
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Passar empresa para o formulário para filtrar meio de pagamento
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            form.empresa_sessao = empresa
        return form

    def form_valid(self, form):
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            form.add_error(None, 'Nenhuma empresa selecionada. Selecione uma empresa antes de continuar.')
            return self.form_invalid(form)
        form.instance.empresa_destinataria = empresa
        dt_emissao = form.cleaned_data.get('dtEmissao')
        aliquota_vigente = None
        if empresa:
            if dt_emissao:
                aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa, dt_emissao)
            if not aliquota_vigente:
                aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa)
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
        empresa = empresa_context(self.request).get('empresa')  # Usar empresa do context processor
        aliquota_vigente = None
        dt_emissao = self.object.dtEmissao if hasattr(self.object, 'dtEmissao') else None
        if empresa:
            if dt_emissao:
                aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa, dt_emissao)
            if not aliquota_vigente:
                aliquota_vigente = Aliquotas.obter_aliquota_vigente(empresa)
        if aliquota_vigente:
            context.update({
                'aliquota_ISS': getattr(aliquota_vigente, 'ISS', 0),
                'aliquota_PIS': getattr(aliquota_vigente, 'PIS', 0),
                'aliquota_COFINS': getattr(aliquota_vigente, 'COFINS', 0),
                'aliquota_IR_BASE': getattr(aliquota_vigente, 'IRPJ_ALIQUOTA', 0),
                'aliquota_IR': getattr(aliquota_vigente, 'IRPJ_PRESUNCAO_OUTROS', 0),
                'aliquota_CSLL_BASE': getattr(aliquota_vigente, 'CSLL_PRESUNCAO_OUTROS', 0),
                'aliquota_CSLL': getattr(aliquota_vigente, 'CSLL_ALIQUOTA', 0),
            })
        else:
            # Definir alíquotas zeradas se não houver alíquota vigente
            context.update({
                'aliquota_ISS': 0,
                'aliquota_PIS': 0,
                'aliquota_COFINS': 0,
                'aliquota_IR_BASE': 0,
                'aliquota_IR': 0,
                'aliquota_CSLL_BASE': 0,
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
        # Passar empresa para o formulário para filtrar meio de pagamento
        empresa = empresa_context(self.request).get('empresa')
        if empresa:
            form.empresa_sessao = empresa
        return form

class NotaFiscalDeleteView(DeleteView):
    model = NotaFiscal
    template_name = 'faturamento/excluir_nota_fiscal.html'

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
        # Não injeta empresa manualmente
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
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return NotaFiscal.objects.none()
        qs = NotaFiscal.objects.filter(empresa_destinataria__id=int(empresa_id)).order_by('-dtEmissao')
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
        # Não injeta empresa manualmente
        return context
