import django_tables2 as tables
from .models.base import Empresa

class EmpresaTable(tables.Table):
    name = tables.Column(verbose_name="Nome")
    cnpj = tables.Column(verbose_name="CNPJ")
    regime_tributario = tables.Column(verbose_name="Regime Tributário", accessor="get_regime_tributario_display")
    acoes = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'medicos:empresa_detail' record.id %}" class="btn btn-sm btn-secondary">Ver</a>
        <a href="{% url 'medicos:empresa_update' record.id %}" class="btn btn-sm btn-primary">Editar</a>
        <a href="{% url 'medicos:empresa_delete' record.id %}" class="btn btn-sm btn-danger">Excluir</a>
        ''',
        verbose_name="Ações",
        orderable=False
    )

    class Meta:
        model = Empresa
        template_name = "django_tables2/bootstrap5.html"
        fields = ("name", "cnpj", "regime_tributario")
