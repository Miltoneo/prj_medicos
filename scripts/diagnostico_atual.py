#!/usr/bin/env python
"""Diagnóstico atual das despesas de sócio para 2025-08."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio
from medicos.relatorios.builders import montar_relatorio_mensal_socio
import json

def main():
    with open('diagnostico_atual.txt', 'w', encoding='utf-8') as f:
        f.write("=== DIAGNÓSTICO ATUAL 2025-08 ===\n\n")
        
        # 1. Todas as despesas do sócio 10 em 2025-08
        f.write("1. TODAS AS DESPESAS SÓCIO 10 em 2025-08:\n")
        despesas_todas = DespesaSocio.objects.filter(
            socio_id=10,
            data__year=2025,
            data__month=8
        ).select_related('item_despesa__grupo_despesa__empresa').order_by('data')
        
        f.write(f"Total encontradas: {despesas_todas.count()}\n")
        for despesa in despesas_todas:
            empresa_grupo = despesa.item_despesa.grupo_despesa.empresa_id
            f.write(f"  ID {despesa.id}: {despesa.data.strftime('%d/%m/%Y')} - "
                   f"R$ {despesa.valor:.2f} - {despesa.item_despesa.descricao} - "
                   f"empresa_grupo={empresa_grupo}\n")
        
        # 2. Despesas com filtro do builder (empresa=5)
        f.write(f"\n2. DESPESAS COM FILTRO EMPRESA=5:\n")
        despesas_empresa5 = DespesaSocio.objects.filter(
            socio_id=10,
            data__year=2025,
            data__month=8,
            item_despesa__grupo_despesa__empresa_id=5
        ).select_related('item_despesa__grupo_despesa').order_by('data')
        
        f.write(f"Total com empresa=5: {despesas_empresa5.count()}\n")
        for despesa in despesas_empresa5:
            f.write(f"  ID {despesa.id}: {despesa.data.strftime('%d/%m/%Y')} - "
                   f"R$ {despesa.valor:.2f} - {despesa.item_despesa.descricao}\n")
        
        # 3. Teste do builder
        f.write(f"\n3. TESTE BUILDER:\n")
        try:
            resultado = montar_relatorio_mensal_socio(empresa_id=5, mes_ano='2025-08', socio_id=10)
            lista_despesas = resultado.get('lista_despesas_sem_rateio', [])
            f.write(f"Builder retornou: {len(lista_despesas)} despesas\n")
            for desp in lista_despesas:
                f.write(f"  ID {desp.get('id')}: {desp.get('data')} - "
                       f"R$ {desp.get('valor_total', 0):.2f} - {desp.get('descricao')}\n")
        except Exception as e:
            f.write(f"Erro no builder: {e}\n")
        
        # 4. Identificar despesas problemáticas
        f.write(f"\n4. DESPESAS PROBLEMÁTICAS (empresa != 5):\n")
        despesas_problema = despesas_todas.exclude(item_despesa__grupo_despesa__empresa_id=5)
        f.write(f"Total problemáticas: {despesas_problema.count()}\n")
        
        for despesa in despesas_problema:
            empresa_atual = despesa.item_despesa.grupo_despesa.empresa_id
            f.write(f"  ID {despesa.id}: empresa_grupo={empresa_atual} (deveria ser 5)\n")
            f.write(f"    Data: {despesa.data.strftime('%d/%m/%Y')}\n")
            f.write(f"    Valor: R$ {despesa.valor:.2f}\n")
            f.write(f"    Item: {despesa.item_despesa.descricao}\n")
            f.write(f"    Grupo: {despesa.item_despesa.grupo_despesa.descricao}\n\n")
    
    print("Diagnóstico salvo em 'diagnostico_atual.txt'")

if __name__ == '__main__':
    main()
