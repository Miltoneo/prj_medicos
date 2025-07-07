from .models import *
import math
from django.db.models import Avg, Count, Min, Sum, Max
from .util import *
from decimal import Decimal

from django.db.models import FloatField
from django.db.models.functions import Cast
from django.contrib import messages

# import xml
import xml.etree.ElementTree as ET
from babel.numbers import parse_decimal
import xmltodict
#-------------------------------------------------------------------------------------------------
def monta_apuracao_csll_irpj_new(request, empresa_id):

    fornecedor = Empresa.objects.get(id=empresa_id)
    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    #fornecedor = Pjuridica.objects.get(id=empresa_id)
    aliquota = Aliquotas.objects.get(id = 1)

    #--Calculo tributo Trimestral
    mes_inicial = 0
    mes_final   = 0

     # trimestre 1 a 4
    for trimestre in range(1,5):

        mes_inicial = mes_final + 1
        mes_final   = mes_inicial + 2

        # REGIME_TRIBUTACAO_COMPETENCIA = considera mes de emissão da nota fiscal
        if (fornecedor.tipo_regime == REGIME_TRIBUTACAO_COMPETENCIA ):
            
            # recupera notas ficais tipo de alicota= serviços de consultas          
            qry_fat_alicota_consultas = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month__range=(mes_inicial, mes_final), fornecedor=fornecedor, tipo_aliquota = NFISCAL_ALICOTA_CONSULTAS ) \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(irpj=Sum('val_IR')) 
                                                            #.annotate(csll=Sum('val_CSLL')) \


            # recupera notas ficais tipo de alicota= serviços de plantao          
            qry_fat_alicota_plantao = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month__range=(mes_inicial, mes_final), fornecedor=fornecedor, tipo_aliquota = NFISCAL_ALICOTA_PLANTAO) \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(irpj=Sum('val_IR')) 
                                                            #.annotate(csll=Sum('val_CSLL')) \


            # recupera notas ficais tipo de alicota= serviços outros         
            qry_fat_alicota_outros = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month__range=(mes_inicial, mes_final), fornecedor=fornecedor, tipo_aliquota = NFISCAL_ALICOTA_OUTROS) \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(irpj=Sum('val_IR')) 
                                                            #.annotate(csll=Sum('val_CSLL')) \

        else:
            # recupera notas ficais tipo de alicota= serviços de consultas 
            qry_fat_alicota_consultas = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month__range=(mes_inicial, mes_final), fornecedor=fornecedor, tipo_aliquota = NFISCAL_ALICOTA_CONSULTAS)  \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(irpj=Sum('val_IR'))
                                                            #.annotate(csll=Sum('val_CSLL')) \


            qry_fat_alicota_plantao = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month__range=(mes_inicial, mes_final), fornecedor=fornecedor, tipo_aliquota = NFISCAL_ALICOTA_PLANTAO)  \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(irpj=Sum('val_IR'))
                                                            #.annotate(csll=Sum('val_CSLL')) \

            # recupera notas ficais tipo de alicota= serviços outros            
            qry_fat_alicota_outros = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month__range=(mes_inicial, mes_final), fornecedor=fornecedor, tipo_aliquota = NFISCAL_ALICOTA_OUTROS) \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(irpj=Sum('val_IR'))
                                                            #.annotate(csll=Sum('val_CSLL')) \

        # IF END

        #----------------------------------------------------------------------------------------------------------------------------------------------
        # CSLL retido - modificado para considerar o mes de recebimento da nota fiscal (new)
        qry_csll_retido = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month__range=(mes_inicial, mes_final), fornecedor=fornecedor) \
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(csll=Sum('val_CSLL'))

        #----------------------------------------------------------------------------------------------------------------------------------------------
        # rendimentos de aplicações fincanceiras
        ds_rend_aplic= AplicacaoFinanceira.objects.filter(data__year = periodo_fiscal.year, data__month__range=(mes_inicial, mes_final), fornecedor=fornecedor)\
                                                            .values('fornecedor') \
                                                            .order_by('fornecedor') \
                                                            .annotate(total=Sum('rendimentos'))\
                                                            .annotate(irrf=Sum('irrf')) #new
        


        if ds_rend_aplic:
            rend_aplic = ds_rend_aplic.first()

        #----------------------------------------------------------------------------------------------------------------------------------------------
        data_inicial = get_data(periodo_fiscal.year, trimestre)

        # recupera tabela CSLL
        apuracao_csll, created = Apuracao_csll.objects.get_or_create(data__year = periodo_fiscal.year,
                                                                        data = data_inicial,
                                                                        trimestre = trimestre, 
                                                                        fornecedor=fornecedor)
        if created:
            apuracao_csll.save()

        #----------------------------------------------------------------------------------------------------------------------------------------------
        # recupera tabela IRPJ
        apuracao_irpj, created = Apuracao_irpj.objects.get_or_create(data__year = periodo_fiscal.year, 
                                                                        data = data_inicial,
                                                                        trimestre = trimestre, 
                                                                        fornecedor=fornecedor)
        if created:
            apuracao_irpj.save()

        #----------------------------------------------------------------------------------------------------------------------------------------------
        apuracao_csll.receita_consultas = 0
        apuracao_csll.receita_plantao = 0
        apuracao_csll.receita_outros = 0

        # cssl_retido 
        if qry_csll_retido:
            csll_retido = qry_csll_retido.first()
            apuracao_csll.imposto_retido = round(csll_retido.get('csll'), 2)

        # faturamento consultas
        if (qry_fat_alicota_consultas):
            fat_consultas = qry_fat_alicota_consultas.first()
            # CSLL
            apuracao_csll.receita_consultas = round(fat_consultas.get('faturamento'),2)

            # IRPJ
            apuracao_irpj.receita_consultas = round(fat_consultas.get('faturamento'),2)
            apuracao_irpj.imposto_retido = round(fat_consultas.get('irpj'),2)

        # faturamento plantão
        if (qry_fat_alicota_plantao):
            fat_plantao = qry_fat_alicota_plantao.first()
            # CSLL
            apuracao_csll.receita_plantao = round(fat_plantao.get('faturamento'),2)

            # IRPJ
            apuracao_irpj.receita_plantao = round(fat_plantao.get('faturamento'),2)
            apuracao_irpj.imposto_retido += fat_plantao.get('irpj')

        # totaliza receitas
        apuracao_csll.receita_consultas += apuracao_csll.receita_plantao
        apuracao_irpj.receita_consultas += apuracao_irpj.receita_plantao

        # Aplica CSLL_ALIC_2 e IRPJ_ALIC_2 para consultas e plantão
        apuracao_csll.base_calculo = apuracao_csll.receita_consultas * (aliquota.CSLL_ALIC_2/100)
        apuracao_irpj.base_calculo = apuracao_irpj.receita_consultas * (aliquota.IRPJ_ALIC_2/100)

        # Para outros serviços, aplica CSLL_ALIC_1 e IRPJ_ALIC_1
        #for fat_outros in qry_fat_alicota_outros:
        if (qry_fat_alicota_outros):
            fat_outros = qry_fat_alicota_outros.first()
            # soma impostos anteriores
            # CSLL
            apuracao_csll.receita_outros = fat_outros.get('faturamento')
            apuracao_csll.base_calculo += apuracao_csll.receita_outros * (aliquota.CSLL_ALIC_1 / 100)
            # IRPJ
            apuracao_irpj.receita_outros = fat_outros.get('faturamento')
            apuracao_irpj.base_calculo += apuracao_irpj.receita_outros * (aliquota.IRPJ_ALIC_1 / 100)
            apuracao_irpj.imposto_retido += fat_outros.get('irpj')


        # APLICAÇÕES FINANCEIRAS
        # RENDIMENTOS
        apuracao_csll.rend_aplicacao  = round(rend_aplic.get('total'),2)
        apuracao_irpj.rend_aplicacao  = round(rend_aplic.get('total'),2)
        # IRRF
        apuracao_csll.irrf_aplicacao  = round(rend_aplic.get('irrf'),2)
        apuracao_irpj.irrf_aplicacao  = round(rend_aplic.get('irrf'),2)

        # totaliza base de cálculo + rendimentos das aplicações
        apuracao_csll.base_calculo_total = apuracao_csll.base_calculo + apuracao_csll.rend_aplicacao 
        apuracao_irpj.base_calculo_total = apuracao_irpj.base_calculo + apuracao_irpj.rend_aplicacao  

        # receita bruta
        apuracao_csll.receita_bruta = apuracao_csll.receita_consultas + apuracao_csll.receita_outros
        apuracao_irpj.receita_bruta = apuracao_irpj.receita_consultas + apuracao_irpj.receita_outros

        #CSLL imposto devido = alicota 9%
        apuracao_csll.imposto_devido = apuracao_csll.base_calculo_total * (alicota.CSLL_BASE_CAL /100)
        apuracao_csll.imposto_pagar =  apuracao_csll.imposto_devido - apuracao_csll.imposto_retido 
        
        #IRPJ imposto devido = alicota 15%
        apuracao_irpj.imposto_devido =  apuracao_irpj.base_calculo_total * (alicota.IRPJ_BASE_CAL /100) 

        #opa: IRPJ tem imposto adicional se ultrapassar limite 
        if ( apuracao_irpj.base_calculo > alicota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL):
            apuracao_irpj.imposto_adicional = (apuracao_irpj.base_calculo_total - alicota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL) * (alicota.IRPJ_ADICIONAL/100)

        apuracao_irpj.imposto_pagar = apuracao_irpj.imposto_devido +  apuracao_irpj.imposto_adicional - apuracao_irpj.imposto_retido - apuracao_irpj.irrf_aplicacao
        
        # ufa! terminou
        apuracao_csll.save()
        apuracao_irpj.save()

    return 

