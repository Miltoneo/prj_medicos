import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal

class NotaFiscalRecebimentoTable(tables.Table):
    numero = tables.Column(verbose_name='Número')
    dtEmissao = tables.DateColumn(verbose_name='Data Emissão', format='d/m/Y')
    tomador = tables.Column(verbose_name='Tomador do Serviço')
    val_bruto = tables.Column(verbose_name='Valor Bruto (R$)', attrs={"td": {"class": "text-end"}})
    val_liquido = tables.Column(verbose_name='Valor Líquido (R$)', attrs={"td": {"class": "text-end"}})
    meio_pagamento = tables.Column(verbose_name='Meio de Pagamento', default='-')
    dtRecebimento = tables.DateColumn(verbose_name='Data Recebimento', format='d/m/Y')
    status_recebimento = tables.Column(verbose_name='Status')
    actions = tables.TemplateColumn(
        template_code="""
<a href='{% url "medicos:editar_recebimento_nota_fiscal" record.pk %}?{{ request.GET.urlencode }}' class='btn btn-sm btn-secondary'>Editar Recebimento</a>
""",
        verbose_name='Ações', orderable=False
    )

    def render_val_bruto(self, value):
        """Formata o valor bruto com símbolo da moeda"""
        if value is None:
            return '-'
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    def render_val_liquido(self, value):
        """Formata o valor líquido com símbolo da moeda"""
        if value is None:
            return '-'
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    class Meta:
        model = NotaFiscal
        fields = ('numero', 'dtEmissao', 'tomador', 'val_bruto', 'val_liquido', 'meio_pagamento', 'dtRecebimento', 'status_recebimento')
        attrs = {'class': 'table table-striped'}
