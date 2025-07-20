
import os
import sys
import django
from datetime import datetime

# Configuração standalone Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
from medicos.models.base import Socio

def debug_despesas_socio(empresa_id, socio_id, competencia):
    ano, mes = competencia.split('-')
    data_ref = f"{ano}-{mes}-01"
    print(f"Empresa: {empresa_id} | Sócio: {socio_id} | Competência: {competencia}")

    # Despesas individuais
    despesas_ind = DespesaSocio.objects.filter(
        socio_id=socio_id,
        socio__empresa_id=empresa_id,
        data__year=ano, data__month=mes
    )
    print(f"Despesas Individuais: {despesas_ind.count()}")
    for d in despesas_ind:
        print(f"  [IND] {d.id} | {d.item_despesa.descricao} | Valor: {d.valor}")

    # Despesas rateadas
    rateadas = DespesaRateada.objects.filter(
        item_despesa__grupo_despesa__empresa_id=empresa_id,
        data__year=ano, data__month=mes
    )
    print(f"Despesas Rateadas: {rateadas.count()}")
    for dr in rateadas:
        rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
            dr.item_despesa, Socio.objects.get(id=socio_id), dr.data
        )
        if rateio and rateio.percentual_rateio:
            valor_apropriado = dr.valor * (rateio.percentual_rateio / 100)
            print(f"  [RATEIO] {dr.id} | {dr.item_despesa.descricao} | Valor: {dr.valor} | %: {rateio.percentual_rateio} | Apropriado: {valor_apropriado}")
        else:
            print(f"  [RATEIO] {dr.id} | {dr.item_despesa.descricao} | Sócio sem rateio configurado")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python debug_despesas_socio.py <empresa_id> <socio_id> <competencia AAAA-MM>")
        sys.exit(1)
    debug_despesas_socio(sys.argv[1], sys.argv[2], sys.argv[3])
