import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal
from django.utils.safestring import mark_safe

class NotaFiscalRecebimentoTable(tables.Table):
    numero = tables.Column(verbose_name='Número')
    dtEmissao = tables.DateColumn(verbose_name='Data Emissão', format='d/m/Y')
    tomador = tables.Column(verbose_name='Tomador do Serviço')
    val_bruto = tables.Column(verbose_name='Valor Bruto (R$)', attrs={"td": {"class": "text-end"}})
    val_liquido = tables.Column(verbose_name='Valor Líquido (R$)', attrs={"td": {"class": "text-end"}})
    meio_pagamento = tables.Column(verbose_name='Meio de Pagamento', default='-')
    dtRecebimento = tables.DateColumn(verbose_name='Data Recebimento', format='d/m/Y')
    status_recebimento = tables.Column(verbose_name='Status')
    
    def render_status_rateio(self, record):
        """Renderiza o status do rateio da nota fiscal"""
        if not record.tem_rateio:
            return mark_safe('<span class="badge bg-secondary">Sem Rateio</span>')
        elif record.rateio_completo:
            return mark_safe('<span class="badge bg-success">Rateio Completo</span>')
        else:
            return mark_safe(f'<span class="badge bg-warning">Rateio {record.percentual_total_rateado:.1f}%</span>')
    
    status_rateio = tables.Column(verbose_name='Rateio', orderable=False, empty_values=())
    
    # Usando TemplateColumn para renderizar as ações com CSRF token
    actions = tables.TemplateColumn(
        template_name='financeiro/col_acoes_recebimento_notafiscal.html',
        verbose_name='Ações',
        orderable=False,
        attrs={"td": {"class": "text-center"}}
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
        fields = ('numero', 'dtEmissao', 'dtRecebimento', 'tomador', 'val_bruto', 'val_liquido', 'status_rateio', 'meio_pagamento', 'status_recebimento', 'actions')
        attrs = {'class': 'table table-striped'}
