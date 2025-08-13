
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, UpdateView
from django_filters.views import FilterView
from django.views.generic.base import ContextMixin

from django_tables2 import RequestConfig, tables, A
from django.urls import reverse

from medicos.forms import SocioCPFForm, SocioForm, SocioPessoaCompletaForm
from medicos.models.base import Empresa, Pessoa, Socio
from core.context_processors import empresa_context
from .filters_socio import SocioFilter


# Import SocioListaTable from the padronized location
from .tables_socio_lista import SocioListaTable

# Mixin para contexto/session
class SocioContextMixin(ContextMixin):
    menu_nome = 'Cadastro de Sócios'
    cenario_nome = 'Cadastro de Sócios'

    def get_context_data(self, **kwargs):
        # Garante compatibilidade com CreateView, UpdateView, DetailView
        if not hasattr(self, 'object'):
            context = super().get_context_data(object=None, **kwargs)
        else:
            context = super().get_context_data(**kwargs)
        context['menu_nome'] = self.menu_nome
        context['cenario_nome'] = self.cenario_nome
        context['titulo_pagina'] = getattr(self, 'titulo_pagina', 'Sócios')
        return context

    def dispatch(self, request, *args, **kwargs):
        mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
        if not mes_ano:
            mes_ano = datetime.now().strftime('%Y-%m')

        request.session.update({
            'mes_ano': mes_ano,
            'menu_nome': self.menu_nome,
            'user_id': request.user.id,
        })
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class SocioListView(SocioContextMixin, FilterView):
    model = Socio
    filterset_class = SocioFilter
    table_class = SocioListaTable
    template_name = 'empresa/lista_socios_empresa.html'
    paginate_by = 20
    context_object_name = 'table'

    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_object_or_404(Empresa, id=self.kwargs['empresa_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Socio.objects.filter(empresa=self.empresa).order_by('pessoa__name')

    def get_table_data(self):
        queryset = self.get_queryset()
        sort = self.request.GET.get('sort')
        if sort:
            # Tradução dos campos da tabela para campos do modelo
            sort_map = {
                'nome': 'pessoa__name',
                '-nome': '-pessoa__name',
                'cpf': 'pessoa__cpf',
                '-cpf': '-pessoa__cpf',
            }
            sort_field = sort_map.get(sort, sort)
            queryset = queryset.order_by(sort_field)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.titulo_pagina = 'Lista de Sócios'
        context['socio_filter'] = context.get('filter')
        table = SocioListaTable(self.get_table_data())
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        return context




# Views

@method_decorator(login_required, name='dispatch')

class SocioCreateView(CreateView):
    def form_valid(self, form):
        empresa = empresa_context(self.request).get('empresa')
        if not empresa:
            form.add_error(None, 'Nenhuma empresa selecionada.')
            return self.form_invalid(form)
        self.object = form.save(empresa=empresa)
        messages.success(self.request, 'Sócio cadastrado com sucesso!')
        return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id)
    model = Socio
    form_class = SocioPessoaCompletaForm
    template_name = 'empresa/socio_form.html'
    success_url = reverse_lazy('medicos:lista_socios_empresa')

    def get_context_data(self, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Cadastro de Sócio'
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class SocioUpdateView(SocioContextMixin, UpdateView):
    model = Socio
    template_name = 'empresa/socio_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_object_or_404(Empresa, id=self.kwargs['empresa_id'])
        self.socio = get_object_or_404(Socio, id=self.kwargs['socio_id'], empresa=self.empresa)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.socio

    def get_form(self):
        pessoa = self.socio.pessoa
        initial = {
            'name': pessoa.name,
            'cpf': pessoa.cpf,
            'rg': pessoa.rg,
            'data_nascimento': pessoa.data_nascimento,
            'telefone': pessoa.telefone,
            'celular': pessoa.celular,
            'email': pessoa.email,
            'crm': pessoa.crm,
            'especialidade': pessoa.especialidade,
            'pessoa_ativo': pessoa.ativo,
            'socio_ativo': self.socio.ativo,
            'data_entrada': self.socio.data_entrada.strftime('%Y-%m-%d') if self.socio.data_entrada else '',
            'data_saida': self.socio.data_saida.strftime('%Y-%m-%d') if self.socio.data_saida else '',
            'observacoes': self.socio.observacoes,
        }
        if self.request.method == 'POST':
            return SocioPessoaCompletaForm(self.request.POST, initial=initial)
        return SocioPessoaCompletaForm(initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Sócio'
        context['edit_mode'] = True
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            socio = self.socio
            pessoa = socio.pessoa
            pessoa_data = {
                'name': form.cleaned_data['name'],
                'cpf': form.cleaned_data['cpf'],
                'rg': form.cleaned_data.get('rg'),
                'data_nascimento': form.cleaned_data.get('data_nascimento'),
                'telefone': form.cleaned_data.get('telefone'),
                'celular': form.cleaned_data.get('celular'),
                'email': form.cleaned_data.get('email'),
                'crm': form.cleaned_data.get('crm'),
                'especialidade': form.cleaned_data.get('especialidade'),
                'ativo': form.cleaned_data.get('pessoa_ativo', True),
            }
            for k, v in pessoa_data.items():
                setattr(pessoa, k, v)
            pessoa.save()
            socio.ativo = form.cleaned_data.get('socio_ativo', True)
            socio.data_entrada = form.cleaned_data['data_entrada']
            socio.data_saida = form.cleaned_data.get('data_saida')
            socio.observacoes = form.cleaned_data.get('observacoes', '')
            socio.save()
            messages.success(self.request, 'Sócio atualizado com sucesso!')
            return redirect('medicos:lista_socios_empresa', empresa_id=self.empresa.id)
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)



@method_decorator(login_required, name='dispatch')
class SocioDeleteView(SocioContextMixin, DeleteView):
    model = Socio
    template_name = 'empresa/socio_confirm_unlink.html'
    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_object_or_404(Empresa, id=self.kwargs['empresa_id'])
        self.socio = get_object_or_404(Socio, id=self.kwargs['socio_id'], empresa=self.empresa)
        return super().dispatch(request, *args, **kwargs)
    def get_object(self):
        return self.socio
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Desvincular Sócio'
        context['socio'] = self.socio
        return context
    def post(self, request, *args, **kwargs):
        self.socio.delete()
        messages.success(request, 'Sócio desvinculado da empresa com sucesso!')
        return redirect('medicos:lista_socios_empresa', empresa_id=self.empresa.id)
