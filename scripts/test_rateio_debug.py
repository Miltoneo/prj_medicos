#!/usr/bin/env python
"""
Teste das propriedades de rateio das notas fiscais
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal, NotaFiscalRateioMedico

def test_rateio():
    print("=== TESTE PROPRIEDADES RATEIO ===")
    
    # Buscar notas fiscais
    notas = NotaFiscal.objects.prefetch_related('rateios_medicos')[:5]
    
    for nota in notas:
        print(f"\nNota {nota.pk} - Número: {nota.numero}")
        print(f"  tem_rateio: {nota.tem_rateio}")
        print(f"  rateio_completo: {nota.rateio_completo}")
        print(f"  percentual_total_rateado: {nota.percentual_total_rateado}")
        print(f"  count rateios: {nota.rateios_medicos.count()}")
        
        # Listar rateios se existirem
        if nota.tem_rateio:
            print("  Rateios:")
            for rateio in nota.rateios_medicos.all():
                print(f"    - {rateio.percentual_participacao}%")
    
    print("\n=== CRIANDO RATEIO INCOMPLETO PARA TESTE ===")
    
    # Buscar primeira nota sem rateio
    nota_teste = NotaFiscal.objects.filter(rateios_medicos__isnull=True).first()
    
    if nota_teste:
        print(f"Usando nota {nota_teste.numero} para teste")
        
        # Criar rateio incompleto (50%)
        try:
            rateio = NotaFiscalRateioMedico(
                nota_fiscal=nota_teste,
                percentual_participacao=50.0,
                valor_bruto_medico=100.0  # Valor de teste
            )
            rateio.save()
            print(f"Rateio criado com 50%")
            
            # Testar propriedades
            print(f"Após criar rateio:")
            print(f"  tem_rateio: {nota_teste.tem_rateio}")
            print(f"  rateio_completo: {nota_teste.rateio_completo}")
            print(f"  percentual_total_rateado: {nota_teste.percentual_total_rateado}")
            
        except Exception as e:
            print(f"Erro ao criar rateio: {e}")
    else:
        print("Nenhuma nota sem rateio encontrada")

if __name__ == "__main__":
    test_rateio()
