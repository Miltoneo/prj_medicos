import django_tables2 as tables
from .models.conta_corrente import MovimentacaoContaCorrente
from django.utils.safestring import mark_safe

class MovimentacaoContaCorrenteTable(tables.Table):
    acoes = tables.TemplateColumn(
        template_code='''
            <a href="{% url 'medicos:contacorrente_edit' empresa_id=empresa.id pk=record.pk %}?{{ request.GET.urlencode }}" class="btn btn-sm btn-primary me-1">Editar</a>
            <a href="{% url 'medicos:contacorrente_delete' empresa_id=empresa.id pk=record.pk %}?{{ request.GET.urlencode }}" class="btn btn-sm btn-danger" onclick="return confirm('Confirma exclusão?');">Excluir</a>
        ''',
        verbose_name='Ações',
        orderable=False
    )
    
    descricao_movimentacao = tables.Column(verbose_name='Descrição')
    
    def render_tipo_movimentacao(self, record):
        if record.valor > 0:
            return mark_safe('<span class="badge bg-success">Débito Bancário (Entrada)</span>')
        else:
            return mark_safe('<span class="badge bg-danger">Crédito Bancário (Saída)</span>')
    
    tipo_movimentacao = tables.Column(verbose_name='Tipo', orderable=False, empty_values=())
    data_movimentacao = tables.DateColumn(verbose_name='Data')
    
    def render_valor(self, value, record):
        if value > 0:
            return mark_safe(f'<span style="color:green;">R$ {value:,.2f}</span>')
        else:
            return mark_safe(f'<span style="color:red;">R$ {value:,.2f}</span>')

    valor = tables.Column(verbose_name='Valor (R$)', attrs={"td": {"class": "text-end"}}, orderable=True)
    instrumento_bancario = tables.Column(verbose_name='Instrumento Bancário')
    created_at = tables.DateTimeColumn(verbose_name='Criado em')

    class Meta:
        model = MovimentacaoContaCorrente
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('tipo_movimentacao', 'descricao_movimentacao', 'data_movimentacao', 'valor', 'instrumento_bancario', 'created_at', 'acoes')
        order_by = ('-data_movimentacao', '-created_at')
