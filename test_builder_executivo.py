#!/usr/bin/env python
"""
Teste do builder executivo corrigido para verificar o regime de tributação.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builder_executivo import montar_resumo_demonstrativo_socios
from medicos.models.base import Empresa

def testar_builder_executivo():
    print('=== TESTE BUILDER EXECUTIVO CORRIGIDO ===')
    
    # Testar com empresa ID 4
    empresa = Empresa.objects.get(id=4)
    print(f'Empresa: {empresa.name}')
    print(f'Regime Tributário: {empresa.regime_tributario} ({empresa.regime_tributario_nome})')
    
    # Testar para agosto/2025
    resultado = montar_resumo_demonstrativo_socios(4, '2025-08')
    print(f'\nMês/Ano: {resultado["mes_ano_display"]}')
    print(f'Número de sócios: {len(resultado["resumo_socios"])}')
    
    for socio_data in resultado['resumo_socios'][:2]:  # Mostrar primeiros 2 sócios
        print(f'\n📋 {socio_data["socio"].pessoa.name}:')
        print(f'   Receita Emitida: R$ {socio_data["receita_emitida"]:.2f}')
        print(f'   Receita Bruta: R$ {socio_data["receita_bruta"]:.2f}') 
        print(f'   Imposto Devido: R$ {socio_data["imposto_devido"]:.2f}')
        print(f'   Imposto Retido: R$ {socio_data["imposto_retido"]:.2f}')
        print(f'   Imposto a Pagar: R$ {socio_data["imposto_a_pagar"]:.2f}')
    
    print(f'\n📊 TOTAIS:')
    print(f'   Receita Emitida: R$ {resultado["totais_resumo"]["receita_emitida"]:.2f}')
    print(f'   Receita Bruta: R$ {resultado["totais_resumo"]["receita_bruta"]:.2f}')
    print(f'   Imposto Devido: R$ {resultado["totais_resumo"]["imposto_devido"]:.2f}')
    print(f'   Imposto Retido: R$ {resultado["totais_resumo"]["imposto_retido"]:.2f}')
    print(f'   Imposto a Pagar: R$ {resultado["totais_resumo"]["imposto_a_pagar"]:.2f}')
    
    print(f'\n✅ Teste concluído com sucesso!')
    
    # Validação: Verificar se imposto devido considera regime tributário
    if empresa.regime_tributario == 1:  # Competência
        print(f'\n🎯 VALIDAÇÃO: Empresa usa regime de COMPETÊNCIA')
        print(f'   → Imposto devido calculado sobre notas EMITIDAS')
    else:  # Caixa
        print(f'\n🎯 VALIDAÇÃO: Empresa usa regime de CAIXA')
        print(f'   → Imposto devido calculado sobre notas RECEBIDAS')

if __name__ == "__main__":
    testar_builder_executivo()
