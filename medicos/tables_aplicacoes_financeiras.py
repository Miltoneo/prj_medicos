import django_tables2 as tables
from .models.financeiro import AplicacaoFinanceira

class AplicacaoFinanceiraTable(tables.Table):
    class Meta:
        model = AplicacaoFinanceira
        template_name = "django_tables2/bootstrap4.html"
        fields = ("id", "data_referencia", "valor", "descricao", "created_by")
