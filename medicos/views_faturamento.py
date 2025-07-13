
# Imports: Django
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# Imports: Third Party
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView


# Imports: Local
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

    def form_valid(self, form):
        # Sempre usa a empresa da sessão
        empresa_id = self.request.session.get('empresa_id')
        try:
            empresa = Empresa.objects.get(id=int(empresa_id))
        except (Empresa.DoesNotExist, TypeError, ValueError):
            empresa = None
        form.instance.empresa_destinataria = empresa
        dt_emissao = form.cleaned_data.get('dtEmissao')
        conta = empresa.conta if empresa else None
        aliquota_vigente = None
        if conta and dt_emissao:
            from medicos.models.fiscal import Aliquotas
            aliquota_vigente = Aliquotas.obter_aliquota_vigente(conta, dt_emissao)
        if not aliquota_vigente:
            form.add_error(None, 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de emitir a nota fiscal.')
            return self.form_invalid(form)
        # Preenche o campo antes de salvar
        form.instance.aliquotas = aliquota_vigente
        response = super().form_valid(form)
        # Atualiza a sessão para garantir que a lista exibida seja da empresa correta
        self.request.session['empresa_id'] = empresa.id if empresa else None
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campos_topo'] = [
            'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
        ]
        context['campos_excluir'] = [
            'numero','tipo_servico','meio_pagamento','status_recebimento','dtEmissao','dtRecebimento','dtVencimento','descricao_servicos','serie','criado_por'
        ]
        return context
 
class NotaFiscalUpdateView(UpdateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/editar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campos_topo'] = [
            'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
        ]
        context['campos_excluir'] = [
            'dtVencimento','descricao_servicos','serie','criado_por'
        ]
        return context

class NotaFiscalDeleteView(DeleteView):
    model = NotaFiscal
    template_name = 'faturamento/excluir_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')



@method_decorator(login_required, name='dispatch')
class NotaFiscalListView(SingleTableMixin, FilterView):
    model = NotaFiscal
    table_class = NotaFiscalListaTable
    filterset_class = NotaFiscalFilter
    template_name = 'faturamento/lista_notas_fiscais.html'
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.request.session.get('empresa_id')
        try:
            empresa_id = int(empresa_id)
        except (TypeError, ValueError):
            empresa_id = None
        if empresa_id:
            return NotaFiscal.objects.filter(empresa_destinataria__id=empresa_id).order_by('-dtEmissao')
        # Adiciona atributo para exibir mensagem no template
        self.sem_empresa = True
        return NotaFiscal.objects.none()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Entrada de Notas Fiscais'
        context['menu_nome'] = 'Notas Fiscais'
        context['cenario_nome'] = 'Faturamento'
        empresa_id = self.request.session.get('empresa_id')
        empresa_atual = None
        if empresa_id:
            try:
                empresa_atual = Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                empresa_atual = None
        context['empresa_atual'] = empresa_atual
        context['mes_ano'] = self.request.session.get('mes_ano')
        # Adiciona flag para template exibir mensagem se não houver empresa
        context['sem_empresa'] = getattr(self, 'sem_empresa', False)
        return context
