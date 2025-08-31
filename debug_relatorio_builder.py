import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','prj_medicos.settings')
django.setup()
from medicos.relatorios.builders import montar_relatorio_mensal_socio

res = montar_relatorio_mensal_socio(5, '2025-08', socio_id=10)
print('TYPE res:', type(res))
# res is expected to be a dict-like contexto. Print keys and summary of important lists
if isinstance(res, dict):
	print('keys:', list(res.keys()))
	# relatorio may be a model instance inside res['relatorio'] or a dict
	rel = res.get('relatorio')
	print('relatorio type:', type(rel))
	try:
		lista_sem = getattr(rel, 'lista_despesas_sem_rateio', None) if not isinstance(rel, dict) else rel.get('lista_despesas_sem_rateio')
		lista_com = getattr(rel, 'lista_despesas_com_rateio', None) if not isinstance(rel, dict) else rel.get('lista_despesas_com_rateio')
		print('lista_despesas_sem_rateio (from rel):', type(lista_sem), 'len=', len(lista_sem) if lista_sem is not None else 'N/A')
		print('lista_despesas_com_rateio (from rel):', type(lista_com), 'len=', len(lista_com) if lista_com is not None else 'N/A')
	except Exception as e:
		print('Erro ao inspecionar rel listas:', e)

	# Also check if res has top-level lista_* keys
	lsem_top = res.get('lista_despesas_sem_rateio')
	lcom_top = res.get('lista_despesas_com_rateio')
	print('lista_despesas_sem_rateio (top-level):', type(lsem_top), 'len=', len(lsem_top) if lsem_top is not None else 'N/A')
	print('lista_despesas_com_rateio (top-level):', type(lcom_top), 'len=', len(lcom_top) if lcom_top is not None else 'N/A')
else:
	print('Unexpected builder return type; repr:', repr(res))
