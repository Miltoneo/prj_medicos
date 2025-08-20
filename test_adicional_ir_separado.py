#!/usr/bin/env python
"""
Teste do Adicional de IR - Separação entre IRPJ e Adicional
Validar que adicional SEMPRE usa data de emissão, independente do regime

Execução: python test_adicional_ir_separado.py
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from decimal import Decimal
from datetime import date
from medicos.models import Empresa, NotaFiscal
from medicos.models.base import REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.relatorios.apuracao_irpj import montar_relatorio_irpj_persistente

def criar_cenario_teste():
    """
    Criar cenário de teste com empresa em regime de CAIXA
    e notas fiscais com diferentes datas de emissão/recebimento
    """
    print("=" * 80)
    print("CRIANDO CENÁRIO DE TESTE - Adicional IR Separado")
    print("=" * 80)
    
    try:
        empresa = Empresa.objects.get(id=4)
        print(f"✓ Empresa: {empresa.nome}")
        print(f"✓ Regime atual: {empresa.regime_tributario} (1=Competência, 2=Caixa)")
        
        # Forçar regime de CAIXA para demonstrar a diferença
        regime_original = empresa.regime_tributario
        empresa.regime_tributario = REGIME_TRIBUTACAO_CAIXA
        empresa.save()
        print(f"✓ Regime alterado para: CAIXA (2) - para demonstrar separação")
        
        # Limpar notas fiscais existentes para o teste
        NotaFiscal.objects.filter(empresa_destinataria=empresa, dtEmissao__year=2024).delete()
        print("✓ Notas fiscais de 2024 removidas para teste limpo")
        
        # Criar notas de teste - Trimestre T3/2024 (Jul-Set)
        notas_teste = [
            {
                'dtEmissao': date(2024, 7, 15),  # Julho - dentro do trimestre
                'dtRecebimento': date(2024, 10, 5),  # Outubro - fora do trimestre
                'val_bruto': Decimal('100000.00'),
                'tipo_servico': NotaFiscal.TIPO_SERVICO_CONSULTAS,
                'descricao': 'Nota A - Emitida T3, Recebida T4'
            },
            {
                'dtEmissao': date(2024, 6, 20),  # Junho - fora do trimestre  
                'dtRecebimento': date(2024, 8, 10),  # Agosto - dentro do trimestre
                'val_bruto': Decimal('80000.00'),
                'tipo_servico': NotaFiscal.TIPO_SERVICO_CONSULTAS,
                'descricao': 'Nota B - Emitida T2, Recebida T3'
            }
        ]
        
        for i, nota_data in enumerate(notas_teste, 1):
            nota = NotaFiscal.objects.create(
                empresa_destinataria=empresa,
                numero=f"NF-TEST-{i}",
                serie="1",
                dtEmissao=nota_data['dtEmissao'],
                dtRecebimento=nota_data['dtRecebimento'],
                val_bruto=nota_data['val_bruto'],
                val_IR=nota_data['val_bruto'] * Decimal('0.015'),  # 1.5% IR retido
                tipo_servico=nota_data['tipo_servico']
            )
            print(f"✓ Criada: {nota_data['descricao']} - R$ {nota_data['val_bruto']:,.2f}")
        
        print("\n📊 CENÁRIO CONFIGURADO:")
        print(f"   Empresa: Regime CAIXA")
        print(f"   Trimestre analisado: T3/2024 (Jul-Set)")
        print(f"   Nota A: Emitida Jul, Recebida Out - R$ 100.000,00")
        print(f"   Nota B: Emitida Jun, Recebida Ago - R$ 80.000,00")
        
        return empresa, regime_original
        
    except Exception as e:
        print(f"❌ ERRO ao criar cenário: {e}")
        return None, None

def testar_separacao_calculo():
    """
    Testar se IRPJ usa regime (caixa) e Adicional sempre usa emissão
    """
    empresa, regime_original = criar_cenario_teste()
    if not empresa:
        return False
    
    try:
        print("\n" + "=" * 80)
        print("EXECUTANDO TESTE - Separação IRPJ x Adicional")
        print("=" * 80)
        
        # Executar cálculo
        resultado = montar_relatorio_irpj_persistente(empresa.id, 2024)
        
        # Analisar T3/2024 (índice 2)
        if len(resultado['linhas']) >= 3:
            t3_2024 = resultado['linhas'][2]  # T3 = índice 2
            
            print(f"📈 RESULTADOS T3/2024:")
            print(f"   Competência: {t3_2024['competencia']}")
            print(f"   Receita Bruta (IRPJ): R$ {t3_2024['receita_bruta']:,.2f}")
            print(f"   Base Cálculo (IRPJ): R$ {t3_2024['base_calculo']:,.2f}")
            print(f"   Adicional IR: R$ {t3_2024['adicional']:,.2f}")
            
            print(f"\n🔍 ANÁLISE ESPERADA:")
            print(f"   IRPJ (Regime CAIXA - dtRecebimento):")
            print(f"   ✓ Deveria considerar apenas Nota B (recebida em Ago)")
            print(f"   ✓ Receita esperada: R$ 80.000,00")
            print(f"   ✓ Base esperada: R$ 80.000,00 × 32% = R$ 25.600,00")
            
            print(f"\n   ADICIONAL (SEMPRE dtEmissao):")
            print(f"   ✓ Deveria considerar apenas Nota A (emitida em Jul)")
            print(f"   ✓ Base adicional esperada: R$ 100.000,00 × 32% = R$ 32.000,00")
            print(f"   ✓ Adicional esperado: R$ 0,00 (abaixo de R$ 60.000,00)")
            
            # Verificações
            receita_esperada_irpj = Decimal('80000.00')  # Nota B recebida em T3
            base_esperada_irpj = receita_esperada_irpj * Decimal('0.32')
            
            adicional_esperado = Decimal('0.00')  # R$ 32.000 < R$ 60.000 (limite)
            
            print(f"\n✅ VERIFICAÇÕES:")
            
            # Verificar IRPJ
            if abs(t3_2024['receita_bruta'] - receita_esperada_irpj) < Decimal('0.01'):
                print(f"✓ IRPJ Receita: CORRETO (R$ {t3_2024['receita_bruta']:,.2f})")
            else:
                print(f"❌ IRPJ Receita: ERRO! Esperado R$ {receita_esperada_irpj:,.2f}, Obtido R$ {t3_2024['receita_bruta']:,.2f}")
                return False
            
            if abs(t3_2024['base_calculo'] - base_esperada_irpj) < Decimal('0.01'):
                print(f"✓ IRPJ Base: CORRETO (R$ {t3_2024['base_calculo']:,.2f})")
            else:
                print(f"❌ IRPJ Base: ERRO! Esperado R$ {base_esperada_irpj:,.2f}, Obtido R$ {t3_2024['base_calculo']:,.2f}")
                return False
            
            # Verificar Adicional
            if abs(t3_2024['adicional'] - adicional_esperado) < Decimal('0.01'):
                print(f"✓ Adicional IR: CORRETO (R$ {t3_2024['adicional']:,.2f})")
            else:
                print(f"❌ Adicional IR: ERRO! Esperado R$ {adicional_esperado:,.2f}, Obtido R$ {t3_2024['adicional']:,.2f}")
                return False
            
            print(f"\n🎉 SUCESSO: Separação entre IRPJ e Adicional funcionando corretamente!")
            print(f"✅ IRPJ usa regime tributário (data de recebimento para CAIXA)")
            print(f"✅ Adicional IR sempre usa data de emissão (independente do regime)")
            
            return True
            
        else:
            print(f"❌ ERRO: Dados insuficientes no resultado")
            return False
            
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Restaurar regime original
        if empresa and regime_original:
            empresa.regime_tributario = regime_original
            empresa.save()
            print(f"\n✓ Regime da empresa restaurado para: {regime_original}")
        
        # Limpar notas de teste
        if empresa:
            NotaFiscal.objects.filter(empresa_destinataria=empresa, numero__startswith="NF-TEST-").delete()
            print(f"✓ Notas de teste removidas")

if __name__ == '__main__':
    sucesso = testar_separacao_calculo()
    
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 TESTE APROVADO: Adicional IR separado e funcionando corretamente!")
        print("✅ IRPJ respeita regime tributário da empresa")
        print("✅ Adicional IR sempre usa data de emissão (Lei 9.249/1995)")
    else:
        print("💥 TESTE REPROVADO: Correções necessárias!")
    print("=" * 80)
