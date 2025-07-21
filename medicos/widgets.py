from django_select2.forms import ModelSelect2Widget


from medicos.models.despesas import ItemDespesa, GrupoDespesa

class ItemDespesaSelect2Widget(ModelSelect2Widget):
    search_fields = [
        'descricao__icontains',
        'grupo_despesa__descricao__icontains',
    ]
    # Permite mostrar todos os itens ao abrir o dropdown
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['data-minimum-input-length'] = 0
        return attrs

    def __init__(self, *args, **kwargs):
        self.empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self.empresa_id:
            return ItemDespesa.objects.filter(grupo_despesa__empresa_id=self.empresa_id)
        return ItemDespesa.objects.none()
