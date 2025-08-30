import django_tables2 as tables
from medicos.models.fiscal import NotaFiscal
from django.utils.safestring import mark_safe

class NotaFiscalRecebimentoTable(tables.Table):
    numero = tables.Column(verbose_name='Número')
    dtEmissao = tables.DateColumn(verbose_name='Data Emissão', format='d/m/Y')
    tomador = tables.Column(verbose_name='Tomador do Serviço')
    val_bruto = tables.Column(verbose_name='Valor Bruto (R$)', attrs={"td": {"class": "text-end"}})
    val_liquido = tables.Column(verbose_name='Valor Líquido (R$)', attrs={"td": {"class": "text-end"}})
    meio_pagamento = tables.Column(verbose_name='Meio de Pagamento', default='-')
    dtRecebimento = tables.DateColumn(verbose_name='Data Recebimento', format='d/m/Y')
    status_recebimento = tables.Column(verbose_name='Status')
    
    def render_status_rateio(self, record):
        """Renderiza o status do rateio da nota fiscal"""
        if not record.tem_rateio:
            return mark_safe('<span class="badge bg-secondary">Sem Rateio</span>')
        elif record.rateio_completo:
            return mark_safe('<span class="badge bg-success">Rateio Completo</span>')
        else:
            return mark_safe(f'<span class="badge bg-warning">Rateio {record.percentual_total_rateado:.1f}%</span>')
    
    status_rateio = tables.Column(verbose_name='Rateio', orderable=False, empty_values=())
    
    def render_actions(self, record):
        """Renderiza ações condicionais baseadas no status do rateio"""
        # Verificação das condições de rateio
        tem_rateio = record.tem_rateio
        rateio_completo = record.rateio_completo
        percentual = record.percentual_total_rateado
        
        # REGRA: Apenas notas com rateio COMPLETO podem ser editadas
        if tem_rateio and rateio_completo:
            # Apenas notas com rateio completo (100%): permite edição
            return mark_safe(f'''
                <a href="/medicos/recebimento-notas/{record.pk}/editar/" 
                   class="btn btn-sm btn-success" 
                   title="Rateio completo - pode editar">
                    <i class="fas fa-edit me-1"></i>Editar Recebimento
                </a>
            ''')
        elif not tem_rateio:
            # Notas sem rateio: bloqueia edição
            return mark_safe(f'''
                <button type="button" 
                        class="btn btn-sm btn-warning" 
                        disabled 
                        title="Nota sem rateio - não pode editar">
                    <i class="fas fa-ban me-1"></i>Sem Rateio
                </button>
            ''')
        else:
            # Notas com rateio incompleto: bloqueia edição
            return mark_safe(f'''
                <button type="button" 
                        class="btn btn-sm btn-danger" 
                        disabled 
                        title="Rateio incompleto: {percentual:.1f}% de 100%">
                    <i class="fas fa-lock me-1"></i>Rateio Incompleto ({percentual:.1f}%)
                </button>
            ''')
    
    actions = tables.Column(verbose_name='Ações', orderable=False, empty_values=())

    def render_val_bruto(self, value):
        """Formata o valor bruto com símbolo da moeda"""
        if value is None:
            return '-'
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    def render_val_liquido(self, value):
        """Formata o valor líquido com símbolo da moeda"""
        if value is None:
            return '-'
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    class Meta:
        model = NotaFiscal
        fields = ('numero', 'dtEmissao', 'tomador', 'val_bruto', 'val_liquido', 'status_rateio', 'meio_pagamento', 'dtRecebimento', 'status_recebimento')
        attrs = {'class': 'table table-striped'}
