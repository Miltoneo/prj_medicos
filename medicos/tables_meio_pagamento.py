import django_tables2 as tables
from medicos.models.financeiro import MeioPagamento

class MeioPagamentoTable(tables.Table):
    codigo = tables.Column(verbose_name="Código")
    nome = tables.Column(verbose_name="Nome")
    descricao = tables.Column(verbose_name="Descrição")

    class Meta:
        model = MeioPagamento
        template_name = "django_tables2/bootstrap5.html"
        fields = ("codigo", "nome", "descricao")
