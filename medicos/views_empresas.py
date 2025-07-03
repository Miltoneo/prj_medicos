from django.http import HttpResponse, FileResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from .models import *
from .data import *
from .forms import *
import datetime

# django tables
from django.views import generic
from django.views.generic import ListView, TemplateView
from django_tables2 import SingleTableView, LazyPaginator
from .tables import *

import locale
locale.setlocale(locale.LC_ALL,'')

#----------------------------------------------------------
def empresas_main(request):
    return redirect('medicos:Empresas_View')

#---------------------------------------------------------
class Empresas_View(SingleTableView):

    model = Empresa
    table_class = Empresa_Table
    context_object_name = 'empresa_list'
    template_name = 'main/index.html'
    paginate_by = 50    
    paginator_class = LazyPaginator

    def get_context_data(self, **kwargs):
        context = super(Empresas_View, self).get_context_data(**kwargs)
        context['some_data'] = 'This is just some data'

        # cabeçalho da página
        self.request.session['titulo_1'] = 'Empresas Cadastradas'  
        self.request.session['titulo_2'] = 'Página Inicial' 

        return context

    def get_queryset(self):
        return Empresa.objects.all().order_by('name')
