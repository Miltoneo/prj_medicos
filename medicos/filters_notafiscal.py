import django_filters
from medicos.models.fiscal import NotaFiscal

class NotaFiscalFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(lookup_expr='icontains', label='Número')
    empresa_destinataria__nome = django_filters.CharFilter(lookup_expr='icontains', label='Empresa')
    dtEmissao = django_filters.DateFromToRangeFilter(label='Data de Emissão')
    status_recebimento = django_filters.ChoiceFilter(choices=NotaFiscal.STATUS_RECEBIMENTO_CHOICES, label='Status')

    class Meta:
        model = NotaFiscal
        fields = ['numero', 'empresa_destinataria__nome', 'dtEmissao', 'status_recebimento']
