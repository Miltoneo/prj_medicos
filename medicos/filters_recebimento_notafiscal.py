import django_filters
from medicos.models.fiscal import NotaFiscal

class NotaFiscalRecebimentoFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(lookup_expr='icontains', label='Número NF')
    dtEmissao = django_filters.DateFilter(label='Data de Emissão')
    dtRecebimento = django_filters.DateFilter(label='Data de Recebimento')
    status_recebimento = django_filters.ChoiceFilter(
        choices=[('pendente', 'Pendente'), ('recebido', 'Recebido')],
        label='Status de Recebimento'
    )

    class Meta:
        model = NotaFiscal
        fields = ['numero', 'dtEmissao', 'dtRecebimento', 'status_recebimento']
