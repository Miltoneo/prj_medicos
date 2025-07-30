import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal

class NotaFiscalRecebimentoTable(tables.Table):
    numero = tables.Column(verbose_name='Número')
    dtEmissao = tables.DateColumn(verbose_name='Data Emissão', format='d/m/Y')
    meio_pagamento = tables.Column(verbose_name='Meio de Pagamento', default='-')
    dtRecebimento = tables.DateColumn(verbose_name='Data Recebimento', format='d/m/Y')
    status_recebimento = tables.Column(verbose_name='Status')
    actions = tables.TemplateColumn(
        template_code="""
<a href='{% url "medicos:editar_recebimento_nota_fiscal" record.pk %}' class='btn btn-sm btn-secondary'>Editar Recebimento</a>
""",
        verbose_name='Ações', orderable=False
    )

    class Meta:
        model = NotaFiscal
        fields = ('numero', 'dtEmissao', 'meio_pagamento', 'dtRecebimento', 'status_recebimento')
        attrs = {'class': 'table table-striped'}
