

# Imports de terceiros
import django_tables2 as tables

# Imports do projeto
from medicos.models.despesas import DespesaSocio, DespesaRateada

# Tabela para lista de despesas de sócio

class DespesaSocioTable(tables.Table):
    data = tables.DateColumn(verbose_name='Data', format='d/m/Y', attrs={"td": {"style": "min-width: 110px; max-width: 120px; white-space: nowrap;"}})
    socio = tables.Column(verbose_name='Sócio', attrs={"td": {"style": "min-width: 160px; max-width: 240px; white-space: nowrap;"}})
    descricao = tables.Column(verbose_name='Descrição')
    grupo = tables.Column(verbose_name='Grupo', attrs={"td": {"style": "min-width: 200px; max-width: 340px; white-space: nowrap;"}})
    valor_total = tables.Column(verbose_name='Valor Total (R$)', attrs={"td": {"style": "min-width: 120px; max-width: 180px; white-space: nowrap; text-align: right;"}})
    taxa_rateio = tables.Column(verbose_name='Taxa de Rateio (%)')
    valor_apropriado = tables.Column(verbose_name='Valor Apropriado (R$)')

    class Meta:
        template_name = 'django_tables2/bootstrap5.html'
        fields = ('data', 'socio', 'descricao', 'grupo', 'valor_total', 'taxa_rateio', 'valor_apropriado', 'acoes')
        sequence = ('data', 'socio', 'descricao', 'grupo', 'valor_total', 'taxa_rateio', 'valor_apropriado', 'acoes')
    acoes = tables.TemplateColumn(
        template_code='''
        {% if record.id %}
        {% with empresa_id=record.socio.empresa.id|default:request.resolver_match.kwargs.empresa_id %}
        <a href="{% url 'medicos:despesas_socio_form_edit' empresa_id=empresa_id pk=record.id %}" class="btn btn-sm btn-primary me-1">
            <i class="fas fa-edit"></i> Editar
        </a>
        <a href="{% url 'medicos:despesas_socio_confirm_delete' empresa_id=empresa_id pk=record.id %}" class="btn btn-sm btn-danger">
            <i class="fas fa-trash-alt"></i> Excluir
        </a>
        {% endwith %}
        {% endif %}
        ''',
        verbose_name='Ações',
        orderable=False,
        attrs={"td": {"class": "text-center", "style": "min-width: 160px; width: 180px;"}}
    )

    def render_socio(self, record):
        socio = record.get('socio')
        if hasattr(socio, 'pessoa'):
            return getattr(socio.pessoa, 'name', str(socio))
        return str(socio) if socio else '-'

    def render_descricao(self, record):
        val = record.get('descricao', '-')
        return val if val else '-'

    def render_grupo(self, record):
        val = record.get('grupo', '-')
        return val if val else '-'

    def render_valor_total(self, record):
        val = record.get('valor_total', 0)
        try:
            return f'R$ {float(val):,.2f}'
        except Exception:
            return '-'

    def render_taxa_rateio(self, record):
        val = record.get('taxa_rateio', '-')
        if val == '-' or val is None:
            return '-'
        try:
            return f'{float(val):.2f}'
        except Exception:
            return '-'

    def render_valor_apropriado(self, record):
        val = record.get('valor_apropriado', 0)
        try:
            return f'R$ {float(val):,.2f}'
        except Exception:
            return '-'

    class Meta:
        template_name = 'django_tables2/bootstrap5.html'
        fields = ('socio', 'descricao', 'grupo', 'valor_total', 'taxa_rateio', 'valor_apropriado', 'acoes')

# Tabela para lista de despesas da empresa
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
