#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio

print('TESTE SIMPLES DO PROPERTY')

try:
    dados = montar_relatorio_mensal_socio(5, '2025-08', socio_id=10)
    relatorio = dados['relatorio']
    
    print(f'Relatorio criado: {relatorio}')
    print(f'Lista JSON tem {len(relatorio.lista_despesas_sem_rateio)} itens')
    
    despesas_property = relatorio.despesas_sem_rateio
    print(f'Property retorna {len(despesas_property)} despesas')
    
    for i, desp in enumerate(despesas_property):
        print(f'Despesa {i+1}: {desp.data} - R$ {desp.valor} - {desp.descricao}')
    
    print('SUCESSO: Property funcionando!')
    
except Exception as e:
    print(f'ERRO: {e}')
    import traceback
    traceback.print_exc()
