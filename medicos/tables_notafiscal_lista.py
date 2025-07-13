import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal

class NotaFiscalListaTable(tables.Table):
    acoes = tables.TemplateColumn(
        template_code='''
            <a href="{% url 'medicos:editar_nota_fiscal' record.pk %}" class="btn btn-sm btn-primary me-1" title="Editar">
                <i class="bi bi-pencil"></i>
            </a>
            <a href="{% url 'medicos:excluir_nota_fiscal' record.pk %}" class="btn btn-sm btn-danger" title="Excluir" onclick="return confirm('Confirma a exclusão desta nota fiscal?');">
                <i class="bi bi-trash"></i>
            </a>
        ''',
        verbose_name='Ações',
        orderable=False
    )
    numero = tables.Column(verbose_name='Número da NF')
    empresa_destinataria = tables.Column(verbose_name='Empresa Emitente', accessor='empresa_destinataria.nome')
    tomador = tables.Column(verbose_name='Tomador do Serviço')
    cnpj_tomador = tables.Column(verbose_name='CNPJ do Tomador')
    tipo_servico = tables.Column(verbose_name='Tipo de Serviço', accessor='get_tipo_servico_display')
    dtEmissao = tables.DateColumn(verbose_name='Data de Emissão', format='d/m/Y')
    dtRecebimento = tables.DateColumn(verbose_name='Data de Recebimento', format='d/m/Y')
    val_bruto = tables.Column(verbose_name='Valor Bruto (R$)')
    val_ISS = tables.Column(verbose_name='Valor ISS (R$)')
    val_PIS = tables.Column(verbose_name='Valor PIS (R$)')
    val_COFINS = tables.Column(verbose_name='Valor COFINS (R$)')
    val_IR = tables.Column(verbose_name='Valor IRPJ (R$)')
    val_CSLL = tables.Column(verbose_name='Valor CSLL (R$)')
    val_liquido = tables.Column(verbose_name='Valor Líquido (R$)')
    status_recebimento = tables.Column(verbose_name='Status do Recebimento', accessor='get_status_recebimento_display')
    meio_pagamento = tables.Column(verbose_name='Meio de Pagamento', accessor='meio_pagamento.nome')

    class Meta:
        model = NotaFiscal
        fields = (
            'numero',
            'empresa_destinataria',
            'tomador',
            'cnpj_tomador',
            'tipo_servico',
            'dtEmissao',
            'dtRecebimento',
            'val_bruto',
            'val_ISS',
            'val_PIS',
            'val_COFINS',
            'val_IR',
            'val_CSLL',
            'val_liquido',
            'status_recebimento',
            'meio_pagamento',
            'acoes',
        )
