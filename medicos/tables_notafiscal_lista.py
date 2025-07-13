import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal

class NotaFiscalListaTable(tables.Table):
    numero = tables.Column(verbose_name='Número')
    empresa_destinataria = tables.Column(verbose_name='Empresa', accessor='empresa_destinataria.nome')
    dtEmissao = tables.DateColumn(verbose_name='Data de Emissão', format='d/m/Y')
    val_bruto = tables.Column(verbose_name='Valor Bruto')
    status_recebimento = tables.Column(verbose_name='Status', accessor='get_status_recebimento_display')

    class Meta:
        model = NotaFiscal
        template_name = 'django_tables2/bootstrap5.html'
        fields = ('numero', 'empresa_destinataria', 'dtEmissao', 'val_bruto', 'status_recebimento')
