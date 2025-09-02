#!/usr/bin/env python
"""Migração direta das despesas IDs 61, 62, 63 para empresa 5."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio, ItemDespesa, GrupoDespesa
from medicos.models.base import Empresa
from django.db import transaction

def migrar_despesas_direto():
    print("=== MIGRAÇÃO DIRETA ===")
    
    empresa_5 = Empresa.objects.get(id=5)
    despesas_ids = [61, 62, 63]
    
    for despesa_id in despesas_ids:
        try:
            despesa = DespesaSocio.objects.get(id=despesa_id)
            item_original = despesa.item_despesa
            grupo_original = item_original.grupo_despesa
            
            print(f"\nMigrando despesa ID {despesa_id}:")
            print(f"  Valor: R$ {despesa.valor:.2f}")
            print(f"  Item atual: {item_original.descricao}")
            print(f"  Grupo atual: {grupo_original.descricao} (empresa {grupo_original.empresa_id})")
            
            with transaction.atomic():
                # Buscar ou criar grupo na empresa 5
                grupo_correto, created = GrupoDespesa.objects.get_or_create(
                    empresa_id=5,
                    codigo=grupo_original.codigo,
                    defaults={
                        'descricao': grupo_original.descricao,
                        'tipo_rateio': grupo_original.tipo_rateio,
                    }
                )
                
                if created:
                    print(f"  ✅ Criado grupo: {grupo_correto.descricao}")
                else:
                    print(f"  ✅ Usando grupo existente: {grupo_correto.descricao}")
                
                # Buscar ou criar item no grupo correto
                item_correto, created = ItemDespesa.objects.get_or_create(
                    grupo_despesa=grupo_correto,
                    codigo=item_original.codigo,
                    defaults={
                        'descricao': item_original.descricao,
                    }
                )
                
                if created:
                    print(f"  ✅ Criado item: {item_correto.descricao}")
                else:
                    print(f"  ✅ Usando item existente: {item_correto.descricao}")
                
                # Atualizar FK da despesa
                despesa.item_despesa = item_correto
                despesa.save()
                
                print(f"  ✅ Despesa {despesa_id} migrada para empresa 5")
                
        except Exception as e:
            print(f"  ❌ Erro ao migrar despesa {despesa_id}: {e}")

if __name__ == '__main__':
    migrar_despesas_direto()
    
    print("\n=== VERIFICAÇÃO PÓS-MIGRAÇÃO ===")
    despesas = DespesaSocio.objects.filter(id__in=[61, 62, 63]).select_related('item_despesa__grupo_despesa__empresa')
    for despesa in despesas:
        empresa_grupo = despesa.item_despesa.grupo_despesa.empresa_id
        print(f"ID {despesa.id}: empresa_grupo={empresa_grupo}")
