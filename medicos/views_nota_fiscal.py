from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.conf import settings
from django.contrib import messages
from .models import *
from .data import *
from .forms import *
from .tables import *
import json
from django.db.models import Max, Subquery

# django tables
from django.views.generic import ListView
from django_tables2 import SingleTableView, LazyPaginator, SingleTableMixin
from .tables import *
from django.http import HttpResponseNotFound
import locale

  #django filters
import django_filters  
from django.urls import path
from django_filters.views import FilterView

locale.setlocale(locale.LC_ALL,'')

#----------------------------------------------------------
def faturamento(request, fornecedor_id):
    periodo_fiscal = request.session['periodo_fiscal']
    fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido
    request.session['empresa_id'] = fornecedor.id
    return redirect('medicos:NFiscal_TableView', fornecedor_id=fornecedor_id, periodo_fiscal=periodo_fiscal)

class NFiscal_TableView(SingleTableView): 

    #model = NotaFiscal
    table_class = NFiscal_Table
    template_name = 'faturamento/faturamento.html'
    paginate_by = 15    
    paginator_class = LazyPaginator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fornecedor_id= self.kwargs['fornecedor_id']
        periodo_fiscal= self.kwargs['periodo_fiscal']
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

        context["empresa"] = fornecedor 
        context["msg"] = self.request.session['msg_status']
        context["periodo_fiscal"] = periodo_fiscal

        # Título da aba da página
        self.request.session['title_page'] = 'Faturamento'

        # cabeçalha da página
        self.request.session['titulo_1'] = fornecedor.name
        self.request.session['titulo_2'] = 'Faturamento' 
        self.request.session['titulo_3'] = 'Nostas Fiscais' 

        return context
    
    def get_queryset(self):
        fornecedor_id= self.kwargs['fornecedor_id']
        periodo_fiscal= self.kwargs['periodo_fiscal'] + '-01'
        periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

        queryset = NotaFiscal.objects.filter(dtEmissao__year=periodo_fiscal.year, dtEmissao__month=periodo_fiscal.month, fornecedor=fornecedor )\
                                            .order_by('socio__pessoa__name')

        return queryset

    def post(self, request, **kwargs):
        fornecedor_id= self.kwargs['fornecedor_id']
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

        if request.method == 'POST':

          if request.POST.get("form_type") =='getdata':  
            periodo_fiscal = request.POST.get("mytext")
            request.session['periodo_fiscal'] = periodo_fiscal

            return redirect('medicos:faturamento', fornecedor_id=fornecedor_id)
          else:   
            try:
              notafiscal = importar_xml(request, fornecedor)
              return redirect('medicos:nf_editar', notaFiscal_pk=notafiscal.id)
            except ValueError as e:
              messages.error(request, "arquivo XML inválido ou não selecionado. ")
              return redirect('medicos:faturamento', fornecedor_id=fornecedor_id)

