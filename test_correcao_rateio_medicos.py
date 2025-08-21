#!/usr/bin/env python
"""
Teste da Correção - Rateio de Impostos para Médicos
Validar que o rateio usa valores da NF original, não recalcula

Execução: python test_correcao_rateio_medicos.py
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
from medicos.models.fiscal import NotaFiscalRateioMedico
from medicos.models.base import Socio

def testar_correcao_rateio():
    """
    Testar se o rateio agora usa valores da NF original
    """
    print("=" * 80)
    print("TESTE - Correção do Rateio de Impostos para Médicos")
    print("=" * 80)
    
    try:
        # 1. Buscar uma nota fiscal existente para teste
        empresa = Empresa.objects.get(id=4)
        print(f"✓ Empresa: {empresa.nome}")
        
        # Buscar uma nota fiscal com valores de impostos
        nota_fiscal = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            val_bruto__gt=0,
            val_ISS__gt=0
        ).first()
        
        if not nota_fiscal:
            print("❌ ERRO: Nenhuma nota fiscal com impostos encontrada para teste")
            return False
        
        print(f"✓ Nota Fiscal: {nota_fiscal.numero}")
        print(f"   Valor Bruto: R$ {nota_fiscal.val_bruto:,.2f}")
        print(f"   ISS Original: R$ {nota_fiscal.val_ISS:,.2f}")
        print(f"   PIS Original: R$ {nota_fiscal.val_PIS:,.2f}")
        print(f"   COFINS Original: R$ {nota_fiscal.val_COFINS:,.2f}")
        print(f"   IR Original: R$ {nota_fiscal.val_IR:,.2f}")
        print(f"   CSLL Original: R$ {nota_fiscal.val_CSLL:,.2f}")
        
        # 2. Buscar um médico (sócio) para o rateio
        medico = Socio.objects.filter(empresa=empresa).first()
        if not medico:
            print("❌ ERRO: Nenhum médico/sócio encontrado para teste")
            return False
        
        print(f"✓ Médico: {medico.pessoa.name}")
        
        # 3. Limpar rateios de teste anteriores
        NotaFiscalRateioMedico.objects.filter(
            nota_fiscal=nota_fiscal,
            tipo_rateio='TESTE_CORRECAO'
        ).delete()
        
        # 4. Criar rateio de teste com 50% da nota
        percentual_teste = Decimal('50.00')  # 50%
        valor_bruto_rateado = nota_fiscal.val_bruto * (percentual_teste / Decimal('100'))
        
        print(f"\n📊 CRIANDO RATEIO DE TESTE:")
        print(f"   Percentual: {percentual_teste}%")
        print(f"   Valor Bruto Rateado: R$ {valor_bruto_rateado:,.2f}")
        
        # Criar o rateio
        rateio = NotaFiscalRateioMedico.objects.create(
            nota_fiscal=nota_fiscal,
            medico=medico,
            percentual_participacao=percentual_teste,
            valor_bruto_medico=valor_bruto_rateado,
            tipo_rateio='TESTE_CORRECAO'
        )
        
        print(f"✓ Rateio criado com sucesso")
        
        # 5. Verificar se os valores calculados estão corretos
        print(f"\n🔍 VALIDAÇÃO DOS CÁLCULOS:")
        
        # Calcular valores esperados (50% dos valores originais)
        iss_esperado = nota_fiscal.val_ISS * (percentual_teste / Decimal('100'))
        pis_esperado = nota_fiscal.val_PIS * (percentual_teste / Decimal('100'))
        cofins_esperado = nota_fiscal.val_COFINS * (percentual_teste / Decimal('100'))
        ir_esperado = nota_fiscal.val_IR * (percentual_teste / Decimal('100'))
        csll_esperado = nota_fiscal.val_CSLL * (percentual_teste / Decimal('100'))
        
        total_impostos_esperado = (
            iss_esperado + pis_esperado + cofins_esperado + 
            ir_esperado + csll_esperado
        )
        liquido_esperado = valor_bruto_rateado - total_impostos_esperado
        
        print(f"   VALORES ESPERADOS (50% dos originais):")
        print(f"   ISS: R$ {iss_esperado:,.2f}")
        print(f"   PIS: R$ {pis_esperado:,.2f}")
        print(f"   COFINS: R$ {cofins_esperado:,.2f}")
        print(f"   IR: R$ {ir_esperado:,.2f}")
        print(f"   CSLL: R$ {csll_esperado:,.2f}")
        print(f"   Líquido: R$ {liquido_esperado:,.2f}")
        
        print(f"\n   VALORES CALCULADOS PELO RATEIO:")
        print(f"   ISS: R$ {rateio.valor_iss_medico:,.2f}")
        print(f"   PIS: R$ {rateio.valor_pis_medico:,.2f}")
        print(f"   COFINS: R$ {rateio.valor_cofins_medico:,.2f}")
        print(f"   IR: R$ {rateio.valor_ir_medico:,.2f}")
        print(f"   CSLL: R$ {rateio.valor_csll_medico:,.2f}")
        print(f"   Líquido: R$ {rateio.valor_liquido_medico:,.2f}")
        
        # 6. Comparar valores (tolerância de 1 centavo)
        tolerancia = Decimal('0.01')
        erros = []
        
        if abs(rateio.valor_iss_medico - iss_esperado) > tolerancia:
            erros.append(f"ISS: Esperado R$ {iss_esperado:,.2f}, Obtido R$ {rateio.valor_iss_medico:,.2f}")
        
        if abs(rateio.valor_pis_medico - pis_esperado) > tolerancia:
            erros.append(f"PIS: Esperado R$ {pis_esperado:,.2f}, Obtido R$ {rateio.valor_pis_medico:,.2f}")
        
        if abs(rateio.valor_cofins_medico - cofins_esperado) > tolerancia:
            erros.append(f"COFINS: Esperado R$ {cofins_esperado:,.2f}, Obtido R$ {rateio.valor_cofins_medico:,.2f}")
        
        if abs(rateio.valor_ir_medico - ir_esperado) > tolerancia:
            erros.append(f"IR: Esperado R$ {ir_esperado:,.2f}, Obtido R$ {rateio.valor_ir_medico:,.2f}")
        
        if abs(rateio.valor_csll_medico - csll_esperado) > tolerancia:
            erros.append(f"CSLL: Esperado R$ {csll_esperado:,.2f}, Obtido R$ {rateio.valor_csll_medico:,.2f}")
        
        if abs(rateio.valor_liquido_medico - liquido_esperado) > tolerancia:
            erros.append(f"Líquido: Esperado R$ {liquido_esperado:,.2f}, Obtido R$ {rateio.valor_liquido_medico:,.2f}")
        
        # 7. Resultado final
        if erros:
            print(f"\n❌ TESTE REPROVADO - Erros encontrados:")
            for erro in erros:
                print(f"   • {erro}")
            return False
        else:
            print(f"\n✅ TESTE APROVADO:")
            print(f"   ✓ Todos os impostos foram rateados corretamente")
            print(f"   ✓ Valores baseados na NF original, não recalculados")
            print(f"   ✓ Proporção respeitada (50% dos valores originais)")
            print(f"   ✓ Correção funcionando conforme esperado")
            return True
        
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Limpeza: remover rateio de teste
        try:
            NotaFiscalRateioMedico.objects.filter(
                tipo_rateio='TESTE_CORRECAO'
            ).delete()
            print(f"\n🗑️  Rateio de teste removido")
        except:
            pass

if __name__ == '__main__':
    print("Iniciando teste da correção...")
    sucesso = testar_correcao_rateio()
    
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 CORREÇÃO VALIDADA!")
        print("✅ Rateio agora usa valores da NF original")
        print("✅ Não recalcula impostos incorretamente")
        print("✅ Problema do ISS = R$ 0,00 solucionado")
    else:
        print("💥 CORREÇÃO FALHOU!")
        print("❌ Verificar implementação")
    print("=" * 80)