# ------------------------------------------------------------------------------------------------------------------------------
def monta_apuracao_issqn(request, empresa_pk):

    fornecedor = Empresa.objects.get(id=empresa_pk)
    periodo_fiscal = request.session['periodo_fiscal']

    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    #fornecedor = Pjuridica.objects.get(id=empresa_id)
    alicota = Alicotas.objects.get(id = 1)

    #---------------------------------------------------------------------------------------------------------------------
    for mes in range(1,13):
        
        # inicia tabela Apuracao_pis do mes
        data_inicial = get_data(periodo_fiscal.year, mes)
        iss_balanco, created = Apuracao_iss.objects.get_or_create(data = data_inicial, fornecedor = fornecedor)
        if created == True:
            iss_balanco.save()

        # busca o faturamento bruto e o  pis pago no mes
        ds_fat_ISS= NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month= mes, fornecedor = fornecedor) \
                                        .values('fornecedor') \
                                        .order_by('fornecedor') \
                                        .annotate(val_bruto=Sum('val_bruto')) \
                                        .annotate(isqn=Sum('val_ISS'))                                           


        if (ds_fat_ISS):
            for valor in ds_fat_ISS:
                iss_balanco.base_calculo    =  valor.get('val_bruto')
                iss_balanco.imposto_retido  =  valor.get('isqn')
        
            iss_balanco.imposto_devido = round((iss_balanco.base_calculo * (alicota.ISS / 100)),2)
            iss_balanco.imposto_pagar =  round((iss_balanco.imposto_devido - iss_balanco.imposto_retido ),2)

            # salva mes atual
            iss_balanco.save()

    return 

