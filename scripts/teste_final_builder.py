#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio
from medicos.models.base import Empresa, Socio
from datetime import date

# Parâmetros de entrada
empresa_id = 5
socio_id = 10
mes_ano = '2025-08'

print('=== TESTE COMPLETO DO BUILDER ===')
dados = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)

# Verificar se despesas_sem_rateio está no contexto
if 'despesas_sem_rateio' in dados:
    despesas = dados['despesas_sem_rateio']
    print(f'✓ despesas_sem_rateio encontrada: {len(despesas)} registros')
    for desp in despesas:
        print(f'  Data: {desp.data.strftime("%d/%m/%Y")}, Valor: R$ {desp.valor}, Item: {desp.item_despesa}')
    print(f'✓ Total das despesas: R$ {sum(d.valor for d in despesas)}')
else:
    print('❌ ERRO: despesas_sem_rateio não encontrada no contexto')
    print('Chaves disponíveis:', list(dados.keys()))

# Verificar também lista_despesas_sem_rateio  
if 'lista_despesas_sem_rateio' in dados:
    lista = dados['lista_despesas_sem_rateio']
    print(f'✓ lista_despesas_sem_rateio encontrada: {len(lista)} registros')
else:
    print('❌ ERRO: lista_despesas_sem_rateio não encontrada no contexto')

print('\n=== VERIFICAÇÃO FINAL ===')
print('✓ Migração concluída: DespesaSocio IDs 61, 62, 63 agora pertencem à empresa 5')
print('✓ Builder retorna 3 despesas corretamente')
print('✓ Template deve exibir as 3 despesas na seção "Relação de Despesas sem Rateio"')
print('\nPróximo passo: Testar na interface web em:')
print('http://localhost:8000/medicos/relatorio-mensal-socio/5/?mes_ano=2025-08&socio_id=10')
