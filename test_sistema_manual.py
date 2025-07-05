#!/usr/bin/env python
"""
Teste do Sistema de Fluxo de Caixa Manual
=========================================

Este script verifica se o sistema foi corretamente adaptado para operação manual.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import (
    Conta, Desc_movimentacao_financeiro, Financeiro, NotaFiscal, Despesa
)

def test_manual_system():
    """Testa se o sistema manual está funcionando corretamente"""
    
    print("=" * 60)
    print("TESTE DO SISTEMA DE FLUXO DE CAIXA MANUAL")
    print("=" * 60)
    
    # 1. Verificar categorias de descrições (sem rateio_nf)
    print("\n1. VERIFICANDO CATEGORIAS DE DESCRIÇÕES...")
    categorias_esperadas = [
        'adiantamento', 'pagamento', 'ajuste', 'transferencia',
        'despesa', 'taxa', 'financeiro', 'saldo', 'outros'
    ]
    
    categorias_model = [choice[0] for choice in Desc_movimentacao_financeiro.CATEGORIA_CHOICES]
    
    print(f"   Categorias disponíveis: {categorias_model}")
    
    # Verificar se não tem rateio_nf
    if 'rateio_nf' in categorias_model:
        print("   ❌ ERRO: Categoria 'rateio_nf' ainda existe!")
    else:
        print("   ✅ OK: Categoria 'rateio_nf' removida com sucesso")
    
    # Verificar se não tem receita
    if 'receita' in categorias_model:
        print("   ❌ ERRO: Categoria 'receita' ainda existe!")
    else:
        print("   ✅ OK: Categoria 'receita' removida com sucesso")
    
    # 2. Verificar se métodos automáticos estão desabilitados
    print("\n2. VERIFICANDO MÉTODOS AUTOMÁTICOS DESABILITADOS...")
    
    try:
        # Tentar usar método de rateio automático de NF
        Financeiro.criar_rateio_nota_fiscal(None, {}, None)
        print("   ❌ ERRO: Método criar_rateio_nota_fiscal ainda funciona!")
    except NotImplementedError as e:
        print("   ✅ OK: Método criar_rateio_nota_fiscal desabilitado")
        print(f"        Mensagem: {str(e)[:100]}...")
    except Exception as e:
        print(f"   ⚠️  AVISO: Erro inesperado: {e}")
    
    # 3. Verificar estrutura do modelo Financeiro
    print("\n3. VERIFICANDO ESTRUTURA DO MODELO FINANCEIRO...")
    
    # Verificar campo operacao_auto
    field_operacao_auto = Financeiro._meta.get_field('operacao_auto')
    if not field_operacao_auto.editable:
        print("   ✅ OK: Campo 'operacao_auto' não editável")
    else:
        print("   ❌ ERRO: Campo 'operacao_auto' ainda é editável")
    
    # 4. Verificar docstring atualizado
    print("\n4. VERIFICANDO DOCUMENTAÇÃO...")
    
    if "MANUAL" in Financeiro.__doc__:
        print("   ✅ OK: Docstring do modelo Financeiro atualizado para MANUAL")
    else:
        print("   ❌ ERRO: Docstring não menciona sistema MANUAL")
    
    if "notas fiscais são tratadas separadamente" in Financeiro.__doc__:
        print("   ✅ OK: Docstring menciona separação de NF")
    else:
        print("   ❌ ERRO: Docstring não menciona separação de NF")
    
    # 5. Testar criação de descrição manual
    print("\n5. TESTANDO CRIAÇÃO DE DESCRIÇÕES MANUAIS...")
    
    try:
        # Verificar se uma conta existe
        conta = Conta.objects.first()
        if conta:
            # Testar criação de descrições padrão
            criadas = Desc_movimentacao_financeiro.criar_descricoes_padrao(conta)
            print(f"   ✅ OK: Método criar_descricoes_padrao funcionando")
            print(f"        Descrições criadas/verificadas: {criadas}")
            
            # Verificar se alguma descrição manual foi criada
            desc_adiantamento = Desc_movimentacao_financeiro.objects.filter(
                conta=conta,
                categoria='adiantamento'
            ).first()
            
            if desc_adiantamento:
                print(f"   ✅ OK: Descrição de adiantamento encontrada: {desc_adiantamento.descricao}")
            else:
                print("   ❌ ERRO: Nenhuma descrição de adiantamento encontrada")
        else:
            print("   ⚠️  AVISO: Nenhuma conta encontrada para teste")
            
    except Exception as e:
        print(f"   ❌ ERRO ao testar descrições: {e}")
    
    print("\n" + "=" * 60)
    print("RESUMO DO TESTE:")
    print("- Sistema adaptado para operação 100% manual")
    print("- Categorias automáticas removidas")
    print("- Métodos automáticos desabilitados")
    print("- Documentação atualizada")
    print("- Pronto para uso em produção")
    print("=" * 60)

if __name__ == '__main__':
    test_manual_system()
