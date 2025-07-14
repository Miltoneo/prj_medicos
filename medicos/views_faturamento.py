

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

# View movida de views_cenario.py
@login_required
def cenario_faturamento(request):
    request.session['menu_nome'] = 'Faturamento'
    request.session['cenario_nome'] = 'Faturamento'
    request.session['titulo_pagina'] = 'Notas Fiscais'
    # Assume que sempre haverá empresa selecionada
    return redirect('medicos:lista_notas_fiscais')

class NotaFiscalCreateView(CreateView):
    model = NotaFiscal
    form_class = NotaFiscalForm
    template_name = 'faturamento/criar_nota_fiscal.html'
    success_url = reverse_lazy('medicos:lista_notas_fiscais')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.request.session.get('empresa_id')
        empresa_atual = None
        if empresa_id:
            try:
                empresa_atual = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa_atual = None
        context.update({
            'empresa_atual': empresa_atual,
            'campos_topo': [
                'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento'
            ],
            'campos_excluir': [
                'numero', 'tipo_servico', 'meio_pagamento', 'status_recebimento', 'dtEmissao', 'dtRecebimento', 'dtVencimento', 'descricao_servicos', 'serie', 'criado_por'
            ]
        })
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            # Redireciona para seleção de empresa se não houver empresa_id
            raise Exception('Nenhuma empresa selecionada na sessão. Selecione uma empresa antes de continuar.')
        form.request = self.request
        form.empresa_id_sessao = int(empresa_id)
        return form

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
        empresa_atual = None
        if empresa_id:
            try:
                empresa_atual = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa_atual = None
        context.update({
            'empresa_atual': empresa_atual,
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
        empresa_atual = None
        if empresa_id:
            try:
                empresa_atual = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa_atual = None
        context.update({
            'empresa_atual': empresa_atual
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
        empresa_atual = None
        if empresa_id:
            try:
                empresa_atual = Empresa.objects.get(id=int(empresa_id))
            except Empresa.DoesNotExist:
                empresa_atual = None
        context.update({
            'empresa_id': empresa_id,
            'empresa_atual': empresa_atual,
            'mes_ano': self.request.session.get('mes_ano')
        })
        # Não incluir cenario_nome no contexto
        return context
