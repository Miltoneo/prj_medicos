#!/usr/bin/env python
"""
Script para debugar o status de rateio das notas fiscais
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal

def debug_rateio():
    print("=== DEBUG RATEIO NOTAS FISCAIS ===")
    
    # Buscar algumas notas fiscais
    notas = NotaFiscal.objects.all()[:10]
    
    print(f"Total de notas encontradas: {notas.count()}")
    print("-" * 80)
    
    for nota in notas:
        print(f"Nota {nota.pk} - Número: {nota.numero}")
        print(f"  tem_rateio: {nota.tem_rateio}")
        print(f"  rateio_completo: {nota.rateio_completo}")
        print(f"  percentual_total_rateado: {nota.percentual_total_rateado}")
        print(f"  total_medicos_rateio: {nota.total_medicos_rateio}")
        print("-" * 40)
    
    # Buscar especificamente notas com rateio
    notas_com_rateio = NotaFiscal.objects.filter(rateios_medicos__isnull=False).distinct()
    print(f"\nNotas com rateio: {notas_com_rateio.count()}")
    
    for nota in notas_com_rateio[:5]:
        print(f"Nota {nota.pk} - {nota.numero}: {nota.percentual_total_rateado}% rateado")

if __name__ == "__main__":
    debug_rateio()
