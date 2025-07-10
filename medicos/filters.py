import django_filters
from .models.base import Empresa

class EmpresaFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label='Nome', lookup_expr='icontains')
    
    class Meta:
        model = Empresa
        fields = ['name']
