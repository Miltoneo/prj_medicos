
import datetime
import django_filters
from django import forms
from medicos.models.despesas import ItemDespesaRateioMensal, ItemDespesa
from medicos.models.base import Socio
from medicos.models.fiscal import NotaFiscalRateioMedico


# Filtro para configuração de rateio mensal de item de despesa
class ItemDespesaRateioMensalFilter(django_filters.FilterSet):
    item_despesa = django_filters.ModelChoiceFilter(queryset=ItemDespesa.objects.all(), label="Item de Despesa")
    socio = django_filters.ModelChoiceFilter(queryset=Socio.objects.all(), label="Sócio")
    data_referencia = django_filters.DateFilter(field_name="data_referencia", lookup_expr="exact", label="Mês de Competência")

    class Meta:
        model = ItemDespesaRateioMensal
        fields = ['item_despesa', 'socio', 'data_referencia']


class NotaFiscalRateioMedicoFilter(django_filters.FilterSet):
    medico = django_filters.ModelChoiceFilter(queryset=Socio.objects.none(), label="Médico")  # Será definido dinamicamente
    nota_fiscal = django_filters.CharFilter(field_name='nota_fiscal__numero', lookup_expr='icontains', label="Nota Fiscal")
    competencia = django_filters.CharFilter(
        label='Competência',
        method='filter_competencia',
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control',
            'value': datetime.date.today().strftime('%Y-%m')
        })
    )
    data_recebimento = django_filters.CharFilter(
        label='Data Recebimento',
        method='filter_data_recebimento',
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control'
        })
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        
        # Filtrar médicos pela empresa ativa da sessão
        if request and hasattr(request, 'session'):
            empresa_id = request.session.get('empresa_id')
            if empresa_id:
                # Filtrar sócios/médicos pela empresa ativa
                from medicos.models.base import Empresa
                try:
                    empresa = Empresa.objects.get(id=int(empresa_id))
                    self.filters['medico'].queryset = Socio.objects.filter(
                        ativo=True,
                        empresa=empresa,
                        pessoa__isnull=False  # Garantir que há pessoa associada
                    ).select_related('pessoa').order_by('pessoa__name')
                except Empresa.DoesNotExist:
                    self.filters['medico'].queryset = Socio.objects.none()
            else:
                self.filters['medico'].queryset = Socio.objects.none()
        else:
            self.filters['medico'].queryset = Socio.objects.none()

    def filter_competencia(self, queryset, name, value):
        # value esperado: 'YYYY-MM'
        try:
            year, month = value.split('-')
            return queryset.filter(nota_fiscal__dtEmissao__year=year, nota_fiscal__dtEmissao__month=month)
        except Exception:
            return queryset

    def filter_data_recebimento(self, queryset, name, value):
        # value esperado: 'YYYY-MM' - filtra por data de recebimento
        try:
            year, month = value.split('-')
            return queryset.filter(nota_fiscal__dtRecebimento__year=year, nota_fiscal__dtRecebimento__month=month)
        except Exception:
            return queryset

    class Meta:
        model = NotaFiscalRateioMedico
        fields = ['medico', 'nota_fiscal', 'competencia', 'data_recebimento']
