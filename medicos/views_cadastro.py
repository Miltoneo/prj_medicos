from django.http import HttpResponse, FileResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from .models import *
from .data import *
from .forms import *

# django tables
from django.views.generic import ListView
from django_tables2 import SingleTableView, LazyPaginator
from .tables import *

#--------------------------------------------------------------------
def cadastro_main(request):
  
  msg =  request.session['msg_status']
  periodo_fiscal = request.session['periodo_fiscal']

  return redirect('medicos:cadastro_empresa')    

#-------------------------------------------------------------------
def cadastro_empresa(request):
    qryEmpresas = Empresa.objects.all().order_by('name')

    #msg = 'cadastro_empresa : ' 
    template = loader.get_template('cadastro/empresa/empresa_cadastro.html')
    context = {
                'lstEmpresas'   : qryEmpresas,
                'user'          : request.user,
                #'msg'           : msg
              }
    
    return HttpResponse(template.render(context, request))

#-------------------------------------------------------------------
def cadastro_pessoa(request):
  
  msg =  request.session['msg_status']
  lst_Pessoas = Pessoa.objects.all().order_by('name')

  #msg = 'index : ' 
  template = loader.get_template('cadastro/pessoa/pessoa_cadastro.html')
  context = {
              'lstPessoas'   : lst_Pessoas,
              'user'          : request.user,
              'msg'           : msg
            }
  
  return HttpResponse(template.render(context, request))

#-------------------------------------------------------------------
def cadastro_societario(request):
    msg =  request.session['msg_status']
    qryEmpresas = Empresa.objects.all()

    #msg = 'index : ' 
    template = loader.get_template('cadastro/socio/societario_lista_empresa.html')
    context = {
                'lstEmpresas'   : qryEmpresas,
                'user'          : request.user,
                'msg'           : msg
              }
    
    return HttpResponse(template.render(context, request))

#------------------------------------------------
def cadastro_aliquotas(request):
  
  msg =  request.session['msg_status']
  qryAliquotas, created = Aliquotas.objects.get_or_create(id=1)
    
  if request.method == 'POST':

    form = AliquotasForm(request.POST, instance = qryAliquotas)

    if form.is_valid():
      messages.success(request, 'Alíquotas registradas com sucesso!')

      alicotas_dict = request.POST.dict()
      form.save()

      return redirect('medicos:cadastro_alicotas')    

    else:
      request.session['msg_status'] = 'Falha na validação dos dados'
      return redirect('medicos:cadastro_aliquotas')
    
  else:

    form = AliquotasForm(instance = qryAliquotas)
    template = loader.get_template('cadastro/aliquotas/aliquotas_cadastro.html')
    context = {
                'form'        : form,
                'user'        : request.user,
                'msg'         : msg
              }
  
    return HttpResponse(template.render(context, request))

#------------------------------------------------
def cadastro_despesa_grupo(request):

  msg =  request.session['msg_status']
  qry_despesa_grupo = Despesa_Grupo.objects.all().order_by('codigo')

  template = loader.get_template('cadastro/grupo_despesa/cadastro_despesa_grupo.html')
  context = {
              'lst_despesa_grupo'   : qry_despesa_grupo,
              'user'          : request.user,
              'msg'           : msg,
              'tipo_operacao'     : 'Grupos cadastrados',
            }
  
  return HttpResponse(template.render(context, request))

#-------------------------------------------------
def despesa_grupo_incluir(request):

  msg =  request.session['msg_status']

  if request.method == 'POST':

    form = Despesa_Grupo_Form(request.POST)
    if form.is_valid():
      form.save()
      request.session['msg_status'] = 'Item editada com sucesso!!!'

      return redirect('medicos:cadastro_despesa_grupo')    

    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:cadastro_despesa_grupo')
    
  else:
    #msg =  empresa_nome
    form = Despesa_Grupo_Form()
    template = loader.get_template('cadastro/grupo_despesa/despesa_grupo_editar.html')
    context = {
                'form'        : form,
                'user'        : request.user,
                'msg'         : msg,
                'tipo_operacao'     : 'Inclusão',
              }
  
    return HttpResponse(template.render(context, request))

#-----------------------------------------------
def despesa_grupo_excluir(request,id):
  msg =  request.session['msg_status']

  qry_despesa_grupo = Despesa_Grupo.objects.get(id = id)
  qry_despesa_grupo.delete()
  messages.success(request, 'Item excluído com Sucesso!')

  return redirect('medicos:cadastro_despesa_grupo')