#----------------------------------------------------------
def monta_apuracao_pis(request):
    
    fornecedor = Empresa.objects.get(id=empresa_id)
    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    #fornecedor = Pjuridica.objects.get(id=empresa_id)
    alicota = Alicotas.objects.get(id = 1)
    
    saldo_mes_anterior = 0   # acumula saldo para mes seguinte, se imposto a pagar < 10 reais
    for mes in range(1,13):
        
        # inicia tabela Apuracao_pis do mes
        data_inicial = get_data(periodo_fiscal.year, mes)
        ds_pis_balanco, created = Apuracao_pis.objects.get_or_create(data = data_inicial, fornecedor = fornecedor)
        if created == True:
            ds_pis_balanco.save()

        ds_pis_balanco.saldo_mes_anterior = saldo_mes_anterior

        # busca o faturamento bruto - base de cálculo
        ds_fat_mes = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month= mes, fornecedor = fornecedor) \
                                        .values('fornecedor') \
                                        .order_by('fornecedor') \
                                        .annotate(val_bruto=Sum('val_bruto')) \


        if (ds_fat_mes):
            #for faturamento in ds_fat_mes:
            faturamento = ds_fat_mes.first()
            ds_pis_balanco.base_calculo = faturamento.get('val_bruto')


        # busca pis retido no mes
        ds_pis_retido = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month= mes, fornecedor = fornecedor) \
                                        .values('fornecedor') \
                                        .order_by('fornecedor') \
                                        .annotate(val_pis=Sum('val_PIS'))
        
        if (ds_pis_retido):
            # calculo PIS
            pis_retido = ds_pis_retido.first()
            ds_pis_balanco.imposto_retido  =  pis_retido.get('val_pis')


            ds_pis_balanco.saldo_mes_anterior = saldo_mes_anterior
            ds_pis_balanco.imposto_devido = round((ds_pis_balanco.base_calculo * (alicota.PIS / 100)),2)
            ds_pis_balanco.imposto_pagar =  round((ds_pis_balanco.imposto_devido - ds_pis_balanco.imposto_retido + ds_pis_balanco.saldo_mes_anterior ),2)
            
            # se imposto a pagar < 10, transfere para o mes seguinte
            if(ds_pis_balanco.imposto_pagar < 10):
                saldo_mes_anterior =  ds_pis_balanco.imposto_pagar   
                ds_pis_balanco.saldo_mes_seguinte = ds_pis_balanco.imposto_pagar

                ds_pis_balanco.imposto_pagar=  0
            else:  # incluido para corrigir evitar saldo negativo
                saldo_mes_anterior = 0

            # salva mes atual
            ds_pis_balanco.save()
            
    return 

#----------------------------------------------------------
def monta_apuracao_cofins(request):
    
    fornecedor = Empresa.objects.get(id=empresa_id)
    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    #fornecedor = Pjuridica.objects.get(id=empresa_id)
    alicota = Alicotas.objects.get(id = 1)

    # acumula saldo para mes seguinte, se imposto a pagar < 10 reais
    saldo_mes_anterior = 0
    for mes in range(1,13):
        
        # inicia tabela Apuracao_pis do mes
        data_inicial = get_data(periodo_fiscal.year, mes)
        ds_cofins_balanco, created = Apuracao_cofins.objects.get_or_create(data = data_inicial, fornecedor = fornecedor)
        if created == True:
            ds_cofins_balanco.save()

        ds_cofins_balanco.saldo_mes_anterior = saldo_mes_anterior

        # faturamento bruto - base de cálculo
        ds_fat_mes =  NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month= mes, fornecedor = fornecedor)\
                                        .values('fornecedor') \
                                        .order_by('fornecedor') \
                                        .annotate(val_bruto=Sum('val_bruto')) \

        # calculo COFINS
        if (ds_fat_mes):
            faturamento = ds_fat_mes.first()
            ds_cofins_balanco.base_calculo=  faturamento.get('val_bruto') 
        else:
            ds_cofins_balanco.base_calculo= 0

        # cofins retido no mes
        ds_cofins_retido =  NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month= mes, fornecedor = fornecedor)\
                                        .values('fornecedor') \
                                        .order_by('fornecedor') \
                                        .annotate(val_cofins=Sum('val_COFINS'))
        
        if (ds_cofins_retido):
            cofins_retido = ds_cofins_retido.first()
            ds_cofins_balanco.imposto_retido =  cofins_retido.get('val_cofins') 
        else:
            ds_cofins_balanco.imposto_retido = 0
        
        # efetua calculo
        ds_cofins_balanco.imposto_devido =  round((ds_cofins_balanco.base_calculo * (alicota.COFINS /100)),2)
        ds_cofins_balanco.imposto_pagar =  round((ds_cofins_balanco.imposto_devido - ds_cofins_balanco.imposto_retido + ds_cofins_balanco.saldo_mes_anterior),2) 

        # se imposto a pagar < 10, transfere para o mes seguinte
        if(ds_cofins_balanco.imposto_pagar < 10):
            saldo_mes_anterior =  ds_cofins_balanco.imposto_pagar   
            ds_cofins_balanco.saldo_mes_seguinte = ds_cofins_balanco.imposto_pagar
        else:  # incluido para corrigir evitar saldo negativo
            saldo_mes_anterior = 0

        # salva mes atual
        ds_cofins_balanco.save()

    return 

