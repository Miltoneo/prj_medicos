import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico
from django.urls import reverse

class NotaFiscalRateioTable(tables.Table):
    numero = tables.Column(verbose_name="Número", orderable=True)
    dtEmissao = tables.DateColumn(verbose_name="Data Emissão", orderable=True, format="d/m/Y")
    tomador = tables.Column(verbose_name="Tomador", orderable=True)
    cnpj_tomador = tables.Column(verbose_name="CNPJ do Tomador", orderable=True)
    val_bruto = tables.Column(verbose_name="Valor Bruto (R$)", orderable=True)
    total_rateado = tables.TemplateColumn(
        template_code='''
        {% if record.percentual_total_rateado %}
          <span class="{% if record.rateio_completo %}text-success fw-bold{% else %}text-warning{% endif %}">
            {{ record.percentual_total_rateado|floatformat:1 }}%
          </span>
          <br>
          <small class="text-muted">
            R$ {{ record.valor_total_rateado|floatformat:2 }}
          </small>
        {% else %}
          <span class="text-muted">-</span>
        {% endif %}
        ''',
        verbose_name="Total Rateado",
        orderable=False
    )
    selecionar = tables.TemplateColumn(
        template_code='''
        <form method="get" style="display:inline;">
          {% for key, value in request.GET.items %}
            {% if key != 'nota_id' %}
              <input type="hidden" name="{{ key }}" value="{{ value }}" />
            {% endif %}
          {% endfor %}
          <input type="hidden" name="nota_id" value="{{ record.id }}" />
          <button type="submit" class="btn btn-sm btn-outline-primary"><i class="fas fa-hand-pointer"></i> Selecionar</button>
        </form>
        ''',
        verbose_name="Ações",
        orderable=False
    )
    
    class Meta:
        model = NotaFiscal
        template_name = "django_tables2/bootstrap5.html"
        fields = ("numero", "dtEmissao", "tomador", "cnpj_tomador", "val_bruto", "total_rateado")
        order_by = ("-dtEmissao",)  # Ordenação padrão por data de emissão (mais recente primeiro)
        row_attrs = {
            'class': lambda record: 'table-success' if record.rateio_completo else ''
        }
        
    def render_val_bruto(self, value):
        """Formatação personalizada para valor bruto"""
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
