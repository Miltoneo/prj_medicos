import django_filters
from medicos.models.fiscal import NotaFiscal

class NotaFiscalFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(lookup_expr='icontains', label='Número')
    empresa_destinataria__nome = django_filters.CharFilter(lookup_expr='icontains', label='Empresa')
    tomador = django_filters.CharFilter(lookup_expr='icontains', label='Tomador do Serviço')
    status_recebimento = django_filters.ChoiceFilter(choices=NotaFiscal.STATUS_RECEBIMENTO_CHOICES, label='Status do Recebimento')

    class Meta:
        model = NotaFiscal
        fields = [
            'numero',
            'empresa_destinataria__nome',
            'tomador',
            'status_recebimento',
        ]