#------------------------------------------------------------------------------------------
def monta_balanco_ano(request, socio_id, periodo_fiscal):

    #periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    #periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
    for mes in range(1,13):
        
        data = get_data_new(periodo_fiscal.year,mes)
        monta_balanco(request,socio_id,data)
             
    return

#------------------------------------------------------------------------------------------
#def monta_balanco(request, socio_id):
def monta_balanco(request, socio_id, periodo_fiscal):
    
    id_empresa = request.session['empresa_id']
    #periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    #periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()

    fornecedor = Empresa.objects.get(id=id_empresa)
    socio = Socio.objects.get(id=socio_id)
    alicota = Alicotas.objects.get(id = 1)

    # teste 
    #calc_apuracao_ir_adicional_socio_trimestre(request, fornecedor.id,socio.id)

    # cria relatorio
    dsBalanco, qry_created = Balanco.objects.get_or_create( data__year = periodo_fiscal.year, 
                                                            data__month = periodo_fiscal.month,
                                                            socio=socio, 
                                                            defaults= {
                                                                        'data'  : periodo_fiscal,
                                                                        'empresa': fornecedor,
                                                                        })
    if qry_created:
        dsBalanco.save()

    dsBalanco.faturamento_servicos_consultas = 0
    dsBalanco.faturamento_servicos_plantao = 0
    dsBalanco.faturamento_servicos_outros = 0
    dsBalanco.imposto_csll_imposto_retido = 0
    dsBalanco.imposto_irpj_imposto_retido = 0
    #-------------------------------------
    dsBalanco.recebido_consultas = 0
    dsBalanco.recebido_plantao = 0
    dsBalanco.recebido_outros = 0

    #------------------------------------------------------------------------------
    # FLUXO DE CAIXA - NOTAS EMITIDAS
    #------------------------------------------------------------------------------
    ds_notas_emitidas = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month = periodo_fiscal.month, socio = socio) \
                                                            .values('socio')\
                                                            .order_by('socio')\
                                                            .annotate(sum_notas_emitidas=Sum('val_bruto'))
    if (ds_notas_emitidas):
        notas_emitidas = ds_notas_emitidas.first()
        dsBalanco.receita_bruta_notas_emitidas = notas_emitidas.get('sum_notas_emitidas')
    else:
        dsBalanco.receita_bruta_notas_emitidas = 0

    #------------------------------------------------------------------------------
    # FLUXO DE CAIXA - NOTAS RECEBIDAS
    #------------------------------------------------------------------------------
    # recebidos no mes = fluxo de caixa de valores recebidos -> dtRecebimento da nota

    qry_recebido_consultas = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_CONSULTAS) \
                                                            .values('socio')\
                                                            .order_by('socio')\
                                                            .annotate(recebido=Sum('val_bruto'))
    if (qry_recebido_consultas):
        rec_consultas = qry_recebido_consultas.first()
        dsBalanco.recebido_consultas = rec_consultas.get('recebido')
    #--

    qry_recebido_plantao = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_PLANTAO) \
                                                            .values('socio')\
                                                            .order_by('socio')\
                                                            .annotate(recebido=Sum('val_bruto'))

    if (qry_recebido_plantao):
        rec_plantao = qry_recebido_plantao.first()
        dsBalanco.recebido_plantao = rec_plantao.get('recebido')

    #--
    qry_recebido_outros = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_OUTROS) \
                                                            .values('socio')\
                                                            .order_by('socio')\
                                                            .annotate(recebido=Sum('val_bruto'))

    if (qry_recebido_outros):
        rec_outros = qry_recebido_outros.first()
        dsBalanco.recebido_outros = rec_outros.get('recebido')


    #-------------------------------------------------------------------------
    # Total recebido em caixa = NOTAS RECEBIDAS
    #-------------------------------------------------------------------------
    dsBalanco.recebido_total = dsBalanco.recebido_consultas + dsBalanco.recebido_plantao + dsBalanco.recebido_outros

    #-------------------------------------------------------------------------
    # MOVIMENTAÇÃO CONTABEIS
    #-------------------------------------------------------------------------

    # calcula resultado final das operações financeiras = debito + credito
    ds_movimento= Financeiro.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio)

    total_movimento_financeiro = 0
    if (ds_movimento):
        for operacao in ds_movimento:
            if (operacao.tipo == TIPO_MOVIMENTACAO_CONTA_CREDITO):
                total_movimento_financeiro += operacao.valor 
            else:
                total_movimento_financeiro -= operacao.valor 

    dsBalanco.saldo_movimentacao_financeira = total_movimento_financeiro
    #--

    ds_resumo_financeiro= Financeiro.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio)\
                                                            .values('descricao')\
                                                            .annotate(valor=Sum('valor'))

    #-------------------------------------------------------------------------
    # IMPOSTOS
    #-------------------------------------------------------------------------

    # REGIME_TRIBUTACAO_COMPETENCIA = considera mes de emissão da nota fiscal
    if (fornecedor.tipo_regime == REGIME_TRIBUTACAO_COMPETENCIA ):
            
            # recupera notas ficais tipo de alicota= serviços de consultas          
            qry_fat_alicota_consultas = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_CONSULTAS) \
                                                            .values('socio')\
                                                            .order_by('socio')\
                                                            .annotate(faturamento=Sum('val_bruto')) \
                                                            .annotate(csll=Sum('val_CSLL')) \
                                                            .annotate(irpj=Sum('val_IR'))
            
            # recupera notas ficais tipo de alicota= serviços de plantao          
            qry_fat_alicota_plantao = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_PLANTAO) \
                                                            .values('socio')\
                                                            .order_by('socio')\
                                                            .annotate(faturamento=Sum('val_bruto')) \
                                                            .annotate(csll=Sum('val_CSLL')) \
                                                            .annotate(irpj=Sum('val_IR'))
                     
            # recupera notas ficais tipo de alicota= serviços outros         
            qry_fat_alicota_outros = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_OUTROS) \
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(csll=Sum('val_CSLL')) \
                                                            .annotate(irpj=Sum('val_IR'))


    # REGIME_TRIBUTACAO_EXERCICIO/CAIXA = considera mes de recebimento da nota fiscal
    else:
        # recupera notas ficais tipo de alicota= serviços de consultas 
        qry_fat_alicota_consultas = NotaFiscal.objects.filter(dRecebimento__year = periodo_fiscal.year, dRecebimento__month = periodo_fiscal.month, socio = socio,  tipo_aliquota = NFISCAL_ALICOTA_CONSULTAS)\
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(faturamento=Sum('val_bruto')) \
                                                            .annotate(csll=Sum('val_CSLL')) \
                                                            .annotate(irpj=Sum('val_IR'))

        # recupera notas ficais tipo de alicota= serviços de plantao 
        qry_fat_alicota_plantao = NotaFiscal.objects.filter(dRecebimento__year = periodo_fiscal.year, dRecebimento__month = periodo_fiscal.month, socio = socio,  tipo_aliquota = NFISCAL_ALICOTA_PLANTAO)\
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(faturamento=Sum('val_bruto')) \
                                                            .annotate(csll=Sum('val_CSLL')) \
                                                            .annotate(irpj=Sum('val_IR'))
        
        # recupera notas ficais tipo de alicota= serviços outros            
        qry_fat_alicota_outros = NotaFiscal.objects.filter(dRecebimento__year = periodo_fiscal.year, dRecebimento__month = periodo_fiscal.month, socio = socio, tipo_aliquota = NFISCAL_ALICOTA_OUTROS) \
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(faturamento=Sum('val_bruto'))   \
                                                            .annotate(csll=Sum('val_CSLL')) \
                                                            .annotate(irpj=Sum('val_IR'))

    #for fat_consultas in qry_fat_alicota_consultas:
    if (qry_fat_alicota_consultas):
        fat_consultas = qry_fat_alicota_consultas.first()
        dsBalanco.faturamento_servicos_consultas = fat_consultas.get('faturamento')
        dsBalanco.imposto_csll_imposto_retido = fat_consultas.get('csll')
        dsBalanco.imposto_irpj_imposto_retido = fat_consultas.get('irpj')

    #for fat_consultas in qry_fat_alicota_plantao:
    if (qry_fat_alicota_plantao):
        fat_plantao = qry_fat_alicota_plantao.first()
        dsBalanco.faturamento_servicos_plantao = fat_plantao.get('faturamento')
        # soma com imposto retido do alicota consultas !!!!
        dsBalanco.imposto_csll_imposto_retido += fat_plantao.get('csll')
        dsBalanco.imposto_irpj_imposto_retido += fat_plantao.get('irpj')

    #for fat_outros in qry_fat_alicota_outros:
    if (qry_fat_alicota_outros):
        fat_outros = qry_fat_alicota_outros.first()
        dsBalanco.faturamento_servicos_outros = fat_outros.get('faturamento')
        # soma com imposto retido do alicota consultas !!!!
        dsBalanco.imposto_csll_imposto_retido += fat_outros.get('csll')
        dsBalanco.imposto_irpj_imposto_retido += fat_outros.get('irpj')
 
    #----------------------------------------------------------------------------
    # Receita bruta para calculos dos tributos
    #----------------------------------------------------------------------------
    dsBalanco.receita_bruta_total = dsBalanco.faturamento_servicos_consultas + dsBalanco.faturamento_servicos_plantao + dsBalanco.faturamento_servicos_outros

    #----------------------------------------------------------------------------
    # IMPOSTO TOTAL
    #----------------------------------------------------------------------------

    # PIS
    dsBalanco.imposto_PIS_devido = dsBalanco.receita_bruta_total * (alicota.PIS / 100)

    # COFINS
    dsBalanco.imposto_COFINS_devido = dsBalanco.receita_bruta_total * (alicota.COFINS / 100)

    # CSLL 
    dsBalanco.imposto_csll_base_calculo = ((dsBalanco.faturamento_servicos_consultas + dsBalanco.faturamento_servicos_plantao) * (alicota.CSLL_ALIC_2/100) ) + (dsBalanco.faturamento_servicos_outros * alicota.CSLL_ALIC_1 /100)

    # CSLL imposto devido = 9%
    dsBalanco.imposto_csll_imposto_devido = dsBalanco.imposto_csll_base_calculo * (alicota.CSLL_BASE_CAL /100)
    dsBalanco.imposto_csll_imposto_pagar = dsBalanco.imposto_csll_imposto_devido - dsBalanco.imposto_csll_imposto_retido

    # IRPJ 
    dsBalanco.imposto_irpj_base_calculo = ((dsBalanco.faturamento_servicos_consultas + dsBalanco.faturamento_servicos_plantao) * (alicota.IRPJ_ALIC_2/100)) + (dsBalanco.faturamento_servicos_outros * alicota.IRPJ_ALIC_1 /100)
    dsBalanco.imposto_irpj_imposto_devido = dsBalanco.imposto_irpj_base_calculo * (alicota.IRPJ_BASE_CAL /100)
    
    # CALCULA IMPOSTO ADICIONAL ???
    #calc_apuracao_ir_adicional_socio_trimestre(request, fornecedor.id,socio.id)
    #dsBalanco.imposto_irpj_imposto_devido += dsBalanco.imposto_irpj_imposto_adicional
    dsBalanco.imposto_irpj_imposto_pagar = dsBalanco.imposto_irpj_imposto_devido + dsBalanco.imposto_irpj_imposto_adicional - dsBalanco.imposto_irpj_imposto_retido

    # ISS
    dsBalanco.imposto_iss_imposto_devido = dsBalanco.receita_bruta_total  * (alicota.ISS / 100)

    # IMPOSTO TOTAL = CSLL + IRPJ + PIS + COFINS + ISS
    dsBalanco.imposto_total = dsBalanco.imposto_csll_imposto_devido + dsBalanco.imposto_irpj_imposto_devido + dsBalanco.imposto_irpj_imposto_adicional +\
                                dsBalanco.imposto_PIS_devido + dsBalanco.imposto_COFINS_devido + dsBalanco.imposto_iss_imposto_devido

    #-------------------------------------------------------------------------
    # faturamento líquido
    #-------------------------------------------------------------------------

    #dsBalanco.receita_liquida_total = dsBalanco.receita_bruta_total - dsBalanco.imposto_total
    dsBalanco.receita_liquida_total = dsBalanco.recebido_total - dsBalanco.imposto_total

    #-------------------------------------------------------------------------
    # despesas socio/SOCIO
    #-------------------------------------------------------------------------
    #rev: 241216_0930
    #ds_despesa_socio_total = Despesa.objects.filter(data__year=ano_fiscal, data__month=mes, socio = socio, tipo_rateio = TIPO_DESPESA_SEM_RATEIO) \
    ds_despesa_socio_total = Despesa.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, socio = socio, tipo_rateio = TIPO_DESPESA_SEM_RATEIO) \
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(valor=Sum('valor'))
    
    if (ds_despesa_socio_total):
        despesa_socio_total = ds_despesa_socio_total.first()
        dsBalanco.despesa_sem_rateio = despesa_socio_total.get('valor')        
    else:
        dsBalanco.despesa_sem_rateio = 0 

    #-------------------------------------------------------------------------
    # despesas rateio  
    #-------------------------------------------------------------------------

    # Calcula o rateio das despesas
    dsBalanco.despesa_com_rateio = 0
    ds_desp_socio = Despesa_socio_rateio.objects.filter(despesa__data__year=periodo_fiscal.year, despesa__data__month=periodo_fiscal.month, socio=socio, fornecedor = fornecedor ) 
    for desp_socio in ds_desp_socio:
    #if (ds_desp_socio): 
        #desp_socio = ds_desp_socio.first()
        desp_socio.vl_rateio = (desp_socio.percentual / 100) * desp_socio.despesa.valor
        desp_socio.save()
        dsBalanco.despesa_com_rateio += desp_socio.vl_rateio
 
    #-------------------------------------------------------------------------
    # despesas folha 
    #-------------------------------------------------------------------------
    dsBalanco.despesa_folha_rateio = 0
    ds_desp_folha = Despesa_socio_rateio.objects.filter(despesa__data__year=periodo_fiscal.year, despesa__data__month=periodo_fiscal.month, socio=socio, despesa__item__grupo__codigo = CODIGO_GRUPO_DESPESA_FOLHA)
    if (ds_desp_folha):
        desp_folha = ds_desp_folha.first()
        dsBalanco.despesa_folha_rateio  += desp_folha.vl_rateio
 
    #-------------------------------------------------------------------------
    # despesas geral 
    #-------------------------------------------------------------------------
    dsBalanco.despesa_geral_rateio = 0
    ds_desp_geral= Despesa_socio_rateio.objects.filter(despesa__data__year=periodo_fiscal.year, despesa__data__month=periodo_fiscal.month,  socio=socio, despesa__item__grupo__codigo = CODIGO_GRUPO_DESPESA_GERAL)
    for desp_geral in ds_desp_geral:
        dsBalanco.despesa_geral_rateio  += desp_geral.vl_rateio
    
    #-------------------------------------------------------------------------
    # despesas total = despesa socio + despesa do rateio
    #-------------------------------------------------------------------------
    #dsBalanco.despesa_total = dsBalanco.despesa_sem_rateio + dsBalanco.despesa_com_rateio
    dsBalanco.despesa_total = dsBalanco.despesa_sem_rateio + dsBalanco.despesa_folha_rateio + dsBalanco.despesa_geral_rateio 

    #-------------------------------------------------------------------------
    # SALDO APURADO E SALDO A TRANSFERIR 
    #-------------------------------------------------------------------------

    #dsBalanco.saldo_apurado = dsBalanco.recebido_total - dsBalanco.imposto_total - dsBalanco.despesa_sem_rateio - dsBalanco.despesa_com_rateio
    dsBalanco.saldo_apurado = dsBalanco.recebido_total - dsBalanco.imposto_total - dsBalanco.despesa_total
    dsBalanco.saldo_a_transferir = dsBalanco.saldo_apurado + dsBalanco.saldo_movimentacao_financeira 

    # salva relatorio!!! UFA
    dsBalanco.save()

    #-------------------------------------------------------------------------
    # CALCULO IR ADICIONAL A CADA TRIMESTRE
    #-------------------------------------------------------------------------
    #calc_apuracao_ir_adicional_socio_trimestre(request, fornecedor.id,socio.id)
    
    return dsBalanco

