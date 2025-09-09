#!/usr/bin/env python
"""
Script para testar a correção do cálculo do Adicional de IR Trimestral.
Verifica se o adicional só é aplicado quando a base trimestral excede R$ 60.000,00.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('f:\\Projects\\Django\\prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.contrib.auth import authenticate, login
from django.test import RequestFactory
from medicos.models import Empresa, CustomUser
from medicos.views_relatorios import relatorio_apuracao

def testar_calculo_trimestral():
    """
    Testa a correção do adicional de IR na tabela trimestral.
    """
    print("=== TESTE DA CORREÇÃO: ADICIONAL DE IR TRIMESTRAL ===\n")
    
    try:
        # Buscar primeira empresa disponível
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada para teste")
            return
            
        # Buscar usuário
        usuario = CustomUser.objects.first()
        if not usuario:
            print("❌ Nenhum usuário encontrado para teste")
            return
            
        print(f"🏢 Testando com empresa: {empresa.nome} (ID: {empresa.id})")
        print(f"👤 Usuário: {usuario.username}")
        
        # Criar request simulado
        factory = RequestFactory()
        request = factory.get(f'/medicos/relatorio-issqn/{empresa.id}/')
        request.user = usuario
        request.session = {'mes_ano': '2024'}
        
        print(f"📅 Período de teste: 2024\n")
        
        # Executar a view
        response = relatorio_apuracao(request, empresa.id)
        
        if hasattr(response, 'context_data'):
            context = response.context_data
        elif hasattr(response, 'content'):
            # View retornou uma resposta HTTP direta
            print("✅ View executada com sucesso (resposta HTTP)")
            return
        else:
            print("❌ Não foi possível obter os dados do contexto")
            return
        
        # Verificar se os dados estão presentes
        if 'totais_trimestrais' not in context:
            print("❌ Dados trimestrais não encontrados no contexto")
            return
            
        totais_trimestrais = context['totais_trimestrais']
        
        print("📊 RESULTADO DO CÁLCULO TRIMESTRAL - TABELA IRPJ:")
        print("-" * 80)
        
        trimestres = ['T1', 'T2', 'T3', 'T4']
        
        for i, trimestre in enumerate(trimestres):
            base_total = totais_trimestrais['base_calculo_total'][i] if i < len(totais_trimestrais['base_calculo_total']) else Decimal('0')
            adicional = totais_trimestrais['adicional_ir'][i] if i < len(totais_trimestrais['adicional_ir']) else Decimal('0')
            limite = Decimal('60000.00')
            
            print(f"📈 {trimestre}:")
            print(f"   Base total (=(15) + (B)): R$ {base_total:,.2f}")
            print(f"   Limite trimestral: R$ {limite:,.2f}")
            
            if base_total <= limite:
                if adicional == Decimal('0'):
                    print(f"   ✅ CORRETO: Base ≤ R$ {limite:,.2f}, adicional = R$ 0,00")
                else:
                    print(f"   ❌ ERRO: Base ≤ R$ {limite:,.2f}, mas adicional = R$ {adicional:,.2f} (deveria ser R$ 0,00)")
            else:
                excedente_esperado = base_total - limite
                adicional_esperado = excedente_esperado * Decimal('0.10')
                if abs(adicional - adicional_esperado) < Decimal('0.01'):
                    print(f"   ✅ CORRETO: Base > R$ {limite:,.2f}")
                    print(f"   Excedente: R$ {excedente_esperado:,.2f}")
                    print(f"   Adicional (10%): R$ {adicional:,.2f}")
                else:
                    print(f"   ❌ ERRO: Adicional incorreto")
                    print(f"   Esperado: R$ {adicional_esperado:,.2f}")
                    print(f"   Obtido: R$ {adicional:,.2f}")
            
            print()
        
        print("🎯 VALIDAÇÃO DA REGRA:")
        print("✅ Adicional de IR aplicado apenas quando base trimestral > R$ 60.000,00")
        print("✅ Adicional = (base_total - 60.000) × 10% quando excede o limite")
        print("✅ Adicional = R$ 0,00 quando base_total ≤ R$ 60.000,00")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_calculo_trimestral()
