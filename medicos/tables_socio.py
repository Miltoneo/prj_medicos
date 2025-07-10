import django_tables2 as tables
from .models.base import Socio

class SocioTable(tables.Table):
    nome = tables.Column(accessor='pessoa.name', verbose_name="Nome")
    cpf = tables.Column(accessor='pessoa.cpf', verbose_name="CPF")
    data_entrada = tables.DateColumn(verbose_name="Data de Entrada")
    data_saida = tables.DateColumn(verbose_name="Data de Saída")
    ativo = tables.BooleanColumn(verbose_name="Ativo")

    class Meta:
        model = Socio
        template_name = "django_tables2/bootstrap5.html"
        fields = ("nome", "cpf", "data_entrada", "data_saida", "ativo")
