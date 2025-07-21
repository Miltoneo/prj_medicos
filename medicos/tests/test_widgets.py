import pytest
from medicos.widgets import ItemDespesaSelect2Widget
from medicos.models.despesas import GrupoDespesa, ItemDespesa
from django.contrib.auth import get_user_model

@pytest.mark.django_db
def test_item_despesa_select2widget_queryset_filtra_por_empresa_id():
    # Cria duas empresas
    Empresa = GrupoDespesa._meta.get_field('empresa').related_model
    from medicos.models.base import Conta
    conta = Conta.objects.create(name='Conta Teste')
    empresa1 = Empresa.objects.create(name='Empresa 1', cnpj='11111111111111', conta=conta)
    empresa2 = Empresa.objects.create(name='Empresa 2', cnpj='22222222222222', conta=conta)
    # Cria grupos de despesa para cada empresa
    grupo1 = GrupoDespesa.objects.create(empresa=empresa1, codigo='G1', descricao='Grupo 1', tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO)
    grupo2 = GrupoDespesa.objects.create(empresa=empresa2, codigo='G2', descricao='Grupo 2', tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO)
    # Cria itens de despesa para cada grupo
    item1 = ItemDespesa.objects.create(grupo_despesa=grupo1, codigo='I1', descricao='Item 1')
    item2 = ItemDespesa.objects.create(grupo_despesa=grupo2, codigo='I2', descricao='Item 2')
    # Widget filtrando por empresa1
    widget = ItemDespesaSelect2Widget(empresa_id=empresa1.id)
    qs = widget.get_queryset()
    assert item1 in qs
    assert item2 not in qs
    # Widget filtrando por empresa2
    widget2 = ItemDespesaSelect2Widget(empresa_id=empresa2.id)
    qs2 = widget2.get_queryset()
    assert item2 in qs2
    assert item1 not in qs2
    # Widget sem empresa_id não retorna nada (segurança)
    widget3 = ItemDespesaSelect2Widget()
    qs3 = widget3.get_queryset()
    assert item1 not in qs3 and item2 not in qs3
