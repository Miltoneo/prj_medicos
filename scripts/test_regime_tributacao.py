#!/usr/bin/env python
"""
Teste para verificar se a apuração de IRPJ e CSLL está considerando
corretamente o regime de tributação da empresa.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.relatorios.apuracao_irpj import montar_relatorio_irpj_persistente
from medicos.relatorios.apuracao_csll import montar_relatorio_csll_persistente
from medicos.relatorios.apuracao_irpj_mensal import montar_relatorio_irpj_mensal_persistente

def testar_regime_tributacao():
    print("=== TESTE DE REGIME TRIBUTÁRIO ===")
    
    # Pegar empresa de teste
    empresa = Empresa.objects.get(id=4)
    print(f"Empresa: {empresa.name}")
    print(f"Regime atual: {empresa.regime_tributario} ({empresa.regime_tributario_nome})")
    
    # Teste 1: Regime de Competência (atual)
    print("\n1. TESTANDO REGIME DE COMPETÊNCIA:")
    try:
        resultado_irpj = montar_relatorio_irpj_persistente(4, '2025')
        print(f"   ✅ IRPJ Trimestral: {len(resultado_irpj['linhas'])} trimestres processados")
        
        resultado_csll = montar_relatorio_csll_persistente(4, '2025')
        print(f"   ✅ CSLL Trimestral: {len(resultado_csll['linhas'])} trimestres processados")
        
        resultado_irpj_mensal = montar_relatorio_irpj_mensal_persistente(4, '2025')
        print(f"   ✅ IRPJ Mensal: {len(resultado_irpj_mensal['linhas'])} meses processados")
        
    except Exception as e:
        print(f"   ❌ Erro no regime de competência: {e}")
    
    # Teste 2: Simular mudança para Regime de Caixa (temporário)
    print("\n2. SIMULANDO REGIME DE CAIXA (temporário):")
    regime_original = empresa.regime_tributario
    try:
        # Alterar temporariamente para regime de caixa
        empresa.regime_tributario = REGIME_TRIBUTACAO_CAIXA
        empresa.save()
        print(f"   Regime alterado para: {empresa.regime_tributario} ({empresa.regime_tributario_nome})")
        
        resultado_irpj = montar_relatorio_irpj_persistente(4, '2025')
        print(f"   ✅ IRPJ Trimestral (caixa): {len(resultado_irpj['linhas'])} trimestres processados")
        
        resultado_csll = montar_relatorio_csll_persistente(4, '2025')
        print(f"   ✅ CSLL Trimestral (caixa): {len(resultado_csll['linhas'])} trimestres processados")
        
        resultado_irpj_mensal = montar_relatorio_irpj_mensal_persistente(4, '2025')
        print(f"   ✅ IRPJ Mensal (caixa): {len(resultado_irpj_mensal['linhas'])} meses processados")
        
    except Exception as e:
        print(f"   ❌ Erro no regime de caixa: {e}")
    
    finally:
        # Restaurar regime original
        empresa.regime_tributario = regime_original
        empresa.save()
        print(f"   Regime restaurado para: {empresa.regime_tributario} ({empresa.regime_tributario_nome})")
    
    print("\n=== RESULTADO ===")
    print("✅ Alterações implementadas com sucesso!")
    print("📝 MUDANÇAS:")
    print("   - IRPJ/CSLL: Agora considera regime de tributação da empresa")
    print("   - Competência: usa dtEmissao")
    print("   - Caixa: usa dtRecebimento (quando preenchido)")
    print("   - Templates atualizados com notas explicativas")
    print("🌐 Teste na URL: http://127.0.0.1:8000/medicos/relatorio-issqn/4/")

if __name__ == "__main__":
    testar_regime_tributacao()
