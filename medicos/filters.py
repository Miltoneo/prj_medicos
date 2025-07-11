import django_filters
from .models.base import Empresa
from .models.fiscal import Aliquotas
from medicos.models.despesas import GrupoDespesa
from .models import ItemDespesa

class EmpresaFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label='Nome', lookup_expr='icontains')
    
    class Meta:
        model = Empresa
        fields = ['name']

class AliquotasFilter(django_filters.FilterSet):
    ativa = django_filters.BooleanFilter(label="Ativa")
    class Meta:
        model = Aliquotas
        fields = ["ativa"]

class GrupoDespesaFilter(django_filters.FilterSet):
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')

    class Meta:
        model = GrupoDespesa
        fields = ['descricao']

class ItemDespesaFilter(django_filters.FilterSet):
    codigo = django_filters.CharFilter(lookup_expr='icontains', label='Código')
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')
    grupo = django_filters.CharFilter(field_name='grupo__descricao', lookup_expr='icontains', label='Grupo')

    class Meta:
        model = ItemDespesa
        fields = ['codigo', 'descricao', 'grupo']
