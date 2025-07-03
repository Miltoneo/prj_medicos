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
def index(request):
  
  now=datetime.datetime.now()
  periodo_fiscal = now.strftime("%Y-%m")
  msg =  ''
  
  request.session['msg_status'] = 'Bem-vindo!'
  request.session['nome_aplicativo'] = 'SIRCO - Sistema de Rotinas Contábeis'
  request.session['periodo_fiscal'] = periodo_fiscal

  if 'msg_status' in request.session:
    msg = request.session['msg_status']

  return redirect('medicos:empresas_main')  

#----------------------------------------------------------
# Preparação do sistema e fornecedor
def start(request, fornecedor_id):
    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    fornecedor_id = fornecedor_id
    fornecedor = Empresa.objects.get(id=fornecedor_id)  # Corrigido

    # monta tabela de aplicações financeiras
    for mes in range(1,13):
        Aplic_financeiras.objects.get_or_create(
            data = periodo_fiscal,
            fornecedor = fornecedor,
        )

    return redirect('medicos:faturamento', fornecedor_id=fornecedor_id)

