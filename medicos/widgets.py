from django_select2.forms import ModelSelect2Widget


from medicos.models.despesas import ItemDespesa, GrupoDespesa

class ItemDespesaSelect2Widget(ModelSelect2Widget):
    def get_value_queryset(self, value):
        print(f"[DEBUG get_value_queryset] value recebido: {value}")
        qs = ItemDespesa.objects.filter(pk=value)
        print(f"[DEBUG get_value_queryset] queryset: {list(qs)}")
        return qs
    def label_from_instance(self, obj):
        # Garante que o valor selecionado sempre aparece corretamente no Select2
        return str(obj)
    search_fields = [
        'descricao__icontains',
        'grupo_despesa__descricao__icontains',
    ]
    # Permite mostrar todos os itens ao abrir o dropdown
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['data-minimum-input-length'] = 0
        attrs['data-tags'] = 'true'  # Força digitação livre
        attrs['class'] = (attrs.get('class', '') + ' django-select2').strip()
        if self.empresa_id:
            attrs['data-empresa-id'] = self.empresa_id
        return attrs

    def __init__(self, *args, **kwargs):
        self.empresa_id = kwargs.pop('empresa_id', None)
        print(f"[ItemDespesaSelect2Widget] empresa_id recebido: {self.empresa_id}")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self.empresa_id:
            return ItemDespesa.objects.filter(
                grupo_despesa__empresa_id=self.empresa_id,
                grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
            )
        return ItemDespesa.objects.none()
