import django_tables2 as tables
from .models.base import Socio

class SocioListaTable(tables.Table):
    nome = tables.Column(accessor='pessoa.name', verbose_name="Nome")
    cpf = tables.Column(accessor='pessoa.cpf', verbose_name="CPF")
    data_entrada = tables.DateColumn(verbose_name="Data de Entrada")
    data_saida = tables.DateColumn(verbose_name="Data de Saída")
    ativo = tables.BooleanColumn(verbose_name="Ativo")
    acoes = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'medicos:socio_edit' empresa_id=record.empresa.id socio_id=record.id %}" class="btn btn-sm btn-primary me-1">
            <i class="fas fa-edit"></i> Editar
        </a>
        <a href="{% url 'medicos:socio_unlink' empresa_id=record.empresa.id socio_id=record.id %}" class="btn btn-sm btn-danger"
           onclick="return confirm('Deseja realmente excluir este sócio?');">
            <i class="fas fa-trash"></i> Excluir
        </a>
        ''',
        verbose_name="Ações",
        orderable=False
    )

    class Meta:
        model = Socio
        template_name = "django_tables2/bootstrap5.html"
        fields = ("nome", "cpf", "data_entrada", "data_saida", "ativo", "acoes")
        order_by = ("nome",)  # Ordenação padrão por nome


class SocioListaDashboardTable(tables.Table):
    """
    Tabela específica para o dashboard da empresa - apenas informativa, sem ações
    """
    nome = tables.Column(accessor='pessoa.name', verbose_name="Nome")
    cpf = tables.Column(accessor='pessoa.cpf', verbose_name="CPF")
    data_entrada = tables.DateColumn(verbose_name="Data de Entrada")
    data_saida = tables.DateColumn(verbose_name="Data de Saída")
    ativo = tables.BooleanColumn(verbose_name="Ativo")

    class Meta:
        model = Socio
        template_name = "django_tables2/bootstrap5.html"
        fields = ("nome", "cpf", "data_entrada", "data_saida", "ativo")
        order_by = ("nome",)  # Ordenação padrão por nome
