from django.http import HttpResponse, FileResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from .models import *
from .data import *
from .forms import *
import json
import datetime

# django tables
from django.views.generic import ListView
from django_tables2 import SingleTableView, LazyPaginator
from .tables import *

import locale
locale.setlocale(locale.LC_ALL,'')


#----------------------------------------------------------
def aplicacoes_mes(request, id):
    msg =  request.session['msg_status']
    empresa_id = request.session['empresa_id']

    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    fornecedor = Empresa.objects.get(id=empresa_id)  # Corrigido
    rendimentos = Aplic_financeiras.objects.get(id=id)

    rendimentos.data
    data_inicial = str(rendimentos.data)

    if request.method == 'POST':

        form = Rendimentos(request.POST, instance = rendimentos)

        if form.is_valid():
            request.session['msg_status'] = 'Dados salvos com sucesso!'
            form.save()

            return redirect('medicos:Aplic_financeiras_TableView')    

        else:
            request.session['msg_status'] = 'Falha na validadação dos dados'
            return redirect('medicos:Aplic_financeiras_TableView')   
    
    else:

        form = Rendimentos(instance = rendimentos, data_inicial = data_inicial)

        template = loader.get_template('aplicacoes/aplicacoes_mes.html')
        context = {
                    'empresa'     : fornecedor,
                    'periodo_fiscal'  : periodo_fiscal,
                    'form'        : form,
                    'msg'         : msg,
                    'user'        : request.user,
                  }
        
        return HttpResponse(template.render(context, request))
  
#----------------------------------------------------------
# APLICACOES FINANCEIRAS
#---------------------------------------------------------

class Aplic_financeiras_TableView(SingleTableView):
    model = Aplic_financeiras
    table_class = Aplic_fincanceiras_table
    template_name = 'aplicacoes/aplicacoes_main.html'
    paginate_by = 15    
    paginator_class = LazyPaginator

    def get_context_data(self):
        context = super().get_context_data()
        fornecedor_id = self.request.session['empresa_id'] 
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

        periodo_fiscal = self.request.session['periodo_fiscal']
        context["periodo_fiscal"] = periodo_fiscal
        context["empresa"] = fornecedor
        context["msg"] = self.request.session['msg_status']

        # cabeçalho da página
        self.request.session['titulo_1'] = fornecedor.name
        self.request.session['titulo_2'] = 'Aplicações Financeiras'
        self.request.session['titulo_3'] = 'Visão Geral'

        return context

    def get_table_data(self):
        fornecedor_id = self.request.session['empresa_id'] 
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

        periodo_fiscal = self.request.session['periodo_fiscal'] + '-01'
        periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
        # monta tabela de aplicações

        for mes in range(1,13):
          data = get_data_new(periodo_fiscal.year,mes)  
          Aplic_financeiras.objects.get_or_create(
                                                  data = data,
                                                  fornecedor = fornecedor,
                                                  )
          
        queryset = Aplic_financeiras.objects.filter(data__year= periodo_fiscal.year, 
                                                    fornecedor = fornecedor,
                                                    ).order_by('data')

        return queryset
