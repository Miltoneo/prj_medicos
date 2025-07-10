import django_filters
from .models.base import Socio

class SocioFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(label='Nome', field_name='pessoa__name', lookup_expr='icontains')
    cpf = django_filters.CharFilter(label='CPF', field_name='pessoa__cpf', lookup_expr='icontains')
    ativo = django_filters.BooleanFilter(label='Ativo')

    class Meta:
        model = Socio
        fields = ['nome', 'cpf', 'ativo']
