import django_tables2 as tables
from medicos.models.fiscal import NotaFiscalRateioMedico

class NotaFiscalRateioMedicoTable(tables.Table):
    valor_iss_medico = tables.Column(verbose_name='ISS')
    valor_pis_medico = tables.Column(verbose_name='PIS')
    valor_cofins_medico = tables.Column(verbose_name='COFINS')
    valor_ir_medico = tables.Column(verbose_name='IR')
    valor_csll_medico = tables.Column(verbose_name='CSLL')
    medico = tables.Column(accessor='medico.pessoa.name', verbose_name='Médico')
    nota_fiscal = tables.Column(accessor='nota_fiscal.numero', verbose_name='Nota Fiscal')
    tomador = tables.Column(accessor='nota_fiscal.tomador', verbose_name='Tomador')
    # Removido campo competencia
    data_emissao = tables.DateColumn(accessor='nota_fiscal.dtEmissao', verbose_name='Emissão')
    data_recebimento = tables.DateColumn(accessor='nota_fiscal.dtRecebimento', verbose_name='Recebimento')
    percentual_participacao = tables.Column(verbose_name='% Rateio')
    valor_bruto_medico = tables.Column(verbose_name='Valor Bruto Rateado')
    valor_liquido_medico = tables.Column(verbose_name='Valor Líquido')

    class Meta:
        model = NotaFiscalRateioMedico
        template_name = 'django_tables2/bootstrap.html'
        fields = ('medico', 'nota_fiscal', 'tomador', 'data_emissao', 'data_recebimento', 'percentual_participacao', 'valor_bruto_medico', 'valor_liquido_medico', 'valor_iss_medico', 'valor_pis_medico', 'valor_cofins_medico', 'valor_ir_medico', 'valor_csll_medico')
        order_by = ['medico__pessoa__name']  # Ordenação alfabética por nome do médico
