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
            return mark_safe('<span class="badge bg-success">Entrada na conta</span>')
        else:
            return mark_safe('<span class="badge bg-danger">Saída da conta</span>')
    
    tipo_movimentacao = tables.Column(verbose_name='Tipo', orderable=False, empty_values=())
    data_movimentacao = tables.DateColumn(verbose_name='Data')
    
    def render_valor(self, value, record):
        if value > 0:
            return mark_safe(f'<span style="color:green;">R$ {value:,.2f}</span>')
        else:
            return mark_safe(f'<span style="color:red;">R$ {value:,.2f}</span>')

    valor = tables.Column(verbose_name='Valor (R$)', attrs={"td": {"class": "text-end"}}, orderable=True)
    
    def render_socio(self, record):
        if record.socio:
            return record.socio.pessoa.name if record.socio.pessoa else f"Sócio #{record.socio.pk}"
        return mark_safe('<span class="text-muted">-</span>')
    
    socio = tables.Column(verbose_name='Médico/Sócio', orderable=False, empty_values=())
    
    def render_nota_fiscal(self, record):
        if record.nota_fiscal:
            return f"NF {record.nota_fiscal.numero} - {record.nota_fiscal.dtEmissao.strftime('%d/%m/%Y')}" if record.nota_fiscal.numero else f"NF #{record.nota_fiscal.pk}"
        return mark_safe('<span class="text-muted">-</span>')
    
    nota_fiscal = tables.Column(verbose_name='Nota Fiscal', orderable=False, empty_values=())
    instrumento_bancario = tables.Column(verbose_name='Instrumento Bancário')
    created_at = tables.DateTimeColumn(verbose_name='Criado em')

    class Meta:
        model = MovimentacaoContaCorrente
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('tipo_movimentacao', 'descricao_movimentacao', 'data_movimentacao', 'valor', 'socio', 'nota_fiscal', 'instrumento_bancario', 'created_at', 'acoes')
        order_by = ('-data_movimentacao', '-created_at')