#-------------------------------------------------------------
def nf_incluir(request):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  data_fiscal =   request.session['periodo_fiscal'] + '-01'

  fornecedor = Empresa.objects.get(id = empresa_id)  # Corrigido
  qryPjuridica_socios = Socio.objects.filter(empresa = empresa_id).order_by('pessoa__name')  # Corrigido

  lstSocios = []
  for socio in qryPjuridica_socios:
    #socio_data = socio.pessoa.CPF + '-' + socio.pessoa.name
    lstSocios.append([socio.pk,socio.pessoa.name])

  fornecedor_initial = []
  fornecedor_initial.append([fornecedor.pk, fornecedor.name])

  # recupera alicotas
  qryAlicotas = Alicotas.objects.filter().first()

  if request.method == 'POST':
      form = Edit_NotaFiscal_Form(request.POST)
      if form.is_valid():
        
        Nfiscal = form.save(commit = False) 
        Nfiscal.fornecedor = fornecedor   
        Nfiscal.save()

        request.session['msg_status'] = 'Inclusão de nota fiscal com sucesso!'
        return redirect('medicos:faturamento', fornecedor_id=fornecedor.id)
      else:
        print(form.errors)
        request.session['msg_status'] ='Falha na validadação dos dados' + str(form.errors)
        messages.error(request, "Error! " + str(form.errors) )
        return redirect('medicos:faturamento', fornecedor_id=fornecedor.id)
      
  else:
    #form = Edit_NotaFiscal_Form( socio_choices = lstSocios, initial={'dtEmissao': data_inicial  })
    form = Edit_NotaFiscal_Form( socio_choices = lstSocios, initial={'dtEmissao': data_fiscal  })
    template = loader.get_template('faturamento/nf_editar.html')

    context = {

                'data_fiscal' : data_fiscal,
                'form'        : form,
                'empresa'     : fornecedor,
                'alicotas'    : qryAlicotas,
                'msg'         : msg,
                'user'        : request.user,
              }
    return HttpResponse(template.render(context, request))

#-------------------------------------------------------------
def nf_editar(request, notaFiscal_pk):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  data_fiscal =   request.session['periodo_fiscal'] + '-01'

  #data_fiscal = datetime.datetime.strptime(data_fiscal, "%Y-%m-%d").date()

  fornecedor = Empresa.objects.get(id = empresa_id)  # Corrigido
  qryPjuridica_socios = Socio.objects.filter(empresa = empresa_id)  # Corrigido

  lstSocios = []
  for socio in qryPjuridica_socios:
    lstSocios.append([socio.pk,socio.pessoa.name])

  # recupera alicotas
  qryAlicotas = Alicotas.objects.filter().first()
  qryEntrada = NotaFiscal.objects.get(id = notaFiscal_pk) 
  if request.method == 'POST':
      form = Edit_NotaFiscal_Form(request.POST, instance=qryEntrada) # FUNCIONA   
      if form.is_valid():
        #form.save
        qryEntrada = form.save(commit = False) 
        qryEntrada.fornecedor = fornecedor
        qryEntrada.save()

        request.session['msg_status'] = 'Nota fiscal editada com sucesso!!!'
        return redirect('medicos:faturamento', fornecedor_id=fornecedor.id)
      else:
        request.session['msg_status'] = 'Falha na validadação dos dados'
        messages.error(request, "Error!!! - oopps")
        return redirect('medicos:faturamento', fornecedor_id=fornecedor.id)
  else:
    data_emissao = qryEntrada.dtEmissao.isoformat()
    # permitir dtRecebimento = null
    if (qryEntrada.dtRecebimento != None):
      data_recebimento = qryEntrada.dtRecebimento.isoformat()
    else:
      data_recebimento = None
          
    form = Edit_NotaFiscal_Form( instance = qryEntrada, socio_choices = lstSocios, initial={'dtEmissao': data_emissao, 'dtRecebimento': data_recebimento   })
    template = loader.get_template('faturamento/nf_editar.html')

    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Faturamento' 
    request.session['titulo_3'] = 'Notas Fiscais' 

    context = {
                'empresa'     : fornecedor,
                'data_fiscal' : data_fiscal,
                'form'        : form,
                'alicotas'    : qryAlicotas,
                'msg'         : msg,
                'user'        : request.user,
              }
    return HttpResponse(template.render(context, request))
  
#-------------------------------------------------------------------
def nf_excluir(request, notaFiscal_pk):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  fornecedor = Empresa.objects.get(id = empresa_id)  # Corrigido
  qryEntrada = NotaFiscal.objects.get(id = notaFiscal_pk).delete()

  #messages.success(request, 'Nota excluida com sucesso')
  request.session['msg_status'] = 'Nota excluida com sucesso!!!'

  return redirect('medicos:faturamento', fornecedor_id=fornecedor.id)

#-------------------------------------------------------------------
