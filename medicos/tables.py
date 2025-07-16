import django_tables2 as tables
from .models.base import Empresa
from .models.fiscal import Aliquotas
from .models import ItemDespesa
from .models.financeiro import DescricaoMovimentacaoFinanceira

class EmpresaTable(tables.Table):
    name = tables.Column(verbose_name="Nome")
    cnpj = tables.Column(verbose_name="CNPJ")
    regime_tributario = tables.Column(verbose_name="Regime Tributário", accessor="get_regime_tributario_display")
    acoes = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'medicos:empresa_detail' empresa_id=record.id %}" class="btn btn-sm btn-secondary">Ver</a>
        <a href="{% url 'medicos:empresa_update' empresa_id=record.id %}" class="btn btn-sm btn-primary">Editar</a>
        <a href="{% url 'medicos:empresa_delete' empresa_id=record.id %}" class="btn btn-sm btn-danger">Excluir</a>
        ''',
        verbose_name="Ações",
        orderable=False
    )

    class Meta:
        model = Empresa
        template_name = "django_tables2/bootstrap5.html"
        fields = ("name", "cnpj", "regime_tributario")

class AliquotasTable(tables.Table):
    acoes = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'medicos:aliquota_edit' empresa_id=empresa.id aliquota_id=record.id %}" class="btn btn-sm btn-primary">Editar</a>
        ''',
        verbose_name="Ações",
        orderable=False
    )
    class Meta:
        model = Aliquotas
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            "data_vigencia_inicio", "data_vigencia_fim", "ativa",
            "ISS", "PIS", "COFINS", "IRPJ_BASE_CAL", "IRPJ_ALIQUOTA_OUTROS", "IRPJ_ALIQUOTA_CONSULTA",
            "IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL", "IRPJ_ADICIONAL", "CSLL_BASE_CAL", "CSLL_ALIQUOTA_OUTROS",
            "CSLL_ALIQUOTA_CONSULTA", "observacoes"
        )
        order_by = "-data_vigencia_inicio"

class ItemDespesaTable(tables.Table):
    grupo = tables.Column(accessor='grupo.descricao', verbose_name='Grupo')
    codigo = tables.Column(verbose_name='Código')
    descricao = tables.Column(verbose_name='Descrição')
    acoes = tables.TemplateColumn(
        template_code='''
        {% with empresa_id=record.conta.empresas.first.id %}
          {% if empresa_id %}
            <a href="{% url 'medicos:item_despesa_edit' empresa_id=empresa_id grupo_id=record.grupo.id item_id=record.id %}" class="btn btn-sm btn-primary">Editar</a>
            <a href="{% url 'medicos:item_despesa_delete' empresa_id=empresa_id grupo_id=record.grupo.id item_id=record.id %}" class="btn btn-sm btn-danger" onclick="return confirm('Confirma exclusão?');">Excluir</a>
          {% else %}
            <span class="text-muted">Empresa não definida</span>
          {% endif %}
        {% endwith %}
        ''',
        verbose_name="Ações",
        orderable=False
    )
    class Meta:
        model = ItemDespesa
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('grupo', 'codigo', 'descricao', 'acoes')
        order_by = ('grupo', 'codigo', 'descricao')

class DescricaoMovimentacaoFinanceiraTable(tables.Table):
    codigo_contabil = tables.Column(verbose_name='Código Contábil')
    descricao = tables.Column(verbose_name='Descrição')
    observacoes = tables.Column(verbose_name='Observações')
    actions = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'financeiro:descricao_movimentacao_edit' empresa_id=record.empresa_id pk=record.pk %}" class="btn btn-sm btn-primary">Editar</a>
        <a href="{% url 'financeiro:descricao_movimentacao_delete' empresa_id=record.empresa_id pk=record.pk %}" class="btn btn-sm btn-danger">Excluir</a>
        ''',
        verbose_name='Ações', orderable=False
    )

    class Meta:
        model = DescricaoMovimentacaoFinanceira
        template_name = "django_tables2/bootstrap5.html"
        fields = ('codigo_contabil', 'descricao', 'observacoes')
        sequence = ('codigo_contabil', 'descricao', 'observacoes', 'actions')
        attrs = {'class': 'table table-striped'}
