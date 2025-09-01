#!/usr/bin/env python
"""
Script para diagnosticar e corrigir vinculação de DespesaSocio com empresa incorreta.
Problema: DespesaSocio pode estar vinculada a ItemDespesa cujo GrupoDespesa pertence a outra empresa.

Uso: python fix_despesas_socio.py --empresa 5 --socio 10 --mes_ano 2025-08
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio, ItemDespesa, GrupoDespesa
from medicos.models.base import Socio, Empresa
from django.db import transaction

def diagnosticar_despesas(empresa_id, socio_id, mes_ano):
    print(f"=== DIAGNÓSTICO DESPESAS SÓCIO ===")
    print(f"Empresa: {empresa_id}, Sócio: {socio_id}, Competência: {mes_ano}")
    
    ano, mes = mes_ano.split('-')
    ano, mes = int(ano), int(mes)
    
    # 1. Buscar todas as DespesaSocio do sócio na competência
    despesas_socio = DespesaSocio.objects.filter(
        socio_id=socio_id,
        data__year=ano,
        data__month=mes
    ).select_related('item_despesa__grupo_despesa__empresa', 'socio')
    
    print(f"\nTotal DespesaSocio encontradas: {despesas_socio.count()}")
    
    for despesa in despesas_socio:
        grupo_empresa_id = despesa.item_despesa.grupo_despesa.empresa_id
        print(f"ID {despesa.id}: valor={despesa.valor}, "
              f"item={despesa.item_despesa.descricao}, "
              f"grupo={despesa.item_despesa.grupo_despesa.descricao}, "
              f"empresa_do_grupo={grupo_empresa_id}")
        
        if grupo_empresa_id != empresa_id:
            print(f"  ⚠️  PROBLEMA: DespesaSocio {despesa.id} vinculada a grupo da empresa {grupo_empresa_id}, esperado {empresa_id}")
    
    # 2. Verificar builder - filtro correto
    despesas_corretas = DespesaSocio.objects.filter(
        socio_id=socio_id,
        data__year=ano,
        data__month=mes,
        item_despesa__grupo_despesa__empresa_id=empresa_id
    )
    
    print(f"\nDespesas com filtro correto (empresa {empresa_id}): {despesas_corretas.count()}")
    for despesa in despesas_corretas:
        print(f"  ✅ ID {despesa.id}: {despesa.valor}")

def corrigir_despesas(empresa_id, socio_id, mes_ano, dry_run=True):
    print(f"\n=== CORREÇÃO DESPESAS SÓCIO ===")
    print(f"Dry run: {dry_run}")
    
    ano, mes = mes_ano.split('-')
    ano, mes = int(ano), int(mes)
    
    empresa = Empresa.objects.get(id=empresa_id)
    
    despesas_problematicas = DespesaSocio.objects.filter(
        socio_id=socio_id,
        data__year=ano,
        data__month=mes
    ).exclude(
        item_despesa__grupo_despesa__empresa_id=empresa_id
    ).select_related('item_despesa__grupo_despesa')
    
    print(f"Despesas a corrigir: {despesas_problematicas.count()}")
    
    for despesa in despesas_problematicas:
        item_original = despesa.item_despesa
        grupo_original = item_original.grupo_despesa
        
        print(f"\nCorrigindo DespesaSocio ID {despesa.id}:")
        print(f"  Item original: {item_original.descricao}")
        print(f"  Grupo original: {grupo_original.descricao} (empresa {grupo_original.empresa_id})")
        
        if not dry_run:
            with transaction.atomic():
                # Buscar ou criar grupo equivalente na empresa correta
                grupo_correto, created = GrupoDespesa.objects.get_or_create(
                    empresa_id=empresa_id,
                    codigo=grupo_original.codigo,
                    defaults={
                        'descricao': grupo_original.descricao,
                        'tipo_rateio': grupo_original.tipo_rateio,
                        'ativo': grupo_original.ativo,
                    }
                )
                
                if created:
                    print(f"  ✅ Criado novo GrupoDespesa: {grupo_correto.descricao}")
                else:
                    print(f"  ✅ Usando GrupoDespesa existente: {grupo_correto.descricao}")
                
                # Buscar ou criar item equivalente no grupo correto
                item_correto, created = ItemDespesa.objects.get_or_create(
                    grupo_despesa=grupo_correto,
                    codigo=item_original.codigo,
                    defaults={
                        'descricao': item_original.descricao,
                        'ativo': item_original.ativo,
                    }
                )
                
                if created:
                    print(f"  ✅ Criado novo ItemDespesa: {item_correto.descricao}")
                else:
                    print(f"  ✅ Usando ItemDespesa existente: {item_correto.descricao}")
                
                # Atualizar FK da despesa
                despesa.item_despesa = item_correto
                despesa.save()
                
                print(f"  ✅ DespesaSocio {despesa.id} atualizada para item {item_correto.id}")
        else:
            print(f"  [DRY RUN] Criaria/buscaria grupo e item na empresa {empresa_id}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--empresa', required=True, type=int, help='ID da empresa')
    parser.add_argument('--socio', required=True, type=int, help='ID do sócio')
    parser.add_argument('--mes_ano', required=True, help='Competência YYYY-MM')
    parser.add_argument('--fix', action='store_true', help='Aplicar correções (sem --fix = dry run)')
    
    args = parser.parse_args()
    
    diagnosticar_despesas(args.empresa, args.socio, args.mes_ano)
    
    if args.fix:
        corrigir_despesas(args.empresa, args.socio, args.mes_ano, dry_run=False)
    else:
        print("\n=== SIMULAÇÃO (adicione --fix para aplicar) ===")
        corrigir_despesas(args.empresa, args.socio, args.mes_ano, dry_run=True)
    
    print(f"\n=== VERIFICAÇÃO FINAL ===")
    diagnosticar_despesas(args.empresa, args.socio, args.mes_ano)
