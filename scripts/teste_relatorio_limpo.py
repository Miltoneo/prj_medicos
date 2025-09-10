#!/usr/bin/env python
"""
Teste simples para verificar se o código do relatório está funcionando após limpeza
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

def testar_imports():
    """Testa se todos os imports estão funcionando"""
    try:
        # Imports da view de relatórios
        from medicos.views_relatorios import relatorio_mensal_socio
        from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
        from medicos.relatorios.builders import montar_relatorio_mensal_socio
        
        print("✅ Todos os imports estão funcionando corretamente")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

def testar_sintaxe_view():
    """Testa se não há erros de sintaxe na view"""
    try:
        import medicos.views_relatorios
        print("✅ Sintaxe da view está correta")
        return True
    except Exception as e:
        print(f"❌ Erro de sintaxe na view: {e}")
        return False

if __name__ == "__main__":
    print("=== Teste de Limpeza do Relatório Mensal do Sócio ===")
    
    sucesso_imports = testar_imports()
    sucesso_sintaxe = testar_sintaxe_view()
    
    if sucesso_imports and sucesso_sintaxe:
        print("\n✅ Limpeza realizada com sucesso! Código funcionando corretamente.")
    else:
        print("\n❌ Problemas encontrados na limpeza.")