#----------------------------------------------------------  
def clonar_despesa_mes_anterior(request, periodo_fiscal):
    
    empresa_id = request.session['empresa_id']
    fornecedor = Empresa.objects.get(id=empresa_id)  # Corrigido
    data_anterior = sub_months(periodo_fiscal,1)
    ds_desp_anterior = Despesa.objects.filter(data__year=data_anterior.strftime('%Y'), data__month = data_anterior.strftime('%-m'), empresa=fornecedor)
    
    # Despesas coletivas mes anterior
    for desp_anterior in ds_desp_anterior:
        desp_new, created = Despesa.objects.update_or_create (
                                                data__year = periodo_fiscal.year, 
                                                data__month = periodo_fiscal.month,
                                                empresa = fornecedor, 
                                                item = desp_anterior.item,
                                                socio = desp_anterior.socio,
                                                #-- cria se não encontrar   / atualiza se existir
                                                defaults={   
                                                            'data'          : periodo_fiscal,
                                                            'valor'         : desp_anterior.valor,
                                                            'tipo_rateio'   : desp_anterior.tipo_rateio,
                                                            'descricao'     : desp_anterior.descricao,
                                                        },)  
        if created: 
            desp_new.save()

        # atualiza a tabela de despesa de rateio dos sócios
        qry_socios = Socio.objects.filter(pjuridica = fornecedor)
        for socio in qry_socios:
            
            # busca despesa rateio mes anterior
            try: 
                desp_rateio_anterior = Despesa_socio_rateio.objects.get(despesa__data__year  = periodo_fiscal.year,  
                                                                        #despesa__data__month = mes_anterior, 
                                                                        despesa__data__month = data_anterior.strftime('%-m'), 
                                                                        socio=socio,\
                                                                        despesa__item = desp_anterior.item)
                
                # insere ou atualiza mes atual
                ds_desp_rateio_new, created = Despesa_socio_rateio.objects.update_or_create(
                                                                        fornecedor = fornecedor,  # corrigido
                                                                        socio = socio,
                                                                        despesa = desp_new,
                                                                        defaults={   
                                                                            'percentual': desp_rateio_anterior.percentual,
                                                                                },)  

                if created:
                    ds_desp_rateio_new.save()
            except:
                pass


    return

