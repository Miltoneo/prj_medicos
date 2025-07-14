


# Django imports
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# Third-party imports
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

# Local imports
from medicos.models.fiscal import NotaFiscal
from .tables_notafiscal_lista import NotaFiscalListaTable
from .filters_notafiscal import NotaFiscalFilter
from medicos.models.base import Empresa
from .forms_notafiscal import NotaFiscalForm

class NotaFiscalCreateView(CreateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/criar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.request = self.request
        form.empresa_id_sessao = int(self.request.session.get('empresa_id'))
        return form

    def form_valid(self, form):
        empresa_id = int(self.request.session.get('empresa_id'))
        empresa = Empresa.objects.get(id=empresa_id)
        form.instance.empresa_destinataria = empresa
        dt_emissao = form.cleaned_data.get('dtEmissao')
        conta = empresa.conta
        aliquota_vigente = None
        if conta and dt_emissao:
            from medicos.models.fiscal import Aliquotas
            aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta, dt_emissao)
        if not aliquota_vigente:
            form.add_error(None, 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.')
            return self.form_invalid(form)
        form.instance.aliquotas = aliquota_vigente
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = int(self.request.session.get('empresa_id'))
        context['empresa_atual'] = Empresa.objects.get(id=empresa_id)
        context['campos_topo'] = [
            'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
        ]
        context['campos_excluir'] = [
            'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento', 'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
        ]
        return context
 
class NotaFiscalUpdateView(UpdateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/editar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = int(self.request.session.get('empresa_id'))
        context['empresa_atual'] = Empresa.objects.get(id=empresa_id)
        context['campos_topo'] = [
            'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
        ]
        context['campos_excluir'] = [
            'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
        ]
        return context

class NotaFiscalDeleteView(DeleteView):
    model = NotaFiscal
    template_name = 'faturamento/excluir_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = int(self.request.session.get('empresa_id'))
        context['empresa_atual'] = Empresa.objects.get(id=empresa_id)
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
        empresa_id = int(self.request.session.get('empresa_id'))
        return NotaFiscal.objects.filter(empresa_destinataria__id=empresa_id).order_by('-dtEmissao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Entrada de Notas Fiscais'
        context['menu_nome'] = 'Notas Fiscais'
        context['cenario_nome'] = 'Faturamento'
        empresa_id = int(self.request.session.get('empresa_id'))
        context['empresa_id'] = empresa_id
        context['empresa_atual'] = Empresa.objects.get(id=empresa_id)
        context['mes_ano'] = self.request.session.get('mes_ano')
        return context
