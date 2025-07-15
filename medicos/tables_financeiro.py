import django_tables2 as tables
from .models.financeiro import Financeiro

class FinanceiroTable(tables.Table):
    acoes = tables.TemplateColumn(
        template_code='''
            <a href="{% url 'financeiro:financeiro_edit' empresa_id=request.session.empresa_id pk=record.pk %}" class="btn btn-sm btn-primary me-1">Editar</a>
            <a href="{% url 'financeiro:financeiro_delete' empresa_id=request.session.empresa_id pk=record.pk %}" class="btn btn-sm btn-danger" onclick="return confirm('Confirma exclusão?');">Excluir</a>
        ''',
        verbose_name='Ações',
        orderable=False
    )
    socio = tables.Column(verbose_name='Médico/Sócio')
    descricao_movimentacao_financeira = tables.Column(verbose_name='Descrição')
    data_movimentacao = tables.DateColumn(verbose_name='Data')
    tipo = tables.Column(verbose_name='Tipo')
    valor = tables.Column(verbose_name='Valor (R$)', attrs={"td": {"class": "text-end"}})
    created_at = tables.DateTimeColumn(verbose_name='Criado em')

    class Meta:
        model = Financeiro
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('socio', 'descricao_movimentacao_financeira', 'data_movimentacao', 'tipo', 'valor', 'created_at', 'acoes')
        order_by = ('-data_movimentacao', '-created_at')
