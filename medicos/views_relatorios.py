from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.conf import settings
from django.contrib import messages
from .models import *
from .data import *
from .forms import *
from .report import *

# django tables
from django.views.generic import ListView
from django_tables2 import SingleTableView, LazyPaginator
from .tables import *

import locale
locale.setlocale(locale.LC_ALL,'')

#------------------------------------------------------------------------------  
def relatorios(request):

  msg =  request.session['msg_status']
  periodo_fiscal = request.session['periodo_fiscal']

  empresa_id = request.session['empresa_id']

  fornecedor = Empresa.objects.get(id=empresa_id)
  lst_socio = Socio.objects.filter(empresa=fornecedor)

  # cabeçalho da página
  request.session['titulo_1'] = 'Demonstrativo'  
  request.session['titulo_2'] = 'Lista de Sócios '

  template = loader.get_template('relatorios/relatorios.html')
  context = {
              'empresa'           : fornecedor,
              'periodo_fiscal'    : periodo_fiscal,
              'lst_socio'         : lst_socio,
              'msg'               : msg,
              'user'            : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def relatorio_mensal_lista_socios(request):

  msg =  request.session['msg_status']
  periodo_fiscal = request.session['periodo_fiscal']
  empresa_id = request.session['empresa_id']

  fornecedor = Empresa.objects.get(id=empresa_id)
  lst_socio = Socio.objects.filter(empresa=fornecedor).order_by('pessoa__name')

  # cabeçalho da página
  request.session['titulo_1'] = 'Demonstrativo'  
  request.session['titulo_2'] = 'Lista de Sócios '

  template = loader.get_template('relatorios/relatorio_mensal_lista_socios.html')
  context = {
              'empresa'         : fornecedor,
              'periodo_fiscal'      : periodo_fiscal,
              'lst_socio'       : lst_socio,
              'msg'             : msg,
              'user'            : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def relatorio_socio_mes(request, socio_id):

  msg =  request.session['msg_status']
  id_empresa = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  fornecedor = Empresa.objects.get(id=id_empresa)
  socio = Socio.objects.get(id=socio_id)

  if request.method == 'POST':
    
    if request.POST.get("form_type") =='getdata':  
      periodo_fiscal = request.POST.get("mytext")
      request.session['periodo_fiscal'] = periodo_fiscal
      return redirect('medicos:relatorio_socio_mes', socio_id=socio_id)

  else:  
    # nota fiscal  
    lst_nfiscais = NotaFiscal.objects.filter(dtRecebimento__year=periodo_fiscal.year, dtRecebimento__month=periodo_fiscal.month, fornecedor=fornecedor, socio=socio,\
                                            )
    totais_nfiscais = lst_nfiscais.aggregate(
        total_bruto=Sum('val_bruto'),
        total_ISS=Sum('val_ISS'),
        total_PIS=Sum('val_PIS'),
        total_COFINS=Sum('val_COFINS'),
        total_IR=Sum('val_IR'),
        total_CSLL=Sum('val_CSLL'),
        total_liquido=Sum('val_liquido')
    )

    # # nota fiscal  NFISCAL_ALICOTA_CONSULTAS
    # lst_nfiscal_consulta = NotaFiscal.objects.filter(dtRecebimento__year=periodo_fiscal.year, dtRecebimento__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio,\
    #                                                   tipo_aliquota = NFISCAL_ALICOTA_CONSULTAS)
    # totais_nfiscal_consulta = lst_nfiscal_consulta.aggregate(
    #     total_bruto=Sum('val_bruto'),
    #     total_ISS=Sum('val_ISS'),
    #     total_PIS=Sum('val_PIS'),
    #     total_COFINS=Sum('val_COFINS'),
    #     total_IR=Sum('val_IR'),
    #     total_CSLL=Sum('val_CSLL'),
    #     total_liquido=Sum('val_liquido')
    # )

    # # nota fiscal  NFISCAL_ALICOTA_PLANTAO
    # lst_nfiscal_plantao = NotaFiscal.objects.filter(dtRecebimento__year=periodo_fiscal.year, dtRecebimento__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio,\
    #                                                  tipo_aliquota = NFISCAL_ALICOTA_PLANTAO)
    # totais_nfiscal_plantao = lst_nfiscal_plantao.aggregate(
    #     total_bruto=Sum('val_bruto'),
    #     total_iss=Sum('val_ISS'),
    #     total_pis=Sum('val_PIS'),
    #     total_cofins=Sum('val_COFINS'),
    #     total_ir=Sum('val_IR'),
    #     total_csll=Sum('val_CSLL'),
    #     total_liquido=Sum('val_liquido')
    # )
    
    # # nota fiscal NFISCAL_ALICOTA_OUTROS ..
    # lst_nfiscal_outros = NotaFiscal.objects.filter(dtRecebimento__year=periodo_fiscal.year, dtRecebimento__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio,\
    #                                                 tipo_aliquota = NFISCAL_ALICOTA_OUTROS)

    # totais_nfiscal_outros = lst_nfiscal_outros.aggregate(
    #     total_bruto=Sum('val_bruto'),
    #     total_iss=Sum('val_ISS'),
    #     total_pis=Sum('val_PIS'),
    #     total_cofins=Sum('val_COFINS'),
    #     total_ir=Sum('val_IR'),
    #     total_csll=Sum('val_CSLL'),
    #     total_liquido=Sum('val_liquido')
    # )
    

    # despesa de socio = despesas sem rateio 
    ds_despesa_socio = Despesa.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, empresa=fornecedor, socio=socio, tipo_rateio=TIPO_DESPESA_SEM_RATEIO)

    # despesa com rateio = despesa folha  e despesa geral
    ds_desp_rateio= Despesa_socio_rateio.objects.filter(despesa__data__year=periodo_fiscal.year, despesa__data__month=periodo_fiscal.month, socio=socio)\
                                                  .order_by('despesa__item__codigo')

    # rendimentos de aplicações financeiras
    ds_financeiro = Financeiro.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, fornecedor=fornecedor, socio=socio)\
                                                  .order_by('data')

    # operações financeiras
    ds_resumo_operacoes_financeiras = Financeiro.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, fornecedor=fornecedor, socio=socio)\
                                                              .values('descricao__descricao')\
                                                              .annotate(valor=Sum('valor'))

    #monta relatório na tabela de relatorio mensal   

    balanco = monta_balanco(request, socio_id, periodo_fiscal)

    # Título da aba da página
    request.session['title_page'] = 'Desmonstrativo Mensal'
    # cabeçalha da página
    request.session['titulo_1'] = fornecedor.name
    request.session['titulo_2'] = 'Desmonstrativo Mensal' 
    request.session['titulo_3'] = 'Sócio: ' + socio.pessoa.name

  template = loader.get_template('apuracao/apuracao_socio_mes.html')
  context = {
              'empresa'           : fornecedor,
              'periodo_fiscal'    : periodo_fiscal,
              'socio'             : socio,

              'lst_nfiscais'   : lst_nfiscais,
              'totais_nfiscais'  : totais_nfiscais,

              # 'lst_nfiscais_consultas'   : lst_nfiscal_consulta,
              # 'totais_nfiscal_consulta'  : totais_nfiscal_consulta,

              # 'lst_nfiscais_plantao'     : lst_nfiscal_plantao,
              # 'totais_nfiscal_plantao'   : totais_nfiscal_plantao,

              # 'lst_nfiscais_outros'      : lst_nfiscal_outros,
              # 'totais_nfiscal_outros'    : totais_nfiscal_outros,

              'lst_despesa_pessoa'      : ds_despesa_socio,
              'ds_despesa_rateio'       : ds_desp_rateio,
              'ds_financeiro'           : ds_financeiro,
              'ds_resumo_operacoes_financeiras'     : ds_resumo_operacoes_financeiras,
              'balanco'             : balanco,
              'msg'                 : socio,
              'user'                : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def apuracao_pis(request):

  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']
  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
  fornecedor = Empresa.objects.get(id=empresa_id)  # Corrigido

  monta_apuracao_pis(request)
  ds_balanco_pis = Apuracao_pis.objects.filter(data__year = periodo_fiscal.year ,fornecedor = fornecedor)

  # cabeçalho da página
  request.session['titulo_1'] = fornecedor.name
  request.session['titulo_2'] = 'Apuração PIS'  
  request.session['titulo_3'] =  'Relatório' 

  template = loader.get_template('apuracao/apuracao_pis.html')
  context = {
              'empresa'           : fornecedor,
              'periodo_fiscal.year'        : periodo_fiscal.year,
              'ds_balanco_pis'    : ds_balanco_pis,
              'msg'               : msg,
              'user'              : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def apuracao_cofins(request):

  msg =  request.session['msg_status']
  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  empresa_id = request.session['empresa_id']
  fornecedor = Empresa.objects.get(id=empresa_id)  # Corrigido

  monta_apuracao_cofins(request)
  ds_balanco_cofins = Apuracao_cofins.objects.filter(data__year = periodo_fiscal.year ,fornecedor = fornecedor)

  # cabeçalho da página
  request.session['titulo_1'] = fornecedor.name
  request.session['titulo_2'] = 'Apuração COFINS'
  request.session['titulo_3'] = 'Relatório'

  template = loader.get_template('apuracao/apuracao_cofins.html')
  context = {
              'empresa'           : fornecedor,
              'periodo_fiscal.year'        : periodo_fiscal.year,
              'ds_balanco_pis'    : ds_balanco_cofins,
              'msg'               : msg,
              'user'              : request.user,
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def apuracao_csll_irpj(request):
  
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  fornecedor = Empresa.objects.get(id=empresa_id)  # Corrigido

  monta_apuracao_csll_irpj_new(request, empresa_id)
  ds_apuracao_csll = Apuracao_csll.objects.filter( data__year = periodo_fiscal.year, fornecedor = empresa_id)
  ds_apuracao_irpj = Apuracao_irpj.objects.filter( data__year = periodo_fiscal.year, fornecedor = empresa_id)

  # cabeçalho da página
  request.session['titulo_1'] = fornecedor.name
  request.session['titulo_2'] = 'Apuração CSLL'
  request.session['titulo_3'] = 'Relatório'

  template = loader.get_template('apuracao/apuracao_csll_irpj.html')
  context = {
              'periodo_fiscal.year'  : periodo_fiscal.year,
              'periodo_fiscal.month'         : periodo_fiscal.month,
              'empresa'     : fornecedor,
              'apuracao_csll': ds_apuracao_csll,
              'apuracao_irpj': ds_apuracao_irpj,
              'user'          : request.user,
              'msg'           : msg
            }
  
  return HttpResponse(template.render(context, request))

#------------------------------------------------------------------------------  
def apuracao_issqn(request):
  msg =  request.session['msg_status']
  empresa_id = request.session['empresa_id']

  periodo_fiscal = request.session['periodo_fiscal'] + '-01'
  periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

  fornecedor = Empresa.objects.get(id=empresa_id)  # Corrigido
  monta_apuracao_issqn(request, empresa_id)
  ds_balanco_iss = Apuracao_iss.objects.filter(data__year = periodo_fiscal.year ,fornecedor = fornecedor)

  # cabeçalho da página
  request.session['titulo_1'] = fornecedor.name
  request.session['titulo_2'] = 'Apuração ISSQN'  
  request.session['titulo_3'] =  'Relatório' 

  template = loader.get_template('apuracao/apuracao_issqn.html')
  context = {
              'periodo_fiscal.year'    : periodo_fiscal.year,
              'periodo_fiscal.month'           : periodo_fiscal.month,
              'empresa'       : fornecedor,
              'ds_apuracao'   : ds_balanco_iss,
              'user'          : request.user,
              'msg'           : msg
            }
  
  return HttpResponse(template.render(context, request))

#-----------------------------------------------
class Demonstrativo_View(SingleTableView):

    model = Socio
    table_class = Socio_Table
    template_name = 'base/tableView.html'
    paginate_by = 50   
    paginator_class = LazyPaginator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        empresa_id = self.request.session['empresa_id'] 
        empresa = Empresa.objects.get(id=empresa_id)  # Corrigido

        context["periodo_fiscal"] = self.request.session['periodo_fiscal'] 
        context["empresa"] = empresa
        context["msg"] = self.request.session['msg_status']

        # cabeçalha da página
        self.request.session['title_page'] = 'Demonstrativo'
        # cabeçalha da página
        self.request.session['titulo_1'] = empresa.name
        self.request.session['titulo_2'] = 'Demonstrativo' 
        self.request.session['titulo_3'] = 'Lista de sócios' 

        return context

    def get_queryset(self):

        periodo_fiscal=  self.request.session['periodo_fiscal'] + '-01'
        periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
  
        empresa_id = self.request.session['empresa_id'] 
        empresa = Empresa.objects.get(id=empresa_id)  # Corrigido

        queryset = Socio.objects.filter(empresa = empresa ).order_by('pessoa__name')

        return queryset

def relatorio_socio_ano(request, socio_id):
    # ...existing code...
    id_empresa = request.session['empresa_id']
    fornecedor = Empresa.objects.get(id=id_empresa)  # Corrigido
    # ...restante do código...