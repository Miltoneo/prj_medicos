import django_tables2 as tables
from .models.financeiro import AplicacaoFinanceira


from django.utils.html import format_html


class AplicacaoFinanceiraTable(tables.Table):
    def render_saldo(self, value):
        if value is None:
            return "-"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    editar = tables.Column(empty_values=(), orderable=False, verbose_name='Editar')

    def render_editar(self, record):
        url = f"/medicos/aplicacoes-financeiras/{record.pk}/editar/"
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i> Editar</a>', url
        )

    class Meta:
        model = AplicacaoFinanceira
        template_name = "django_tables2/bootstrap4.html"
        fields = ("data_referencia", "saldo", "descricao", "created_by")
