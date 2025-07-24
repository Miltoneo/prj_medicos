import django_filters
from medicos.models.fiscal import NotaFiscal

class NotaFiscalFilter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Padroniza todos os campos como form-control, exceto status_recebimento (form-select)
        for name, field in self.form.fields.items():
            if name == 'status_recebimento':
                field.widget.attrs['class'] = 'form-select'
            elif name == 'mes_ano_emissao':
                field.widget.attrs['class'] = 'form-control'
                # Força input type month para UX consistente
                try:
                    field.widget.input_type = 'month'
                except Exception:
                    pass
            else:
                field.widget.attrs['class'] = 'form-control'
    numero = django_filters.CharFilter(lookup_expr='icontains', label='Número')
    tomador = django_filters.CharFilter(lookup_expr='icontains', label='Tomador do Serviço')
    cnpj_tomador = django_filters.CharFilter(lookup_expr='icontains', label='CNPJ do Tomador')
    status_recebimento = django_filters.ChoiceFilter(choices=NotaFiscal.STATUS_RECEBIMENTO_CHOICES, label='Status do Recebimento')
    mes_ano_emissao = django_filters.CharFilter(label='Mês/Ano de Emissão', method='filter_mes_ano_emissao')

    def filter_mes_ano_emissao(self, queryset, name, value):
        """
        Filtra dtEmissao pelo mês/ano informado (formato yyyy-mm).
        Aceita valores com ou sem espaços e ignora valores inválidos.
        """
        if value:
            value = value.strip()
            if len(value) == 7 and '-' in value:
                try:
                    ano, mes = value.split('-')
                    ano = int(ano)
                    mes = int(mes)
                    if 1 <= mes <= 12:
                        return queryset.filter(dtEmissao__year=ano, dtEmissao__month=mes)
                except Exception:
                    pass
        return queryset

    class Meta:
        model = NotaFiscal
        fields = [
            'mes_ano_emissao',
            'status_recebimento',
            'numero',
            'tomador',
            'cnpj_tomador',
        ]
