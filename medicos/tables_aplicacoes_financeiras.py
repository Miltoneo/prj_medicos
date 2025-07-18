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
        from django.urls import reverse
        empresa_id = record.empresa_id if hasattr(record, 'empresa_id') else (record.empresa.id if hasattr(record.empresa, 'id') else None)
        url = reverse('medicos:aplicacoes_financeiras_edit', kwargs={'empresa_id': empresa_id, 'pk': record.pk})
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i> Editar</a>', url
        )

    class Meta:
        model = AplicacaoFinanceira
        template_name = "django_tables2/bootstrap4.html"
        fields = ("data_referencia", "saldo", "ir_cobrado", "descricao", "created_by")
        sequence = ("data_referencia", "saldo", "ir_cobrado", "descricao", "created_by", "editar")
