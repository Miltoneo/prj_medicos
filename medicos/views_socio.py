


# Imports: Standard Library
from datetime import datetime

# Imports: Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.contrib import messages

# Imports: Third Party
from django_tables2 import RequestConfig

# Imports: Local
from medicos.models.base import Empresa, Socio, Pessoa
from medicos.forms import SocioCPFForm, SocioPessoaForm, SocioForm, SocioPessoaCompletaForm
from .tables_socio_lista import SocioListaTable
from .filters_socio import SocioFilter


# Mixin para contexto/session
from django.views.generic.base import ContextMixin
class SocioContextMixin(ContextMixin):
    menu_nome = 'Cadastro de Sócios'
    cenario_nome = 'Cadastro de Sócio'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = getattr(self, 'empresa', None)
        context['empresa'] = empresa
        context['menu_nome'] = self.menu_nome
        context['cenario_nome'] = self.cenario_nome
        context['titulo_pagina'] = getattr(self, 'titulo_pagina', 'Sócios')
        return context
    def dispatch(self, request, *args, **kwargs):
        mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
        if not mes_ano:
            mes_ano = datetime.now().strftime('%Y-%m')
        request.session['mes_ano'] = mes_ano
        request.session['menu_nome'] = self.menu_nome
        request.session['cenario_nome'] = self.cenario_nome
        request.session['user_id'] = request.user.id
        return super().dispatch(request, *args, **kwargs)



from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class SocioListView(SocioContextMixin, ListView):
    model = Socio
    template_name = 'empresa/lista_socios_empresa.html'
    context_object_name = 'table'
    paginate_by = 20
    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_object_or_404(Empresa, id=self.kwargs['empresa_id'])
        return super().dispatch(request, *args, **kwargs)
    def get_queryset(self):
        socios_qs = Socio.objects.filter(empresa=self.empresa)
        self.socio_filter = SocioFilter(self.request.GET, queryset=socios_qs)
        return self.socio_filter.qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.titulo_pagina = 'Lista de Sócios'
        table = SocioListaTable(self.socio_filter.qs)
        RequestConfig(self.request, paginate={'per_page': self.paginate_by}).configure(table)
        context['table'] = table
        context['socio_filter'] = self.socio_filter
        return context




# Views

@method_decorator(login_required, name='dispatch')





class SocioCreateView(CreateView):
    model = Socio
    form_class = SocioPessoaCompletaForm
    template_name = 'empresa/socio_form.html'
    success_url = reverse_lazy('medicos:lista_socios_empresa')

    def get_context_data(self, **kwargs):
        empresa_id = self.kwargs.get('empresa_id') or self.request.session.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        context = {
            'empresa': empresa,
            'titulo_pagina': 'Cadastro de Sócio',
            'form': self.get_form(),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        empresa_id = self.kwargs.get('empresa_id') or self.request.session.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        form = self.get_form()
        if form.is_valid():
            socio = form.save(empresa=empresa)
            messages.success(request, 'Sócio cadastrado com sucesso!')
            return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id)
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class SocioUpdateView(SocioContextMixin, UpdateView):
    model = Socio
    form_class = SocioForm
    template_name = 'empresa/socio_form.html'
    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_object_or_404(Empresa, id=self.kwargs['empresa_id'])
        self.socio = get_object_or_404(Socio, id=self.kwargs['socio_id'], empresa=self.empresa)
        return super().dispatch(request, *args, **kwargs)
    def get_object(self):
        return self.socio
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Sócio'
        context['pessoa'] = self.socio.pessoa
        context['step'] = 'socio'
        context['edit_mode'] = True
        context['socio_form'] = self.get_form()  # Always pass the bound form instance
        return context
    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Sócio atualizado com sucesso!')
        return redirect('medicos:lista_socios_empresa', empresa_id=self.empresa.id)



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