#-------------------------------------------------------------------------------------------------
def calc_apuracao_ir_adicional_socio_trimestre(request, empresa_id, socio_id):

    periodo_fiscal = request.session['periodo_fiscal'] + '-01'
    periodo_fiscal = datetime.datetime.strptime(periodo_fiscal, "%Y-%m-%d").date()
    socio = Socio.objects.get(id=socio_id)

    msg =  'calc_apuracao_ir_adicional_socio_trimestre(): ENTREI' 
    messages.error(request, msg )
    
    # verifia se mes atual é fechamento de trimestre
    ir_adicional_socio = 11111
    modulo_mes = periodo_fiscal.month % 3
    if (modulo_mes!=0):
        msg =  'calc_apuracao_ir_adicional_socio_trimestre(): NÃO É TRIMESTRE' 
        messages.error(request, msg )
        ir_adicional_socio = 0
        return  ir_adicional_socio # não é fechamento de mes

    # calculo tributo Trimestral
    mes_inicial = periodo_fiscal.month - 2
    mes_final   = periodo_fiscal.month

    # REGIME_TRIBUTACAO_COMPETENCIA = considera mes de emissão da nota fiscal
    if (socio.empresa.tipo_regime == REGIME_TRIBUTACAO_COMPETENCIA ):
        ds_faturamento_socio_trimestre = NotaFiscal.objects.filter(dtEmissao__year = periodo_fiscal.year, dtEmissao__month__range=(mes_inicial, mes_final), socio=socio) \
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(receita_bruta=Sum('val_bruto')) 
    # REGIME_TRIBUTACAO_CAIXA = considera mes de recebimento da nota fiscal
    else:
        ds_faturamento_socio_trimestre = NotaFiscal.objects.filter(dtRecebimento__year = periodo_fiscal.year, dtRecebimento__month__range=(mes_inicial, mes_final), socio=socio ) \
                                                            .values('socio') \
                                                            .order_by('socio') \
                                                            .annotate(receita_bruta=Sum('val_bruto'))
        #messages.error(request, "passei pelo regime caixa")
    # IF END

    #----------------------------------------------------------------------------------------------------------------------------------------------
    if (ds_faturamento_socio_trimestre):
            fat_socio_bruto= ds_faturamento_socio_trimestre.first()
            receita_bruta_notasfiscais_trimestre = fat_socio_bruto.get('receita_bruta')
    else:
        receita_bruta_notasfiscais_trimestre = 0
        msg = 'monta_apuracao_ir_adicional_socio(): FALHA RECUPERAÇÃO IRPJ TRIMESTRAL:' + str( data_trimestre)
        messages.error(request, msg  )
        ir_adicional_socio = 0
        return ir_adicional_socio
    
    # recupera ir adicional da empresa para calcular/ratear com os sócios.
    data_trimestre = periodo_fiscal
    try:
        trimestre = data_trimestre.month / 3
        apuracao_irpj_trimestre = Apuracao_irpj.objects.get(data__year = data_trimestre.year,
                                                            data__month = trimestre,    # tem um erro no data_month. Não é month que está armazenado e sim o trimestre !!!!!!!!!!!!!!!!!!!!
                                                            fornecedor=empresa_id)
    except:
        msg = 'calc_apuracao_ir_adicional_socio_trimestre(): Montando apuração de CSLL/IRPJ: Tente novamente!' + str( data_trimestre.year) + " / " + str( data_trimestre.month)
        messages.error(request, msg )
        monta_apuracao_csll_irpj_new()
        ir_adicional_socio = 0
        return ir_adicional_socio
            
    relacao_fat_socio_fat_empresa = round((receita_bruta_notasfiscais_trimestre / apuracao_irpj_trimestre.receita_bruta),2)
    ir_adicional_socio = apuracao_irpj_trimestre.imposto_adicional * relacao_fat_socio_fat_empresa

    msg = 'CALCULEI ADICIONAL= ' + str(ir_adicional_socio)
    messages.error(request, msg )

    # busca balanço referente à data do calculo do trimestre
    balanco_trimestre = Balanco.objects.get( data = data_trimestre, socio=socio )
    balanco_trimestre.imposto_irpj_imposto_adicional = ir_adicional_socio
    balanco_trimestre.receita_bruta_trimestre = receita_bruta_notasfiscais_trimestre
    balanco_trimestre.save() # TESTE SE SALVAR AQUI DÁ EFEITO NO BALANÇO ??????

    return ir_adicional_socio

