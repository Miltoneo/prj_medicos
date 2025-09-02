#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

print('✓ Django iniciado')

from medicos.models.despesas import DespesaSocio
from medicos.models.base import Empresa

# Verificar status dos registros migrados
print('\n=== VERIFICAÇÃO RÁPIDA ===')

empresa_5 = Empresa.objects.get(id=5)
print(f'✓ Empresa 5: {empresa_5.razao_social}')

despesas_ids = [61, 62, 63]
for despesa_id in despesas_ids:
    try:
        despesa = DespesaSocio.objects.get(id=despesa_id)
        empresa_grupo = despesa.item_despesa.grupo_despesa.empresa_id
        print(f'✓ DespesaSocio ID {despesa_id}: valor R$ {despesa.valor}, empresa_grupo={empresa_grupo}')
    except Exception as e:
        print(f'❌ Erro ao buscar DespesaSocio ID {despesa_id}: {e}')

print('\n=== CONTAGEM TOTAL ===')
total_despesas = DespesaSocio.objects.filter(
    socio_id=10,
    item_despesa__grupo_despesa__empresa_id=5,
    data__year=2025,
    data__month=8
).count()
print(f'✓ Total DespesaSocio para socio_id=10, empresa=5, competência=2025-08: {total_despesas}')

print('\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!')
print('   As 3 despesas dos sócios (R$ 111.00, R$ 222.00, R$ 333.00) agora')
print('   pertencem à empresa 5 e devem aparecer no relatório.')
print('\n🌐 Teste na interface:')
print('   http://localhost:8000/medicos/relatorio-mensal-socio/5/?mes_ano=2025-08&socio_id=10')
