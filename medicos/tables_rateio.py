import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from django.urls import reverse

class NotaFiscalRateioTable(tables.Table):
    numero = tables.Column(verbose_name="Nº NF")
    empresa_destinataria = tables.Column(verbose_name="Empresa")
    tomador = tables.Column(verbose_name="Tomador")
    val_bruto = tables.Column(verbose_name="Valor Bruto (R$)")
    val_liquido = tables.Column(verbose_name="Valor Líquido (R$)")
    dtEmissao = tables.DateColumn(verbose_name="Emissão")
    rateio = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'medicos:lista_rateio_medicos' nota_id=record.id %}" class="btn btn-sm btn-primary">Ratear</a>
        ''',
        verbose_name="Rateio",
        orderable=False
    )
    class Meta:
        model = NotaFiscal
        template_name = "django_tables2/bootstrap5.html"
        fields = ("numero", "empresa_destinataria", "tomador", "val_bruto", "val_liquido", "dtEmissao")

class RateioMedicoTable(tables.Table):
    medico = tables.Column(verbose_name="Médico")
    valor_bruto_medico = tables.Column(verbose_name="Valor Bruto (R$)")
    percentual_participacao = tables.Column(verbose_name="% Participação")
    valor_liquido_medico = tables.Column(verbose_name="Valor Líquido (R$)")
    acoes = tables.TemplateColumn(
        template_code='''
        <a href="{% url 'medicos:editar_rateio_medico' nota_id=record.nota_fiscal.id rateio_id=record.id %}" class="btn btn-sm btn-warning">Editar</a>
        <a href="{% url 'medicos:excluir_rateio_medico' nota_id=record.nota_fiscal.id rateio_id=record.id %}" class="btn btn-sm btn-danger">Excluir</a>
        ''',
        verbose_name="Ações",
        orderable=False
    )
    class Meta:
        model = NotaFiscalRateioMedico
        template_name = "django_tables2/bootstrap5.html"
        fields = ("medico", "valor_bruto_medico", "percentual_participacao", "valor_liquido_medico")