#----------------------------------------------------------  
def importar_xml(request, fornecedor):
    
    try:
        xml_file = request.FILES['file']
    except KeyError:
        raise ValueError("Nenhum arquivo XML foi enviado.")
    doc = xmltodict.parse(xml_file)

    xml_nf_numero = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["Numero"]
    xml_nf_dtEmissao= doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Competencia"]

    xml_nf_val_liquido = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["ValoresNfse"]["ValorLiquidoNfse"]
    xml_nf_val_bruto= doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorServicos"]
    xml_nf_val_pis = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorPis"]
    xml_nf_val_cofins = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorCofins"]
    xml_nf_val_inss = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorInss"]
    xml_nf_val_ir = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorIr"]
    xml_nf_val_csll = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorCsll"]
    xml_nf_val_iss = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Servico"]["Valores"]["ValorIss"]

    xml_nf_prestador_razaosocial= doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["PrestadorServico"]["RazaoSocial"]
    xml_nf_prestador_cnpj = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["Prestador"]["CpfCnpj"]["Cnpj"]
    xml_nf_tomador_razaosocial = doc["EnviarLoteRpsSincronoResposta"]["ListaNfse"]["CompNfse"]["Nfse"]["InfNfse"]["DeclaracaoPrestacaoServico"]["InfDeclaracaoPrestacaoServico"]["TomadorServico"]["RazaoSocial"]

    notafiscal, created = NotaFiscal.objects.update_or_create (
                                                numero = xml_nf_numero, 
                                                dtEmissao = xml_nf_dtEmissao, 
                                                tomador = xml_nf_tomador_razaosocial, 
                                                fornecedor = fornecedor,
                                                socio = None,
                                                #-- cria se não encontrar   / atualiza se existir
                                                defaults={   
                                                            'val_bruto'     : xml_nf_val_bruto,
                                                            'val_liquido'   : xml_nf_val_liquido,
                                                            'val_PIS'       : xml_nf_val_pis,
                                                            'val_COFINS'    : xml_nf_val_cofins,
                                                            'val_ISS'       : xml_nf_val_iss,
                                                            'val_IR'        : xml_nf_val_ir,
                                                            'val_CSLL'      : xml_nf_val_csll,
                                                        },)  
    if created: 
        notafiscal.save()

    return notafiscal