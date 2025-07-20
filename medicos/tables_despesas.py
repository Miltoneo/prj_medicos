import django_tables2 as tables
from medicos.models.despesas import DespesaRateada

class DespesaEmpresaTable(tables.Table):
    descricao = tables.Column(accessor='item_despesa.descricao', verbose_name='Descrição')
    grupo = tables.Column(accessor='item_despesa.grupo_despesa.descricao', verbose_name='Grupo')
    valor = tables.Column(verbose_name='Valor Total', attrs={"td": {"class": "text-end"}})
    def render_valor(self, value):
        return f'R$ {value:,.2f}'

    acoes = tables.TemplateColumn(
        template_name='despesas/col_acoes_empresa.html',
        orderable=False,
        verbose_name='Ações',
        attrs={"td": {"class": "text-center"}}
    )

    class Meta:
        model = DespesaRateada
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('descricao', 'grupo', 'valor')
