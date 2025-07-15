import django_tables2 as tables
from .models.financeiro import Financeiro

class FinanceiroTable(tables.Table):
    socio = tables.Column(verbose_name='Médico/Sócio')
    descricao_movimentacao_financeira = tables.Column(verbose_name='Descrição')
    data_movimentacao = tables.DateColumn(verbose_name='Data')
    tipo = tables.Column(verbose_name='Tipo')
    valor = tables.Column(verbose_name='Valor (R$)', attrs={"td": {"class": "text-end"}})
    created_at = tables.DateTimeColumn(verbose_name='Criado em')

    class Meta:
        model = Financeiro
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('socio', 'descricao_movimentacao_financeira', 'data_movimentacao', 'tipo', 'valor', 'created_at')
        order_by = ('-data_movimentacao', '-created_at')
