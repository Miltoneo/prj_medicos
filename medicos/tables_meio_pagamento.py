import django_tables2 as tables
from medicos.models.financeiro import MeioPagamento

class MeioPagamentoTable(tables.Table):
    codigo = tables.Column(verbose_name="Código")
    nome = tables.Column(verbose_name="Nome")
    descricao = tables.Column(verbose_name="Descrição")
    acoes = tables.TemplateColumn(
        template_code='''
            <a href="{% url 'medicos:editar_meio_pagamento' pk=record.id %}" class="btn btn-sm btn-primary">Editar</a>
            <a href="{% url 'medicos:excluir_meio_pagamento' pk=record.id %}" class="btn btn-sm btn-danger" onclick="return confirm('Confirma exclusão?');">Excluir</a>
        ''',
        verbose_name="Ações",
        orderable=False
    )
    class Meta:
        model = MeioPagamento
        template_name = 'django_tables2/bootstrap4.html'
        fields = ("codigo", "nome", "descricao")
