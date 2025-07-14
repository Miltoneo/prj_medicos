

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

# Local imports
from medicos.models.fiscal import NotaFiscal, Aliquotas
from .tables_notafiscal_lista import NotaFiscalListaTable
from .filters_notafiscal import NotaFiscalFilter
from medicos.models.base import Empresa
from .forms_notafiscal import NotaFiscalForm

class NotaFiscalCreateView(CreateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/criar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.request.session.get('empresa_id')
        if empresa_id:
            empresa = Empresa.objects.get(id=int(empresa_id))
            conta = getattr(empresa, 'conta', None)
            aliquota_vigente = None
            dt_emissao = self.request.POST.get('dtEmissao') or self.request.GET.get('dtEmissao')
            if conta:
                if dt_emissao:
                    aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta, dt_emissao)
                if not aliquota_vigente:
                    aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta)
            if not aliquota_vigente:
                context['erro_aliquota'] = 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.'
                context['aliquota_vigente'] = False
            else:
                context.update({
                    'empresa': empresa,
                    'aliquota_ISS': getattr(aliquota_vigente, 'ISS', 0),
                    'aliquota_PIS': getattr(aliquota_vigente, 'PIS', 0),
                    'aliquota_COFINS': getattr(aliquota_vigente, 'COFINS', 0),
                    'aliquota_IR_BASE': getattr(aliquota_vigente, 'IRPJ_BASE_CAL', 0),
                    'aliquota_IR': getattr(aliquota_vigente, 'IRPJ_ALIQUOTA_OUTROS', 0),
                    'aliquota_CSLL_BASE': getattr(aliquota_vigente, 'CSLL_BASE_CAL', 0),
                    'aliquota_CSLL': getattr(aliquota_vigente, 'CSLL_ALIQUOTA_OUTROS', 0),
                    'campos_topo': [
                        'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
                    ],
                    'campos_excluir': [
                        'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento', 'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
                    ]
                })
        return context

    def get_form(self, form_class=None):
        return super().get_form(form_class)

    def form_valid(self, form):
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            form.add_error(None, 'Nenhuma empresa selecionada na sessão. Selecione uma empresa antes de continuar.')
            return self.form_invalid(form)
        empresa = Empresa.objects.get(id=int(empresa_id))
        form.instance.empresa_destinataria = empresa
        dt_emissao = form.cleaned_data.get('dtEmissao')
        conta = empresa.conta
        aliquota_vigente = None
        if conta and dt_emissao:
            aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta, dt_emissao)
        if not aliquota_vigente:
            form.add_error(None, 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.')
            return self.form_invalid(form)
        form.instance.aliquotas = aliquota_vigente
        return super().form_valid(form)
 
class NotaFiscalUpdateView(UpdateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/editar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.request.session.get('empresa_id')
        empresa = None
        aliquota_vigente = None
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=int(empresa_id))
                conta = getattr(empresa, 'conta', None)
                dt_emissao = self.object.dtEmissao if hasattr(self.object, 'dtEmissao') else None
                if conta:
                    if dt_emissao:
                        aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta, dt_emissao)
                    if not aliquota_vigente:
                        aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta)
            except Empresa.DoesNotExist:
                empresa = None
        if aliquota_vigente:
            context.update({
                'aliquota_ISS': getattr(aliquota_vigente, 'ISS', 0),
                'aliquota_PIS': getattr(aliquota_vigente, 'PIS', 0),
                'aliquota_COFINS': getattr(aliquota_vigente, 'COFINS', 0),
                'aliquota_IR_BASE': getattr(aliquota_vigente, 'IRPJ_BASE_CAL', 0),
                'aliquota_IR': getattr(aliquota_vigente, 'IRPJ_ALIQUOTA_OUTROS', 0),
                'aliquota_CSLL_BASE': getattr(aliquota_vigente, 'CSLL_BASE_CAL', 0),
                'aliquota_CSLL': getattr(aliquota_vigente, 'CSLL_ALIQUOTA_OUTROS', 0),
            })
        context.update({
            'empresa': empresa,
            'campos_topo': [
                'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
            ],
            'campos_excluir': [
                'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
            ]
        })
        return context

class NotaFiscalDeleteView(DeleteView):
    model = NotaFiscal
    template_name = 'faturamento/excluir_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.request.session.get('empresa_id')
        empresa = None
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa = None
        context.update({
            'empresa': empresa
        })
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
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return NotaFiscal.objects.none()
        return NotaFiscal.objects.filter(empresa_destinataria__id=int(empresa_id)).order_by('-dtEmissao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo_pagina': 'Entrada de Notas Fiscais',
            'menu_nome': 'Notas Fiscais',
        })
        self.request.session['cenario_nome'] = 'Faturamento'
        empresa_id = self.request.session.get('empresa_id')
        empresa = None
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa = None
        context.update({
            'empresa_id': empresa_id,
            'empresa': empresa,
            'mes_ano': self.request.session.get('mes_ano')
        })
        # Não incluir cenario_nome no contexto
        return context
