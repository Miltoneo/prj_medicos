from .models import *
from dateutil.relativedelta import relativedelta
import calendar
import datetime

#---------------------------------------------------------------------  
# retorna date 
# yy-mm-01
def get_data_new(ano_fiscal, mes):
    
    mm =  '%02d' %mes
    #yy-mm-01
    data_inicial = str(ano_fiscal) + '-' + mm + '-01'
    data_inicial = datetime.datetime.strptime(data_inicial, "%Y-%m-%d").date()
    return data_inicial

#---------------------------------------------------------------------
def get_data(ano_fiscal, mes):
    
    mm =  '%02d' %mes
    #yy-mm-01
    data_inicial = str(ano_fiscal) + '-' + mm + '-01'
    
    return data_inicial

#---------------------------------------------------------------------
def get_mes_seguinte(ano_fiscal, mes):
    
    ano = int(ano_fiscal)
    mes = int(mes)
    data=datetime.date(ano, mes, 1)
    data = data + relativedelta(months=1)  # mes seguinte
    data = data.strftime("%Y-%m-%d")
    
    return data

#---------------------------------------------------------------------
def excel_round(num, decimals=0):

    #num = Number(Math.round(num +'e'+ decimals) + 'e-' + decimals);
    num =   round(int(num*10**decimals)*int(22876.5*10**d)/10**(d*2),2)
    return num

#---------------------------------------------------------------------
# retorna a id da descrição para padrão de movimentação financeira
# cria se não existir 
def get_descricao_movimentacao(descricao):

    desc_movimentacao, created = DescricaoMovimentacao.objects.get_or_create(descricao = descricao)
    if created:
        desc_movimentacao.save()

    return desc_movimentacao

#---------------------------------------------------------------------

# apaga as movimentações automaticas do mes seguinte para recalculo do balanço

def apaga_movimentoes_automaticas_mes_seguinte(ano_fiscal, mes):

    ano = int(ano_fiscal)
    mes = int(mes)
    data=datetime.date(ano, mes, 1)
    data = data + relativedelta(months=1) # mes seguinte

    descricao = get_descricao_movimentacao(DESC_MOVIMENTACAO_CREDITO_SALDO_MES_SEGUINTE)

    try:
        Financeiro.objects.get(data = data, operacao_auto = True).delete()
    except:
        pass


#-----------------------------------------------------------------------------------
def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)

#-----------------------------------------------------------------------------------
def sub_months(sourcedate, months):
    month = sourcedate.month - 1 - months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    temp = datetime.date(year, month, day)
    return temp