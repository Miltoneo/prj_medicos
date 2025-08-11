import django_tables2 as tables
from .models.financeiro import Financeiro
from django.utils.safestring import mark_safe

class FinanceiroTable(tables.Table):
    acoes = tables.TemplateColumn(
        template_code='''
            <a href="{% url 'medicos:financeiro_edit' empresa_id=empresa.id pk=record.pk %}" class="btn btn-sm btn-primary me-1">Editar</a>
            <a href="{% url 'medicos:financeiro_delete' empresa_id=empresa.id pk=record.pk %}" class="btn btn-sm btn-danger" onclick="return confirm('Confirma exclusão?');">Excluir</a>
        ''',
        verbose_name='Ações',
        orderable=False
    )
    socio = tables.Column(verbose_name='Médico/Sócio', accessor='socio.pessoa.name')
    nota_fiscal = tables.Column(
        accessor='nota_fiscal.numero',
        verbose_name='Nota Fiscal',
        default='-',
        orderable=True
    )
    descricao_movimentacao_financeira = tables.Column(verbose_name='Descrição')
    data_movimentacao = tables.DateColumn(verbose_name='Data')
    from django.utils.safestring import mark_safe
    def render_valor(self, value):
        if value >= 0:
            return mark_safe(f'<span style="color:green;">R$ {value:,.2f}</span>')
        else:
            return mark_safe(f'<span style="color:red;">R$ {value:,.2f}</span>')

    valor = tables.Column(verbose_name='Valor (R$)', attrs={"td": {"class": "text-end"}}, orderable=True)
    created_at = tables.DateTimeColumn(verbose_name='Criado em')

    class Meta:
        model = Financeiro
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('socio', 'nota_fiscal', 'descricao_movimentacao_financeira', 'data_movimentacao', 'valor', 'created_at', 'acoes')
        order_by = ('-data_movimentacao', '-created_at')
