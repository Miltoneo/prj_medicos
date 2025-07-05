from django_tables2 import tables, Table, Column, LinkColumn, TemplateColumn
from django_tables2.utils import A
from django.db import models
from django.views.generic import ListView

from .models import *
from .data import *
from .forms import *

#-----------------------------------
class NFiscal_Table(tables.Table):

    editar = LinkColumn('medicos:nf_editar', text='Editar',args=[A('pk')],orderable=False, empty_values=())
    excluir = TemplateColumn('''<a href="{% url 'medicos:nf_excluir' notaFiscal_pk=record.id %}"  onclick="return confirm('Confirma exclusão?')">Excluir</a>''') 
               
    class Meta:
        model = NotaFiscal
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ("editar", "excluir",'id','tipo_aliquota' )
        exclude = ('fornecedor', 'id',)  
        order = ('socio__pessoa__name',)

#-----------------------------------
class NFiscal_recebidas_Table(tables.Table):
    editar = LinkColumn('medicos:financeiro_NF_editar', text='Editar',args=[A('pk')],orderable=False, empty_values=())
            
    class Meta:
        model = NotaFiscal
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ("editar", )
        fields = ( 'numero', 'dtRecebimento', 'dtEmissao','socio','val_bruto','val_liquido', 'tomador', 'numero',  ) # fields to display

#-----------------------------------
class Financeiro_Table(tables.Table):

    editar = LinkColumn('medicos:financeiro_transferencia_editar', text='Editar',args=[A('pk')],orderable=False, empty_values=())
    excluir = TemplateColumn('''<a href="{% url 'medicos:financeiro_transacao_excluir' financeiro_id=record.id %}"  onclick="return confirm('Confirma exclusão?')">Excluir</a>''') 
               
    class Meta:
        model = Financeiro
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        fields = ("editar", "excluir",'data','socio','tipo','descricao','valor' )

#-----------------------------------
class Despesas_Table(tables.Table):

    editar = LinkColumn('medicos:despesa_coletiva_editar', text='Editar',args=[A('pk')],orderable=False, empty_values=())
    excluir = TemplateColumn('''<a href="{% url 'medicos:despesa_excluir' id=record.id %}"  onclick="return confirm('Confirma exclusão?')">Excluir</a>''') 

    class Meta:
        model = Despesa
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ("editar", "excluir", )
        exclude = ('id','socio','tipo_rateio', 'empresa', 'descricao' )  

#-----------------------------------
class Aplic_fincanceiras_table(tables.Table):

    editar = LinkColumn('medicos:aplicacoes_mes', text='Editar',args=[A('pk')],orderable=False, empty_values=())

    class Meta:
        model = AplicacaoFinanceira
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ("editar", 'data', 'rendimentos', 'irrf')
        exclude = ('id', 'fornecedor', 'descricao', 'conta')  

#-----------------------------------
class Desc_mov_financeira_Table(tables.Table):

    editar = LinkColumn('medicos:desc_mov_financeira_editar', text='Editar',args=[A('pk')],orderable=False, empty_values=())
    excluir = TemplateColumn('''<a href="{% url 'medicos:desc_mov_transferencia_excluir' desc_id=record.id %}"  onclick="return confirm('Confirma exclusão?')">Excluir</a>''') 
               
    class Meta:
        model = DescricaoMovimentacao
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        fields = ("editar", "excluir",'descricao', )

#-----------------------------------
class Empresa_Table(tables.Table):

    name = LinkColumn('medicos:start',args=[A('pk')],orderable=True, empty_values=())
              
    class Meta:
        model = Empresa
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ('CNPJ','name','tipo_regime')
        exclude = ('id',)  

#-----------------------------------
class Despesas_Socio_Table(tables.Table):

    editar = LinkColumn('medicos:despesa_socio_editar', text='Editar',args=[A('pk')],orderable=False, empty_values=())
    excluir = TemplateColumn('''<a href="{% url 'medicos:despesa_socio_excluir' despesa_id=record.id socio_id=socio.id%}"  onclick="return confirm('Confirma exclusão?')">Excluir</a>''') 

    class Meta:
        model = Despesa
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ("editar", "excluir",'id' )
        exclude = ('socio','tipo_rateio', 'empresa', 'descricao' )  

#-----------------------------------
class Socio_Table(tables.Table):

    pessoa = LinkColumn('medicos:relatorio_socio_mes', args=[A('pk')],orderable=False, empty_values=())

    class Meta:
        model = Socio
        template_name = "django_tables2/bootstrap.html"
        orderable = True
        sequence = ('pessoa', )
        exclude = ('id','empresa',)
