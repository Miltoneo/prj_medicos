from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.conf import settings
from django.contrib import messages
from .models import *
from .data import *
from .forms import *
import json
from django.db.models import Max, Subquery
from django.forms import formset_factory, modelform_factory, modelformset_factory

# django tables
from django.views.generic import ListView
from django_tables2 import SingleTableView, LazyPaginator
from .tables import *

import locale
locale.setlocale(locale.LC_ALL,'')


#------------------------------------------------------
def despesas(request):
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal']

  fornecedor = Empresa.objects.get(id = empresa_id)

  template = loader.get_template('despesas/despesas.html')
  context = {
              'empresa'           : fornecedor.name,
              'periodo_fiscal'     : periodo_fiscal,
              'msg'               : msg,

              'user'              : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------
def despesa_coletiva(request, mes):
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal'] + '-01'

  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  empresa = Empresa.objects.get(id = empresa_id)
  qry_despesas = Despesa.objects.filter(data__year = periodo_fiscal.year, data__month = periodo_fiscal.month, empresa = empresa_id, tipo_rateio = TIPO_DESPESA_COM_RATEIO) \
                                                                    .order_by('item__grupo__codigo','item__codigo') 
                                                                                              
  template = loader.get_template('despesas/despesa_coletiva/despesa_coletiva.html')
  context = {
              'empresa'           : empresa,
              'mes'               : mes,
              'periodo_fiscal'    : periodo_fiscal,
              'lst_despesas'      : qry_despesas,
              'msg'               : msg,
              'user'              : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#---------------------------------------------------------------------
def despesa_incluir(request):
  
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'

  fornecedor = Empresa.objects.get(id = empresa_id)

  if request.method == 'POST':
    form = Despesa_Form(request.POST)
    if form.is_valid():

      # insere data formata
      despesa = form.save(commit = False) 
      despesa.empresa = fornecedor    
      despesa.tipo_rateio = TIPO_DESPESA_COM_RATEIO 
      despesa.save()

      # CORRIGIDO: campo empresa
      qry_socios = Socio.objects.filter(empresa = empresa_id)
      for socio in qry_socios:
          ds_socio= Despesa_socio_rateio.objects.create(
              fornecedor= fornecedor,   
              socio=socio, 
              despesa = despesa,                                                   
          )
          ds_socio.save()

      request.session['msg_status'] = 'Item incluído com sucesso!!!'
      return redirect('medicos:Despesas_TableView')    
    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:Despesas_TableView')   
    
  else:

    lst_item = Despesa_Item.objects.filter(grupo__tipo_rateio = GRUPO_ITEM_COM_RATEIO).order_by('grupo__codigo','codigo')      

    item_initial = []
    for item in lst_item:
        item_initial.append([item.pk, item])


    # Título da aba da página
    request.session['title_page'] = 'Faturamento'
    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Despesa Coletiva' 
    request.session['titulo_3'] = 'Incluir/Editar' 

    form = Despesa_Form(initial={'data': periodo_fiscal})
    template = loader.get_template('despesas/despesa_coletiva/despesa_incluir.html')
    context = {
                'empresa'     : fornecedor.name,
                'periodo_fiscal'  : periodo_fiscal,
                'form'        : form,
                'msg'         : msg,
                'tipo_operacao'     : 'Inclusão de despesa',
                'user'        : request.user,
              }
  
    return HttpResponse(template.render(context, request))

#---------------------------------------------------------------------
def despesa_copiar(request):
  
  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  # copia despesas coletivas do mes anterior inclusive o rateio para os socios 
  clonar_despesa_mes_anterior(request, periodo_fiscal)

  request.session['msg_status'] = 'Despesas copiadas com sucesso!!!'
  return redirect('medicos:Despesas_TableView')   
  
#-------------------------------------------------------------
def despesa_coletiva_editar(request,despesa_id):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()


  fornecedor = Empresa.objects.get(id = empresa_id)

  ds_despesa = Despesa.objects.get(id = despesa_id)
  if request.method == 'POST':
    
    form = Despesa_Form(request.POST, instance = ds_despesa)
    if form.is_valid():

      # insere data formata
      despesa = form.save() 
      request.session['msg_status'] = 'Item incluído com sucesso!!!'
      return redirect('medicos:Despesas_TableView')    
    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:Despesas_TableView')   
    
  else:

    lst_item = Despesa_Item.objects.filter(grupo__tipo_rateio = GRUPO_ITEM_COM_RATEIO).order_by('grupo__codigo','codigo')      
    
    item_initial = []
    for item in lst_item:
      item_initial.append([item.pk, item])

    # Título da aba da página
    request.session['title_page'] = 'Despesa Coletiva'
    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Despesa' 
    request.session['titulo_3'] = 'Editar' 
      
    data_inicial = ds_despesa.data.isoformat()
    form = Despesa_Form( instance = ds_despesa, initial={'data': data_inicial})
    template = loader.get_template('despesas/despesa_coletiva/despesa_incluir.html')
    context = {
                'empresa'     : fornecedor,
                'periodo_fiscal'  : periodo_fiscal,
                'form'        : form,
                'msg'         : msg,
                'user'        : request.user,
              }
  
    return HttpResponse(template.render(context, request))

#-----------------------------------------------
def despesa_excluir(request,id):
  
  qry_despesa = Despesa.objects.get(id = id)
  qry_despesa.delete()
  request.session['msg_status'] = 'Item excluido com sucesso!!!'

  return redirect('medicos:Despesas_TableView')    

#-----------------------------------------------
def despesa_detalhe_grupo(request,item):

  msg =  request.session['msg_status']  
  empresa_id = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  empresa_nome = Empresa.objects.get(id = empresa_id).name
  qry_despesas = Despesa.objects.filter(item = item, empresa= empresa_id, data__year= periodo_fiscal.year, data__month = periodo_fiscal.month)

  template = loader.get_template('despesas/despesa_coletiva.html')
  context = {
              'empresa_nome'      : empresa_nome,
              'lst_despesas'      : qry_despesas,
              'user'              : request.user,
              'msg'               : msg,
              'tipo_operacao'     : 'Despesas cadastradas',
            }
  
  return HttpResponse(template.render(context, request))

#---------------------------------------------
def despesa_rateio(request, mes):
  
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal']

  fornecedor = Empresa.objects.get(id = empresa_id)

  lst_socios = Socio.objects.filter(empresa=empresa_id ).order_by('socio__pessoa__name')

  template = loader.get_template('despesas/despesa_coletiva/despesa_rateio.html')
  context = {
              'empresa'           : fornecedor.name,
              'periodo_fiscal'    : periodo_fiscal,
              'lst_socios'        : lst_socios,
              'msg'               : msg,
              'tipo_operacao'     : ' ',
              'user'              : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------
# socio = socio_id
def despesa_rateio_socio(request, socio_id):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  fornecedor = Empresa.objects.get(id = empresa_id)
  socio = Socio.objects.get(id = socio_id)

  ds_despesas = Despesa_socio_rateio.objects.filter(despesa__data__year = periodo_fiscal.year, despesa__data__month=periodo_fiscal.month, socio = socio )

  myModelFormset = modelformset_factory(Despesa_socio_rateio, form=Despesa_socio_rateio_Form, extra=0 )
  FormsetInstance = myModelFormset(queryset=ds_despesas)
  
  if request.method == 'POST':
    
    if request.POST.get("form_type") =='getdata':  
      periodo_fiscal = request.POST.get("mytext")
      request.session['periodo_fiscal'] = periodo_fiscal
      return redirect('medicos:despesa_rateio_socio', socio_id=socio_id)
    
    else:
      formset = myModelFormset(request.POST, request.FILES )
      if formset.is_valid():
        for form in formset:
          if form.has_changed():
              form.save()

        request.session['msg_status'] = 'Item incluído com sucesso!!!'
        return redirect('medicos:despesa_rateio_socio', socio_id=socio_id )    
      else:
        request.session['msg_status'] = 'Falha na validadação dos dados'
        return redirect('medicos:despesa_rateio_socio', socio_id=socio_id )   
    
  else:

    # Título da aba da página
    request.session['title_page'] = 'Despesa Sócio'
    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Despesa Sócio' 
    request.session['titulo_3'] = 'Principal' 

    template = loader.get_template('despesas/despesa_coletiva/despesa_rateio_socio.html')
    context = {
                'empresa'     : fornecedor,
                'periodo_fiscal'         : periodo_fiscal,
                'socio'       : socio,
                'formset'     : FormsetInstance,
                'msg'         : msg,
                'user'        : request.user,
              }
  
    return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def despesa_socio(request):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  # formata data inicial
  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  fornecedor = Empresa.objects.get(id=empresa_id)
  lst_socios = Socio.objects.filter(empresa = fornecedor).order_by('pessoa__name')

  # Título da aba da página
  request.session['title_page'] = 'Despesa Sócio'
  # cabeçalha da página
  request.session['titulo_1'] = fornecedor.name
  request.session['titulo_2'] = 'Despesa Sócio' 
  request.session['titulo_3'] = 'Visão Geral' 

  template = loader.get_template('despesas/despesa_socio/despesa_socio.html')
  context = {
              'empresa'           : fornecedor,
              'periodo_fiscal'    : periodo_fiscal,
              'lst_socios'        : lst_socios,
              'msg'             : msg,
              'user'            : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#-----------------------------------------------------------------------------
def despesa_socio_detail(request, socio_id):
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  if request.method == 'POST':
    if request.POST.get("form_type") =='getdata':  
      periodo_fiscal = request.POST.get("mytext")
      request.session['periodo_fiscal'] = periodo_fiscal

      return redirect('medicos:despesa_socio_detail', socio_id=socio_id)
  else:
    
    fornecedor = Empresa.objects.get(id = empresa_id) 
    socio = Socio.objects.get(id = socio_id)
    lst_despesas = Despesa.objects.filter(data__year = periodo_fiscal.year, data__month = periodo_fiscal.month, empresa = fornecedor , socio = socio  )

  # cabeçalha da página
  request.session['titulo_1'] = 'Despesa Sócio'  
  request.session['titulo_2'] = 'Sócio: ' +  socio.pessoa.name
    
  template = loader.get_template('despesas/despesa_socio/despesa_socio_detail.html')
  context = {
                'periodo_fiscal'    : periodo_fiscal,
                'empresa'       : fornecedor.name,
                'socio'         : socio,
                'lst_despesas'  : lst_despesas,
                'msg'           : msg,
                'user'          : request.user
              }
  return HttpResponse(template.render(context, request))

#---------------------------------------------------------------------
def despesa_socio_incluir(request, socio_id):
  
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  #periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  data_inicial = periodo_fiscal

  fornecedor = Empresa.objects.get(id = empresa_id)
  socio = Socio.objects.get(id=socio_id)

  # monta data para salva item: YYYY-MM-DD 
  #data_inicial = periodo_fiscal

  if request.method == 'POST':
    
    form = Despesa_Form(request.POST)
    if form.is_valid():

      # insere data formata
      despesa = form.save(commit = False) 
      despesa.empresa = fornecedor   
      despesa.socio   = socio
      #despesa.data    = date_input
      despesa.tipo_rateio = TIPO_DESPESA_SEM_RATEIO 
      despesa.save()

      request.session['msg_status'] = 'Item incluído com sucesso!!!'
      return redirect('medicos:Despesas_Socio_View', socio_id=socio.id)
    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:Despesas_Socio_View', socio_id=socio.id)
    
  else:

    ##fornecedor_initial = []
    #fornecedor_initial.append([fornecedor.pk, fornecedor.name])

    lst_item = Despesa_Item.objects.filter(grupo__tipo_rateio = GRUPO_ITEM_SEM_RATEIO).order_by('grupo__codigo','codigo')  

    item_initial = []
    for item in lst_item:
      item_initial.append([item.pk, item])

    # Título da aba da página
    request.session['title_page'] = 'Despesa Sócio Incluir 123'
    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Despesa Sócio Incluir' 
    request.session['titulo_3'] = 'Sócio: ' + socio.pessoa.name

    form = Despesa_Form(initial={'data': data_inicial})
    template = loader.get_template('despesas/despesa_socio/despesa_socio_incluir.html')
    context = {
                'empresa'     : fornecedor,
                'periodo_fiscal'         : periodo_fiscal,
                'socio'       : socio,
                'form'        : form,
                'msg'         : msg,
                'user'        : request.user,
              }
  
    return HttpResponse(template.render(context, request))

#-------------------------------------------------------------
def despesa_socio_editar(request, despesa_id):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal']

  fornecedor = Empresa.objects.get(id = empresa_id)
  socio = Despesa.objects.get(id=despesa_id).socio

  ds_despesa = Despesa.objects.get(id = despesa_id)
  if request.method == 'POST':
    
    form = Despesa_Form(request.POST, instance = ds_despesa)
    if form.is_valid():

      # insere data formata
      despesa = form.save() 
      request.session['msg_status'] = 'Item incluído com sucesso!!!'
      return redirect('medicos:Despesas_Socio_View', socio_id=socio.id) 
     
    else:

        request.session['msg_status'] = 'Falha na validadação dos dados'
        return redirect('medicos:Despesas_Socio_View', socio_id=socio.id)
      
  else:

    lst_item = Despesa_Item.objects.filter(grupo__tipo_rateio = TIPO_DESPESA_SEM_RATEIO).order_by('grupo__codigo','codigo')      
    
    item_initial = []
    for item in lst_item:
      item_initial.append([item.pk, item])
                                               
    # Título da aba da página
    request.session['title_page'] = 'Despesas de sócio'
    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Despesas de Sócio' 
    request.session['titulo_3'] = 'Sócio: ' + socio.pessoa.name
		
    data_inicial = ds_despesa.data.isoformat()
    form = Despesa_Form( instance = ds_despesa, initial={'data': data_inicial})
    template = loader.get_template('despesas/despesa_socio/despesa_socio_incluir.html')
    context = {
                'empresa'     : fornecedor,
                'periodo_fiscal'  : periodo_fiscal,
                'form'        : form,
                'msg'         : msg,
                'user'        : request.user,
              }
  
    return HttpResponse(template.render(context, request))

#-----------------------------------------------
def despesa_socio_excluir(request, despesa_id, socio_id):
  
  msg =  request.session['msg_status']
  id_empresa = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  socio = Socio.objects.get(id=socio_id)

  qry_despesa = Despesa.objects.get(id=despesa_id, empresa=id_empresa, socio = socio, data__month=periodo_fiscal.month, data__year=periodo_fiscal.year )
  qry_despesa.delete()
  #messages.success(request, 'Item excluído com Sucesso!')
  request.session['msg_status'] = 'Item incluído com sucesso!!!'

  return redirect('medicos:Despesas_Socio_View', socio_id=socio.id)

#-----------------------------------------------
class Despesas_TableView(SingleTableView):

    model = Despesa
    table_class = Despesas_Table
    template_name = 'despesas/despesa_coletiva/despesa_coletiva.html'
    paginate_by = 20   
    paginator_class = LazyPaginator

    #testing
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fornecedor_id = self.request.session['empresa_id'] 
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # CORRIGIDO
        
        context["periodo_fiscal"] = self.request.session['periodo_fiscal'] 
        context["empresa"] = fornecedor
        context["msg"] = self.request.session['msg_status']

        # Título da aba da página
        self.request.session['title_page'] = 'Despesas Coletiva'
        # cabeçalha da página
        self.request.session['titulo_1'] =  fornecedor.name
        self.request.session['titulo_2'] = 'Despesas de Coletiva'
        self.request.session['titulo_3'] = 'Principal' 
		

        return context

    def get_table_data(self):
        fornecedor_id = self.request.session['empresa_id']
        periodo_fiscal=  self.request.session['periodo_fiscal'] + '-01'
        periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # CORRIGIDO
        queryset = Despesa.objects.filter(
            data__year = periodo_fiscal.year,
            data__month = periodo_fiscal.month,
            empresa = fornecedor,
            tipo_rateio = TIPO_DESPESA_COM_RATEIO
        ).order_by('item__grupo__codigo','item__codigo')
        return queryset

    def post(self, request, **kwargs):
        fornecedor_id = self.request.session['empresa_id']
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # CORRIGIDO

        if request.method == 'POST':

          if request.POST.get("form_type") =='getdata':  
            periodo_fiscal = request.POST.get("mytext")
            request.session['periodo_fiscal'] = periodo_fiscal

            return redirect('medicos:Despesas_TableView')
          else:   
            notafiscal = importar_xml(request, fornecedor)
            return redirect('medicos:Despesas_TableView') 

#-----------------------------------------------
class Despesas_Socio_View(SingleTableView):

    model = Despesa
    table_class = Despesas_Socio_Table
    template_name = 'despesas/despesa_socio/despesa_socio_detail.html'
    paginate_by = 50   
    paginator_class = LazyPaginator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        socio_id = self.kwargs['socio_id']
        socio = Socio.objects.get(id = socio_id)

        empresa_id = self.request.session['empresa_id'] 
        empresa = Empresa.objects.get(id=empresa_id)  # CORRIGIDO

        context["periodo_fiscal"] = self.request.session['periodo_fiscal'] 
        context["empresa"] = empresa
        context["socio"] = socio
        context["msg"] = self.request.session['msg_status']

        # Título da aba da página
        self.request.session['title_page'] = 'Despesas Sócio'
        # cabeçalha da página
        self.request.session['titulo_1'] =  empresa.name
        self.request.session['titulo_2'] = 'Despesas de Sócio'
        self.request.session['titulo_3'] = 'Sócio: ' + socio.pessoa.name 

        return context

    def get_queryset(self):

        periodo_fiscal=  self.request.session['periodo_fiscal'] + '-01'
        periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
  
        socio_id = self.kwargs['socio_id']
        socio = Socio.objects.get(id = socio_id)

        queryset = Despesa.objects.filter(data__year = periodo_fiscal.year, data__month = periodo_fiscal.month, socio = socio  )

        return queryset

    def post(self, request, **kwargs):
      
      socio_id = self.kwargs['socio_id']
      
      if request.method == 'POST':

        if request.POST.get("form_type") =='getdata':  
          periodo_fiscal = request.POST.get("mytext")
          request.session['periodo_fiscal'] = periodo_fiscal

          return redirect('medicos:Despesas_Socio_View', socio_id=socio_id)

