import babel.dates
from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape, letter, portrait, inch
from reportlab.lib.units import inch, mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, NextPageTemplate, PageBreak, SimpleDocTemplate, Spacer, BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors

from django.db.models import Max, Subquery
import datetime
from .models import *
from io import BytesIO, StringIO

from babel.numbers import format_number, format_decimal, format_compact_decimal, format_percent
import babel.numbers
from datetime import datetime as dt
import pandas as pd
from functools import partial
from reportlab.lib.styles import ParagraphStyle as PS
from django.db.models import Avg, Count, Min, Sum, Max

def gerar_relatorio_socio(request, socio_id):
    empresa_id = request.session['empresa_id']
    fornecedor = Empresa.objects.get(id=empresa_id)
    socio = Socio.objects.get(id=socio_id)

    now=datetime.datetime.now()
    buffer = BytesIO()

    #----------------------------------------------------------------------------#
    filename = "DEMONSTRATIVO_DE_RESULTADOS_" + socio.pessoa.name + "_" + str(periodo_fiscal) + ".pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + filename


    #----------------------------------------------------------------------------#
    #   TESTETE    de redefinição do pageTemplate da firstPage- funciona!!!!                                                
    #----------------------------------------------------------------------------#

    class MyDocTemplate(BaseDocTemplate):

        def __init__(self, filename, **kw):
            self.allowSplitting = 0
            BaseDocTemplate.__init__(self, filename, **kw)

            #template_CoverPage = PageTemplate('CoverPage',[Frame(2.0 *cm, 2.0*cm, 17.5*cm, 26*cm, id='F1')],pagesize=portrait(A4), onPage=foot1)
            template_CoverPage = PageTemplate('CoverPage',frame_portrait_teste, pagesize=portrait(A4), onPage=foot1)

            self.addPageTemplates([template_CoverPage])


        def afterFlowable(self, flowable):
            "Registers TOC entries."
            if flowable.__class__.__name__ == 'Paragraph':
                text = flowable.getPlainText()
                style = flowable.style.name
                if style == 'Heading1':
                    self.notify('TOCEntry', (0, text, self.page))
                if style == 'Heading2':
                    self.notify('TOCEntry', (1, text, self.page))

    h1 = PS(name = 'Heading1',
        fontSize = 14,
        leading = 16)

    h2 = PS(name = 'Heading2',
        fontSize = 12,
        leading = 14,
        leftIndent = 5)
    l0 = PS(name = 'list0',
            fontSize = 12,
            leading =14,
            leftIndent=0,
            rightIndent=0,
            spaceBefore = 12,
            spaceAfter =0
            )

    '-----------------------------------------------------------------------------'
    'Header and Footer'
    '-----------------------------------------------------------------------------'
    def header(canvas, doc, content):
        canvas.saveState()
        w, h = content.wrap(doc.width, doc.topMargin)
        content.drawOn(canvas, doc.leftMargin-22.4, doc.height + doc.bottomMargin + doc.topMargin - h-25)
        canvas.restoreState()

    def footer(canvas, doc, content):
        drawPageNumber(canvas, doc)
        canvas.saveState()
        w, h = content.wrap(doc.width, doc.bottomMargin)
        content.drawOn(canvas, doc.leftMargin-22.4, h)
        canvas.restoreState()

    def header_and_footer(canvas, doc, header_content, footer_content):
        header(canvas, doc, header_content)
        footer(canvas, doc, footer_content)

    def drawPageNumber(canvas, doc):
        pageNumber = canvas.getPageNumber()
        canvas.setFont("Arial",11)
        canvas.drawCentredString(17.4*cm, 1.35*cm, 'Page '+str(pageNumber))

    def PageNumber(canvas, doc):
        return(canvas.getPageNumber())

    header_center_text='header_center_text foo'
    footer_center_text='footer_center_text bar'  

    def foot1(canvas,doc):
        canvas.saveState()
        footerBotton = doc.bottomMargin - 20
        lineLength = doc.width + doc.leftMargin
        canvas.setFont('Times-Roman',8)
        '''
        canvas.setFont('Times-Roman',8)
        #canvas.drawString(inch, 0.75 * inch, "Pag: %d" % doc.page + "Arquivo: %s" % filename)
        canvas.drawString(inch, 0.75 * inch, "Pag:%d" % doc.page + "/ Emitido em: %s" % now.strftime("%m/%d/%Y %H:%M:%S"))
        canvas.restoreState()
        '''

        # FOOTER #

        canvas.drawString(doc.leftMargin, footerBotton , "MILENIO CONTABILIDADE LTDA" )
        canvas.drawString(doc.leftMargin, footerBotton - 10, "www.mileniocontabilidade.com.br" )
        canvas.drawString(doc.leftMargin, footerBotton - 20 , "Pagina:%d" % doc.page + "  / Emitido em: %s" % now.strftime("%m/%d/%Y %H:%M:%S")) 

        # on left
        canvas.drawRightString(lineLength, footerBotton, "SIRCO - SISTEMA DE ROTINAS CONTÁBEIS "  )
        canvas.drawRightString(lineLength, footerBotton - 10 , "Descomplique a sua rotina" )
        canvas.drawRightString(lineLength, footerBotton - 20 , "CONTATO: (031) 9.8852-4188" )

        canvas.restoreState()

    doc_teste = BaseDocTemplate(buffer, showBoundary= False, pagesize=A4)
    frame_portrait_teste = Frame(doc_teste.leftMargin, doc_teste.bottomMargin, doc_teste.width, doc_teste.height,                     id='normal')

    #----------------------------------------------------------------------------#

    #doc = BaseDocTemplate(buffer, showBoundary= False, pagesize=A4)
    doc = MyDocTemplate(buffer, showBoundary= False, pagesize=A4)

    #----------------------------------------------------------------------------#
    # STYLES                                                                     #   
    #----------------------------------------------------------------------------#
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='centered', alignment=TA_CENTER))

    styleBH = styles["Normal"]
    styleBH.alignment = TA_CENTER

    styleN = styles["BodyText"]
    styleN.alignment = TA_LEFT

    #----------------------------------------------------------------------------#
    # FORMATAÇÃO                                                                 #   
    #----------------------------------------------------------------------------#

    def foot1(canvas,doc):
        canvas.saveState()
        canvas.setFont('Times-Roman',8)
        #canvas.drawString(inch, 0.75 * inch, "Pag: %d" % doc.page + "Arquivo: %s" % filename)
        canvas.drawString(inch, 0.75 * inch, "Pag:%d" % doc.page + "/ Emitido em: %s" % now.strftime("%m/%d/%Y %H:%M:%S"))
        canvas.restoreState()

    #-----------------------------------------------------------------
    # para formato landscape
    def header_landscape(canvas, doc):
        # header
        canvas.saveState()
        canvas.setFont('Times-Roman',8)

        canvas.saveState()
        fontsize = 10
        fontname = 'Times-Roman'
        #headerBottom = doc.bottomMargin + doc.height + doc.topMargin /2
        headerBottom = doc.bottomMargin + doc.width + doc.topMargin /2
        bottomLine = headerBottom - fontsize/4
        topLine = headerBottom + fontsize
        lineLength = doc.width + doc.leftMargin
        canvas.setFont(fontname,fontsize)

        canvas.drawString(doc.leftMargin, headerBottom - 10, "   Demonstrativo de Resultados: "  + str(periodo_fiscal.month) + "/" + now.strftime('%Y')  )
        canvas.drawString(doc.leftMargin, headerBottom - 20, "   Empresa  : " + fornecedor.name)
        canvas.drawString(doc.leftMargin, headerBottom - 30, "   Associado:"  + socio.pessoa.name)
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin ,      headerBottom - 40, lineLength, headerBottom - 40)

        # FOOTER #
        footerBotton = doc.bottomMargin - 20
        canvas.setFont('Times-Roman',8)
        canvas.drawString(doc.leftMargin, footerBotton , "MILENIO CONTABILIDADE LTDA" )
        canvas.drawString(doc.leftMargin, footerBotton - 10, "www.mileniocontabilidade.com.br" )
        canvas.drawString(doc.leftMargin, footerBotton - 20 , "Pagina:%d" % doc.page + "  / Emitido em: %s" % now.strftime("%m/%d/%Y %H:%M:%S")) 

        # on left
        canvas.drawRightString(lineLength, footerBotton, "SIRCO - SISTEMA DE ROTINAS CONTÁBEIS " )
        canvas.drawRightString(lineLength, footerBotton - 10 , "Descomplique a sua rotina" )
        canvas.drawRightString(lineLength, footerBotton - 20 , "CONTATO: (031) 9.8852-4188" )
        canvas.restoreState()
    
    #-----------------------------------------------------------------
    # #display the title of the blog and the current page
    def add_Header_footer(canvas, doc):
        canvas.saveState()
        title = 'doc.getTitle()'
        fontsize = 10
        fontname = 'Times-Roman'
        headerBottom = doc.bottomMargin + doc.height + doc.topMargin /2
        bottomLine = headerBottom - fontsize/4
        topLine = headerBottom + fontsize
        lineLength = doc.width + doc.leftMargin
        canvas.setFont(fontname,fontsize)
        

        '''
        if doc.page % 2:
            #odd page: put the page number on the right and align right
                title += "-" + str(doc.page)
                canvas.drawRightString(lineLength, headerBottom, title)
        else:
            #even page: put the page number on the left and align left
            title = str(doc.page) + "-" + title
            canvas.drawString(doc.leftMargin, headerBottom, title)
        '''


        canvas.drawString(doc.leftMargin, headerBottom - 10, "   Demonstrativo de Resultados: "  + str(periodo_fiscal.month) + "/" + now.strftime('%Y')  )
        canvas.drawString(doc.leftMargin, headerBottom - 20, "   Empresa  : " + fornecedor.name)
        canvas.drawString(doc.leftMargin, headerBottom - 30, "   Associado:"  + socio.pessoa.name)
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin ,      headerBottom - 40, lineLength, headerBottom - 40)

        # FOOTER #
        footerBotton = doc.bottomMargin - 20
        canvas.setFont('Times-Roman',8)

        # on right
        canvas.drawString(doc.leftMargin, footerBotton , "MILENIO CONTABILIDADE LTDA" )
        canvas.drawString(doc.leftMargin, footerBotton - 10, "www.mileniocontabilidade.com.br" )
        canvas.drawString(doc.leftMargin, footerBotton - 20 , "Pagina:%d" % doc.page + "  / Emitido em: %s" % now.strftime("%m/%d/%Y %H:%M:%S")) 
        # on left
        canvas.drawRightString(lineLength, footerBotton, "SIRCO - SISTEMA DE ROTINAS CONTÁBEIS " )
        canvas.drawRightString(lineLength, footerBotton - 10 , "Descomplique a sua rotina" )
        canvas.drawRightString(lineLength, footerBotton - 20, "CONTATO: (031) 9.8852-4188" )
        canvas.restoreState()

    # #display the title of the blog and the current page
    def header_firstpage(canvas, doc):
        canvas.saveState()
        title = 'doc.getTitle()'
        fontsize = 12
        fontname = 'Times-Roman'
        headerBottom = doc.bottomMargin+doc.height+doc.topMargin/2
        bottomLine = headerBottom - fontsize/4
        topLine = headerBottom + fontsize
        lineLength = doc.width+doc.leftMargin
        canvas.setFont(fontname,fontsize)
        
        if doc.page % 2:
            #odd page: put the page number on the right and align right
                title += "-" + str(doc.page)
                canvas.drawRightString(lineLength, headerBottom, title)
        else:
            #even page: put the page number on the left and align left
            title = str(doc.page) + "-" + title
            canvas.drawString(doc.leftMargin, headerBottom, title)

        canvas.restoreState()

    #----------------------------------------------------------------------------#
    # FRAMES
    #----------------------------------------------------------------------------#

    #Two Columns
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-6, doc.height,                 id='col1')
    frame2 = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin, doc.width/2-6,doc.height,    id='col2')

    frame_portrait = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,                     id='normal')
    frame_landscape = Frame(doc.leftMargin, doc.bottomMargin, height=doc.width, width= doc.height,      id='frame_landscape')

    #----------------------------------------------------------------------------#
    # PAGES TEMPLATES
    #----------------------------------------------------------------------------#

    doc.addPageTemplates([  PageTemplate(id='template_myfooter'         ,frames=frame_portrait,     onPage=foot1),
                            PageTemplate(id='template_firstpage'        ,frames=[frame1,frame2],    onPage=header_firstpage),
                            PageTemplate(id='template_portrait'         ,frames=frame_portrait,     pagesize=portrait(A4),  onPage=add_Header_footer),
                            PageTemplate(id='template_landscape'        ,frames=frame_landscape,    pagesize=landscape(A4), onPage=header_landscape),
                        ])
    
    elements = []

    #----------------------------------------------------------------------------#
    # FIRSTPAGE CABEÇALHO
    #----------------------------------------------------------------------------#

    elements.append(Paragraph("DEMONSTRATIVO DE RESULTADOS        ", styleBH))
    elements.append(Paragraph(fornecedor.name, styleBH))
    elements.append(Paragraph("----------------------------------------------------------------------------------", styleBH))

    elements.append(Paragraph("Associado:"  + socio.pessoa.name, styleN))
    elements.append(Paragraph("Mês:"  + str(periodo_fiscal.month) + "/" + str(periodo_fiscal.year) , styleN))


    #---------------------------------------------------------------------------------------------#
    # DEMONSTRATIVO                                                                               #  
    #---------------------------------------------------------------------------------------------#
    op_financeira= Financeiro.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio)\
                                                            .values('descricao__descricao')\
                                                            .annotate(valor=Sum('valor'))
    
    parstyle = ParagraphStyle(name='Title', fontName='Helvetica', fontSize=11, alignment=0)
    data = []
    try:

            ds_demonstrativo = Balanco.objects.get(data__year = periodo_fiscal.year, data__month = periodo_fiscal.month, socio=socio)

            number = babel.numbers.format_currency(ds_demonstrativo.recebido_total, 'BRL', locale='pt_BR')
            data.append(["1- RECEITA BRUTA RECEBIDA (=)",number])

            number = babel.numbers.format_currency(ds_demonstrativo.recebido_consultas, 'BRL', locale='pt_BR')
            data.append(["   Receita de consultas",number])

            number = babel.numbers.format_currency(ds_demonstrativo.recebido_plantao, 'BRL', locale='pt_BR')
            data.append(["   Receita de plantao",number])

            number = babel.numbers.format_currency(ds_demonstrativo.recebido_outros, 'BRL', locale='pt_BR')
            data.append(["   Receita de procedimentos e outros", number])

            number = babel.numbers.format_currency(ds_demonstrativo.imposto_total, 'BRL', locale='pt_BR')
            data.append(["2- IMPOSTOS (VALOR A PROVISIONAR)  (-)",number])

            number = babel.numbers.format_currency(ds_demonstrativo.imposto_PIS_devido, 'BRL', locale='pt_BR')
            data.append(["   PIS",number])
 
            number = babel.numbers.format_currency(ds_demonstrativo.imposto_COFINS_devido, 'BRL', locale='pt_BR')
            data.append(["   COFINS",number])

            number = babel.numbers.format_currency(ds_demonstrativo.imposto_irpj_imposto_devido, 'BRL', locale='pt_BR')
            data.append(["   IRPJ",number])

            number = babel.numbers.format_currency(ds_demonstrativo.imposto_irpj_imposto_adicional, 'BRL', locale='pt_BR')
            data.append(["   Adicional de IR",number])

            number = babel.numbers.format_currency(ds_demonstrativo.imposto_csll_imposto_devido, 'BRL', locale='pt_BR')
            data.append(["   CSLL",number])

            number = babel.numbers.format_currency(ds_demonstrativo.imposto_iss_imposto_devido, 'BRL', locale='pt_BR')
            data.append(["   ISSQN",number])

            number = babel.numbers.format_currency(ds_demonstrativo.receita_liquida_total, 'BRL', locale='pt_BR')
            data.append(["3- RECEITA LIQUIDA (=)",number])

            number = babel.numbers.format_currency(ds_demonstrativo.despesa_total, 'BRL', locale='pt_BR')
            data.append(["4- DESPESAS (-)",number])

            number = babel.numbers.format_currency(ds_demonstrativo.despesa_sem_rateio, 'BRL', locale='pt_BR')
            data.append(["   Despesa de sócio",number])

            number = babel.numbers.format_currency(ds_demonstrativo.despesa_folha_rateio, 'BRL', locale='pt_BR')
            data.append(["   Despesa de folha de pagamento",number])

            number = babel.numbers.format_currency(ds_demonstrativo.despesa_geral_rateio, 'BRL', locale='pt_BR')
            data.append(["   Despesa geral",number])

            number = babel.numbers.format_currency(ds_demonstrativo.saldo_apurado, 'BRL', locale='pt_BR')
            data.append(["5- SALDO APURADO (=)",number])

            number = babel.numbers.format_currency(ds_demonstrativo.saldo_movimentacao_financeira, 'BRL', locale='pt_BR')
            data.append(["6- SALDO DAS MOVIMENTAÇÕES FINANCEIRAS (+)",number])
                
            #teste = Desc_movimentacao_financeiro.objects.all()    
            operacao_list = [entry for entry in op_financeira] # gera a lista {'descricao__descricao': 'CREDITO SALDO MES ANTERIOR', 'valor': Decimal('5039.93')}
            for teste in operacao_list:
                number = babel.numbers.format_currency(teste["valor"], 'BRL', locale='pt_BR')
                text = "    " + teste["descricao__descricao"]
                data.append([text, number]) 

            #--------------------------------

            number = babel.numbers.format_currency(ds_demonstrativo.saldo_a_transferir, 'BRL', locale='pt_BR')
            data.append(["7- SALDO A TRANSFERIR (=)",number])

            #number = babel.numbers.format_currency(ds_demonstrativo.imposto_total, 'BRL', locale='pt_BR')
            #data.append(["8- SALDO PROVISIONADO MES SEGUINTE (=)",number])


    except:
        request.session['msg_status'] = "FALHA GERAÇÃO RELATORIO"
        pass

    tbl_demostrativo= Table(data, hAlign='LEFT', repeatRows=1, spaceBefore= 20, spaceAfter= 20)
    tbl_demostrativo.setStyle(TableStyle([
        #('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.red, None, (2, 2, 1)),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.blue),
        ]))
    #---------------------------------------------------------------------------------------------#

    elements.append(NextPageTemplate('template_portrait'))
    elements.append(Paragraph('RESULTADO FINANCEIRO', styleN))
    elements.append(tbl_demostrativo)

    #---------------------------------------------------------------------------------------------#
    # FINANCEIRO                                                                 #  
    #---------------------------------------------------------------------------------------------#

    # headers
    h1        = Paragraph('''<b> id   </b>'''               , styleBH)
    h2        = Paragraph('''<b> Data </b>'''               , styleBH)
    h3        = Paragraph('''<b> Tipo </b>'''   , styleBH)
    h4        = Paragraph('''<b> Descricao	 </b>'''        , styleBH)
    h5        = Paragraph('''<b> Valor 	 </b>'''    , styleBH)
 

    data =[]
    data.append([h1,h2,h3,h4,h5])

    ds_financeiro= Financeiro.objects.filter(data__year=periodo_fiscal.year, data__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio)\
                                                .order_by('data')
    idx=0
    try:

        for movimentacao in ds_financeiro:
            row = []
            idx +=1
            row.append(idx)

            mydate = babel.dates.format_date(movimentacao.data, 'dd/MM/YYYY')
            row.append(mydate)  

            row.append(movimentacao.tipo)
            row.append(movimentacao.descricao.descricao)            
            number = babel.numbers.format_currency(movimentacao.valor, 'BRL', locale='pt_BR')
            row.append(number)    
            data.append(row)

    except:
        request.session['msg_status'] = "FALHA GERAÇÃO RELATORIO"
        pass


    tbl_financeiro= Table(data,   hAlign='LEFT', repeatRows=1, spaceAfter= 20, spaceBefore= 20)
    tbl_financeiro.setStyle(TableStyle([
        #('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.red, None, (2, 2, 1)),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.blue),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))

    #---------------------------------------------------------------------------------------------#
    elements.append(NextPageTemplate('template_portrait'))
    elements.append(Paragraph('RELAÇÃO DE MOVIMENTAÇÕES FINANCEIRAS', styleN))
    elements.append(tbl_financeiro)

    #---------------------------------------------------------------------------------------------#
    # DESPESAS DE SOCIO                                                                      #  
    #---------------------------------------------------------------------------------------------#

    # headers
    h1        = Paragraph('''<b> id   </b>'''               , styleBH)
    h2        = Paragraph('''<b> Data </b>'''               , styleBH)
    h3        = Paragraph('''<b> Grupo da despesa </b>'''         , styleBH)
    #h4        = Paragraph('''<b> Codigo da despesa	 </b>'''    , styleBH)
    h5        = Paragraph('''<b> Descricao	 </b>'''        , styleBH)
    h6        = Paragraph('''<b> Valor </b>'''          , styleBH)

    data =[]
    #data.append([h1,h2,h3,h4,h5,h6])
    data.append([h1,h2,h3,h5,h6])

    ds_despesa_pessoa = Despesa.objects.filter(data__year= periodo_fiscal.year, data__month=periodo_fiscal.month, empresa = fornecedor, socio=socio, \
                                              tipo_rateio = TIPO_DESPESA_SEM_RATEIO)
    idx=0
    try:

        for despesa in ds_despesa_pessoa:
            row = []
            idx +=1
            row.append(idx)
            #row.append(despesa.data)
            mydate = babel.dates.format_date(despesa.data, 'dd/MM/YYYY')
            row.append(mydate)  

            row.append(despesa.item.grupo.codigo)
            #row.append(despesa.item.codigo)            
            row.append(despesa.item.descricao)

            number = babel.numbers.format_currency(despesa.valor, 'BRL', locale='pt_BR')
            row.append(number)    
            data.append(row)

    except:
        request.session['msg_status'] = "FALHA GERAÇÃO RELATORIO"
        pass
    
    tbl_despesa_socio= Table(data,   hAlign='LEFT', repeatRows=1, spaceAfter= 20, spaceBefore= 20)
    tbl_despesa_socio.setStyle(TableStyle([
        #('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.red, None, (2, 2, 1)),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.blue),
        ]))

    #---------------------------------------------------------------------------------------------#
    elements.append(NextPageTemplate('template_portrait'))
    elements.append(Paragraph('RELAÇÃO DE DESPESAS DE SOCIO', styleN))
    elements.append(tbl_despesa_socio)

    #---------------------------------------------------------------------------------------------#
    # DESPESAS GERAL E FOLHA                                                                     #  
    #---------------------------------------------------------------------------------------------#

    # headers
    h1        = Paragraph('''<b> id   </b>'''               , styleBH)
    h2        = Paragraph('''<b> Data </b>'''               , styleBH)
    h3        = Paragraph('''<b> Grupo da despesa </b>'''   , styleBH)
    h4        = Paragraph('''<b> Descricao	 </b>'''        , styleBH)
    h5        = Paragraph('''<b> Valor total	 </b>'''    , styleBH)
    h6        = Paragraph('''<b> Rateio [%]      </b>'''    , styleBH)
    h7        = Paragraph('''<b> Valor sócio </b>'''        , styleBH)

    data =[]
    data.append([h1,h2,h3,h4,h5,h6])

    ds_desp_rateio= Despesa_socio_rateio.objects.filter(despesa__data__year=periodo_fiscal.year, despesa__data__month=periodo_fiscal.month, socio = socio)\
                                                .order_by('despesa__item__codigo')
    idx=0
    try:

        for despesa in ds_desp_rateio:
            row = []
            idx +=1
            row.append(idx)
            #row.append(despesa.despesa.data)
            mydate = babel.dates.format_date(despesa.despesa.data, 'dd/MM/YYYY')
            row.append(mydate)  

            row.append(despesa.despesa.item.grupo.codigo)
            row.append(despesa.despesa.item.descricao)

            number = babel.numbers.format_currency(despesa.despesa.valor, 'BRL', locale='pt_BR')
            row.append(number)    

            number = format_decimal(despesa.percentual, locale='pt_BR')
            row.append(number)      

            number = babel.numbers.format_currency(despesa.vl_rateio, 'BRL', locale='pt_BR')
            row.append(number)    

            data.append(row)

    except:
        request.session['msg_status'] = "FALHA GERAÇÃO RELATORIO"
        pass


    tbl_despesa_geral= Table(data,   hAlign='LEFT', repeatRows=1, spaceAfter= 20, spaceBefore= 20)
    tbl_despesa_geral.setStyle(TableStyle([
        #('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.red, None, (2, 2, 1)),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.blue),
        ]))
    
    #---------------------------------------------------------------------------------------------#
    elements.append(NextPageTemplate('template_portrait'))
    elements.append(Paragraph('RELAÇÃO DE DESPESAS DE FOLHA E GERAL', styleN))
    elements.append(tbl_despesa_geral)



    #---------------------------------------------------------------------------------------------#
    # NOTAS FISCAIS                                                                       #  
    #---------------------------------------------------------------------------------------------#
    # headers
    h1        = Paragraph('''<b> id   </b>'''           , styleBH)
    h2        = Paragraph('''<b> Tipo </b>'''           , styleBH)
    h3        = Paragraph('''<b> Número </b>'''         , styleBH)
    h4        = Paragraph('''<b> Tomador </b>'''        , styleBH)
    h5        = Paragraph('''<b> Dt emissão </b>'''     , styleBH)
    h6        = Paragraph('''<b> Dt recebimento </b>''' , styleBH)
    h7        = Paragraph('''<b> Valor bruto </b>'''    , styleBH)
    h8        = Paragraph('''<b> Valor líquido </b>'''  , styleBH)
    h9        = Paragraph('''<b> ISS </b>'''            , styleBH)
    h10       = Paragraph('''<b> PIS </b>'''            , styleBH)
    h11       = Paragraph('''<b> IRPJ </b>'''           , styleBH)
    h12       = Paragraph('''<b> CSLL </b>'''           , styleBH)


    data = []
    data.append([h1,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12])

    ds_nfiscal_consulta = NotaFiscal.objects.filter(dtEmissao__year=periodo_fiscal.year, dtEmissao__month=periodo_fiscal.month, fornecedor = fornecedor, socio = socio)

    idx=0
    try:

        for nfiscal in ds_nfiscal_consulta:
            row = []
            idx +=1
            row.append(idx)
            #row.append(nfiscal.tipo_aliquota)
            row.append(nfiscal.numero)
            row.append(nfiscal.tomador[0:27])      # limite qte de caracteres      
            #row.append(nfiscal.dtEmissao)
            mydate = babel.dates.format_date(nfiscal.dtEmissao, 'dd/MM/YYYY')
            row.append(mydate)  

            #row.append(nfiscal.dtRecebimento)   
            mydate = babel.dates.format_date(nfiscal.dtRecebimento, 'dd/MM/YYYY')
            row.append(mydate)  

            number = babel.numbers.format_currency(nfiscal.val_bruto, 'BRL', locale='pt_BR')
            row.append(number)

            number = babel.numbers.format_currency(nfiscal.val_liquido, 'BRL', locale='pt_BR')
            row.append(number)

            number = babel.numbers.format_currency(nfiscal.val_ISS, 'BRL', locale='pt_BR')
            row.append(number)

            number = babel.numbers.format_currency(nfiscal.val_PIS, 'BRL', locale='pt_BR')
            row.append(number)

            number = babel.numbers.format_currency(nfiscal.val_COFINS, 'BRL', locale='pt_BR')
            row.append(number)  

            number = babel.numbers.format_currency(nfiscal.val_CSLL, 'BRL', locale='pt_BR')
            row.append(number)


            data.append(row)

    except:
        request.session['msg_status'] = "FALHA GERAÇÃO RELATORIO"
        pass

    tlb_nfconsulta= Table(data,   hAlign='LEFT', repeatRows=1, spaceAfter= 20, spaceBefore= 20)
    tlb_nfconsulta.setStyle(TableStyle([
        #('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.red, None, (2, 2, 1)),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.blue),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))

    elements.append(NextPageTemplate('template_landscape'))
    elements.append(PageBreak())
    elements.append(Paragraph('RELAÇÃO DE NOTAS FISCAIS', styleN))
    elements.append(tlb_nfconsulta)


    #---------------------------------------------------------------------------------------------#
    # GERACAO                                                                                     #  
    #---------------------------------------------------------------------------------------------#
    doc.build(elements)
    response.write(buffer.getvalue())
    buffer.close()
    return response