#-------------------------------------------------------------
def despesa_grupo_editar(request,id):

  msg =  request.session['msg_status']
  qry_despesa_grupo = Despesa_Grupo.objects.get(id = id)   
  
  if request.method == 'POST':

    form = Despesa_Grupo_Form(request.POST, instance = qry_despesa_grupo)
    if form.is_valid():
      form.save()
      request.session['msg_status'] = 'Item editada com sucesso!!!'

      return redirect('medicos:cadastro_despesa_grupo')    

    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:cadastro_despesa_grupo')
    
  else:
    #msg =  empresa_nome
    form = Despesa_Grupo_Form(instance = qry_despesa_grupo)
    template = loader.get_template('cadastro/grupo_despesa/despesa_grupo_editar.html')
    context = {
                'form'        : form,
                'user'        : request.user,
                'msg'         : msg,
                'tipo_operacao'     : 'Edição',
              }
  
    return HttpResponse(template.render(context, request))
  
#------------------------------------------------
def cadastro_despesa_item(request):
  
  msg =  request.session['msg_status']
  qry_despesa_item = Despesa_Item.objects.order_by('grupo__codigo','codigo','descricao')
  template = loader.get_template('cadastro/item_despesa/cadastro_despesa_item.html')
  context = {
              'lst_despesa_item'  : qry_despesa_item,
              'user'              : request.user,
              'msg'               : msg,
              'tipo_operacao'     : 'Itens cadastrados',
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------
def despesa_item_incluir(request):

  msg =  request.session['msg_status']

  if request.method == 'POST':

    form = Despesa_Item_Form(request.POST)
    if form.is_valid():
      form.save()
      request.session['msg_status'] = 'Item editada com sucesso!!!'

      return redirect('medicos:cadastro_despesa_item')    

    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:cadastro_despesa_item')
    
  else:
    #msg =  empresa_nome
    form = Despesa_Item_Form()
    template = loader.get_template('cadastro/item_despesa/despesa_item_editar.html')
    context = {
                'form'        : form,
                'user'        : request.user,
                'msg'         : msg,
                'tipo_operacao'     : 'Inclusão',
              }
  
    return HttpResponse(template.render(context, request))

#-----------------------------------------------
def despesa_item_excluir(request,id):
  msg =  request.session['msg_status']

  qry_despesa_item = Despesa_Item.objects.get(id = id)
  qry_despesa_item.delete()
  messages.success(request, 'Item excluído com Sucesso!')

  return redirect('medicos:cadastro_despesa_item')

#-------------------------------------------------------------
def despesa_item_editar(request,id):

  msg =  request.session['msg_status']
  qry_despesa_item = Despesa_Item.objects.get(id = id)   
  
  if request.method == 'POST':

    form = Despesa_Item_Form(request.POST, instance = qry_despesa_item)
    if form.is_valid():
      form.save()
      request.session['msg_status'] = 'Item editada com sucesso!!!'

      return redirect('medicos:cadastro_despesa_item')    

    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:cadastro_despesa_item')
    
  else:
    #msg =  empresa_nome
    form = Despesa_Item_Form(instance = qry_despesa_item)
    template = loader.get_template('cadastro/item_despesa/despesa_item_editar.html')
    context = {
                'form'        : form,
                'user'        : request.user,
                'msg'         : msg,
                'tipo_operacao'     : 'Edição',
              }
  
    return HttpResponse(template.render(context, request))

#-------------------------------------------------------------
def empresa_editar(request,id_empresa):

  msg =  request.session['msg_status']

  empresa_nome = Empresa.objects.get(id = id_empresa).name

  qrySetEmpresa, created = Empresa.objects.get_or_create(id = id_empresa)   
  
  if request.method == 'POST':

    form = EmpresaForm(request.POST, instance = qrySetEmpresa)

    if form.is_valid():
      #messages.success(request, 'Empresa Editada com sucesso! !')
      request.session['msg_status'] = 'Empresa Editada com sucesso!!!'
      form.save()

      return redirect('medicos:cadastro_empresa')    

    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:cadastro_empresa')
    
  else:
    #msg =  empresa_nome

    form = EmpresaForm(instance = qrySetEmpresa)
    template = loader.get_template('cadastro/empresa/empresa_editar.html')
    context = {
                'form'        : form,
                'empresa'     : empresa_nome,
                'user'        : request.user,
                'msg'         : msg
              }
  
    return HttpResponse(template.render(context, request))
  
#--
def empresa_excluir(request,id_empresa):
  msg =  request.session['msg_status']

  qryEntrada = Empresa.objects.get(id = id_empresa)
  qryEntrada.delete()
  messages.success(request, 'Entrada apagada com sucesso')

  return redirect('medicos:cadastro_empresa')

#-------------------------------------------------
def empresa_incluir(request):
  
  msg =  request.session['msg_status']

  if request.POST: 
      form = EmpresaForm(request.POST)    

      if form.is_valid():
        qryCreate = Empresa(
          CNPJ    = form.cleaned_data["CNPJ"],
          name    = form.cleaned_data["name"]
          )
        qryCreate.save()
        return redirect('medicos:cadastro_empresa')

  template = loader.get_template('cadastro/empresa/empresa_inclusao.html')
  form = EmpresaForm( )  

  context = {
              'form'       : form,
              'user'       : request.user,
              'msg'        : msg
            }
  return HttpResponse(template.render(context, request))

#--
def pessoa_editar(request,id_pessoa):
  
  msg =  request.session['msg_status']

  pessoa_nome = Pessoa.objects.get(id = id_pessoa).name

  qrySetPessoa, created = Pessoa.objects.get_or_create(id = id_pessoa)   
  if request.method == 'POST':

    form = PessoaForm(request.POST, instance = qrySetPessoa)
    if form.is_valid():
      messages.success(request, 'Pessoa Editada com sucesso! !')
      form.save()
      return redirect('medicos:cadastro_pessoa')    

    else:
      request.session['msg_status'] = 'Falha na validadação dos dados'
      return redirect('medicos:cadastro_pessoa')
    
  else:
    #msg =  pessoa_nome

    form = PessoaForm(instance = qrySetPessoa)
    template = loader.get_template('cadastro/pessoa/pessoa_inclusao.html')
    context = {
                'form'       : form,
                'pessoa'     : pessoa_nome,
                'user'       : request.user,
                'msg'        : msg
              }
  
    return HttpResponse(template.render(context, request))
  
#-----------------------------------------------
def pessoa_excluir(request,id_pessoa):
  msg =  request.session['msg_status']

  qryPessoa = Pessoa.objects.get(id = id_pessoa)
  qryPessoa.delete()
  messages.info(request, 'Pessoa apagada com sucesso')

  return redirect('medicos:cadastro_pessoa')

#------------------------------------------------------------------
def pessoa_incluir(request):
  msg =  request.session['msg_status']

  if request.POST: 
      
      form = PessoaForm(request.POST)    
      if form.is_valid():
        form.save()
        request.session['msg_status'] = 'Item incluído com sucesso!!!'
        return redirect('medicos:cadastro_pessoa')
      else:
        request.session['msg_status'] = 'Falha na validadação dos dados'
        return redirect('medicos:cadastro_pessoa')

  template = loader.get_template('cadastro/pessoa/pessoa_inclusao.html')
  form = PessoaForm( )  

  context = {
              'form'       : form,
              'user'       : request.user,
              'msg'        : msg
            }
  
  return HttpResponse(template.render(context, request))

#-- Gestão de Socios: Tela incluir
def socio_incluir(request, id_empresa):
  
  msg =  request.session['msg_status']

  empresa_nome = Empresa.objects.get(id = id_empresa).name  # Corrigido

  qrySetPrestador = Socio.objects.filter(empresa = id_empresa).values_list('pessoa', 'pessoa')  # Corrigido
  qrySet_socio_empresa = Socio.objects.filter(empresa = id_empresa)  # Corrigido

  # cria a nota fiscal
  qrySocio = Socio()
  qrySocio.empresa = Empresa.objects.get(id=id_empresa)  # Corrigido

  if request.POST: 
      form = SocioForm(request.POST)    

      if form.is_valid():
          qryCreate = Socio(
          pjuridica             = form.cleaned_data["pjuridica"],
          pessoa                = form.cleaned_data["pessoa"],
         
          )
      qryCreate.save()
      return redirect('medicos:societario_empresa', id_empresa=id_empresa)

  template = loader.get_template('cadastro/socio/socio_inclusao.html')
  form = SocioForm(instance=qrySocio)  
  context = {
              'empresa_nome' : empresa_nome,
              'form'       : form,
              'user'       : request.user,
              'msg'        : msg
            }
  
  return HttpResponse(template.render(context, request))

#--------------------------------
def socio_excluir(request,id_pessoa, id_empresa):
  msg =  request.session['msg_status']

  qryPessoa_Empresa = Socio.objects.get(empresa = id_empresa, pessoa = id_pessoa)  # Corrigido
  qryPessoa_Empresa.delete()
  messages.success(request, 'Pessoa apagada com sucesso')

  return redirect('medicos:societario_empresa', id_empresa=id_empresa)

def societario_empresa(request,id_empresa):
    msg =  request.session['msg_status']

    request.session['empresa_id'] = id_empresa
    empresa_id = request.session['empresa_id']
    empresa = Empresa.objects.get(id=empresa_id)  # Corrigido

    #lstSocios = montaListaSocios(request, id_empresa)
    qry_socios = Socio.objects.filter(empresa = id_empresa)  # Corrigido

    #msg = empresa_nome
    template = loader.get_template('cadastro/socio/societario_empresa.html')
    context = {
              'id_empresa'    : id_empresa,  
              'empresa'       : empresa,
              'lstSocios'     : qry_socios,
              'user'          : request.user,
              'msg'           : msg
            }
  
    return HttpResponse(template.render(context, request))

def despesa_geral_folha(request):
    msg =  request.session['msg_status']

    empresa_id = request.session['empresa_id']

    empresa_nome = Empresa.objects.get(id=empresa_id).name  # Corrigido
    lst_despesa = monta_despesa(request, empresa_id)

    #msg = empresa_nome + " - FORNECEDOR>> " + str(lst_despesa[0].empresa)

    template = loader.get_template('despesa_geral_folha.html')
    context = {
              'id_empresa'    : empresa_id,  
              'empresa_nome'  : empresa_nome,
              'lst_despesa'  : lst_despesa,
              'user'          : request.user,
              'msg'           : msg
            }
  
    return HttpResponse(template.render(context, request))

#-----------------------------------------------------------------------------
class Cadastro_Desc_Mov_Financeiras_TableView(SingleTableView):

    model = DescricaoMovimentacao
    table_class = Desc_mov_financeira_Table
    template_name = 'cadastro/desc_mov_financeira/desc_mov_financeira.html'
    paginate_by = 15    
    paginator_class = LazyPaginator

    def get_context_data(self):
        context = super().get_context_data()
        
        fornecedor_id = self.request.session['empresa_id'] 
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido
        
        context["empresa"] = fornecedor
        context["msg"] = self.request.session['msg_status']

        return context

    def get_table_data(self):
        fornecedor_id = self.request.session['empresa_id'] 
        fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

        #queryset = DescricaoMovimentacao.objects.filter(fornecedor = fornecedor ).order_by('descricao')
        queryset = DescricaoMovimentacao.objects.all().order_by('descricao')
        return queryset
    
#----------------------------------------------------------------------------#
# CADASTRO DE MOVIMENTAÇÃO                                      
#----------------------------------------------------------------------------#    

def desc_mov_transferencia_incluir(request):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  fornecedor = Empresa.objects.get(id = empresa_id)  # Corrigido

  if request.method == 'POST':

    form = Edit_Desc_Mov_Financeira_Form(request.POST)
    if form.is_valid():
      desc= form.save(commit=False)
      desc.fornecedor = fornecedor
      desc.save()

      request.session['msg_status'] = 'Inclusão com sucesso!'
      return redirect('medicos:Cadastro_Desc_Mov_Financeiras_TableView')    

    else:
      print(form.errors)
      request.session['msg_status'] ='Falha na validadação dos dados' + str(form.errors)
      messages.error(request, "Error! " + str(form.errors) )
      return redirect('medicos:Cadastro_Desc_Mov_Financeiras_TableView')  
    
  else:

    #form = Edit_NotaFiscal_Form( socio_choices = lstSocios, initial={'dtEmissao': data_inicial, 'dtRecebimento': data_inicial   })
    form = DescricaoMovimentacaoForm()
    template = loader.get_template('cadastro/desc_mov_financeira/desc_mov_financeira_editar.html')


    context = {
                'form'        : form,
                'empresa'     : fornecedor,
                'msg'         : msg,
                'user'        : request.user,
              }
    return HttpResponse(template.render(context, request))

#----------------------------------------------------------------------------#
def desc_mov_financeira_editar(request, desc_id):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  fornecedor = Empresa.objects.get(id = empresa_id)  # Corrigido


  ds_desc_movimentacao = DescricaoMovimentacao.objects.get(id = desc_id) 
  if request.method == 'POST':

    form = DescricaoMovimentacaoForm(request.POST, instance=ds_desc_movimentacao)
    if form.is_valid():
      form.save()

      request.session['msg_status'] = 'Inclusão com sucesso!'
      return redirect('medicos:Cadastro_Desc_Mov_Financeiras_TableView')    

    else:
      print(form.errors)
      request.session['msg_status'] ='Falha na validadação dos dados' + str(form.errors)
      messages.error(request, "Error! " + str(form.errors) )
      return redirect('medicos:Cadastro_Desc_Mov_Financeiras_TableView')  
    
  else:

    form = DescricaoMovimentacaoForm( instance = ds_desc_movimentacao)
    template = loader.get_template('cadastro/desc_mov_financeira/desc_mov_financeira_editar.html')


    context = {
                'form'        : form,
                'empresa'     : fornecedor,
                'msg'         : msg,
                'user'        : request.user,
              }
    return HttpResponse(template.render(context, request))

#-------------------------------------------------------------------
def desc_mov_transferencia_excluir(request, desc_id):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  fornecedor = Empresa.objects.get(id = empresa_id)  # Corrigido
  ds_financeiro = DescricaoMovimentacao.objects.get(id = desc_id).delete()

  #messages.success(request, 'Nota excluida com sucesso')
  request.session['msg_status'] = 'Exclusão com com sucesso!!!'

  return redirect('medicos:Cadastro_Desc_Mov_Financeiras_TableView')
