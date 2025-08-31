from medicos.models import Empresa
from medicos.models.base import Socio
from medicos.models.despesas import DespesaSocio, ItemDespesa, GrupoDespesa
from datetime import date

empresa = Empresa.objects.get(id=5)
socio = Socio.objects.get(id=10)
grupos = GrupoDespesa.objects.filter(empresa=empresa, tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO)
if grupos.exists():
    grupo = grupos.first()
    itens = ItemDespesa.objects.filter(grupo_despesa=grupo)
    if itens.exists():
        item = itens.first()
        despesa = DespesaSocio.objects.create(
            socio=socio,
            item_despesa=item,
            data=date(2025, 8, 30),
            valor=123.00
        )
        print(f'Despesa criada: ID {despesa.id}')
    else:
        print('Nenhum ItemDespesa encontrado para o grupo SEM_RATEIO')
else:
    print('Nenhum GrupoDespesa SEM_RATEIO encontrado para a empresa')
