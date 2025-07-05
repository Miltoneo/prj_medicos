#!/usr/bin/env python3
"""
Script de Teste e Validação do Sistema de Alíquotas
Sistema de Contabilidade para Associações Médicas
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
sys.path.append('.')
django.setup()

from medicos.models import Conta, Alicotas, NotaFiscal

def test_validacao_aliquotas():
    """Testa validações do modelo Alicotas"""
    print("=== TESTE: Validação de Alíquotas ===")
    
    try:
        # Buscar primeira conta disponível
        conta = Conta.objects.first()
        if not conta:
            print("❌ Nenhuma conta encontrada para teste")
            return False
        
        # Teste 1: Alíquotas válidas
        aliquota_valida = Alicotas(
            conta=conta,
            ISS=Decimal('3.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            IRPJ_BASE_CAL=Decimal('32.00'),
            IRPJ_ALIC_1=Decimal('15.00'),
            CSLL_BASE_CAL=Decimal('32.00'),
            CSLL_ALIC_1=Decimal('9.00')
        )
        
        try:
            aliquota_valida.clean()
            print("✓ Validação de alíquotas válidas: PASSOU")
        except Exception as e:
            print(f"❌ Validação de alíquotas válidas: FALHOU - {e}")
            return False
        
        # Teste 2: ISS inválido (muito alto)
        aliquota_invalida = Alicotas(
            conta=conta,
            ISS=Decimal('25.00'),  # Muito alto
        )
        
        try:
            aliquota_invalida.clean()
            print("❌ Validação de ISS alto: FALHOU - Deveria ter rejeitado")
            return False
        except Exception:
            print("✓ Validação de ISS alto: PASSOU - Rejeitado corretamente")
        
        # Teste 3: Data de vigência inválida
        aliquota_data_invalida = Alicotas(
            conta=conta,
            ISS=Decimal('3.00'),
            data_vigencia_inicio=date(2024, 12, 31),
            data_vigencia_fim=date(2024, 1, 1)  # Fim antes do início
        )
        
        try:
            aliquota_data_invalida.clean()
            print("❌ Validação de datas: FALHOU - Deveria ter rejeitado")
            return False
        except Exception:
            print("✓ Validação de datas: PASSOU - Rejeitado corretamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro geral no teste de validação: {e}")
        return False

def test_calculo_impostos():
    """Testa cálculos de impostos"""
    print("\n=== TESTE: Cálculo de Impostos ===")
    
    try:
        # Criar configuração de teste
        conta = Conta.objects.first()
        if not conta:
            print("❌ Nenhuma conta encontrada para teste")
            return False
        
        # Limpar configurações antigas de teste
        Alicotas.objects.filter(conta=conta, observacoes__contains="TESTE").delete()
        
        aliquota = Alicotas.objects.create(
            conta=conta,
            ISS=Decimal('3.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            IRPJ_BASE_CAL=Decimal('32.00'),
            IRPJ_ALIC_1=Decimal('15.00'),
            IRPJ_ALIC_2=Decimal('25.00'),
            IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL=Decimal('20000.00'),
            IRPJ_ADICIONAL=Decimal('10.00'),
            CSLL_BASE_CAL=Decimal('32.00'),
            CSLL_ALIC_1=Decimal('9.00'),
            CSLL_ALIC_2=Decimal('9.00'),
            ativa=True,
            observacoes="TESTE - Configuração para validação"
        )
        
        # Teste 1: Valor baixo (sem adicional de IRPJ)
        valor_baixo = Decimal('10000.00')
        resultado_baixo = aliquota.calcular_impostos_nf(valor_baixo)
        
        # Verificações esperadas
        iss_esperado = valor_baixo * Decimal('0.03')  # 3%
        pis_esperado = valor_baixo * Decimal('0.0065')  # 0.65%
        cofins_esperado = valor_baixo * Decimal('0.03')  # 3%
        
        base_ir = valor_baixo * Decimal('0.32')  # 32%
        ir_esperado = base_ir * Decimal('0.15')  # 15%
        
        base_csll = valor_baixo * Decimal('0.32')  # 32%
        csll_esperado = base_csll * Decimal('0.09')  # 9%
        
        if (abs(resultado_baixo['valor_iss'] - iss_esperado) < Decimal('0.01') and
            abs(resultado_baixo['valor_pis'] - pis_esperado) < Decimal('0.01') and
            abs(resultado_baixo['valor_cofins'] - cofins_esperado) < Decimal('0.01') and
            abs(resultado_baixo['valor_ir'] - ir_esperado) < Decimal('0.01') and
            abs(resultado_baixo['valor_csll'] - csll_esperado) < Decimal('0.01')):
            print("✓ Cálculo valor baixo (sem adicional): PASSOU")
        else:
            print("❌ Cálculo valor baixo (sem adicional): FALHOU")
            print(f"  ISS: esperado {iss_esperado}, obtido {resultado_baixo['valor_iss']}")
            print(f"  PIS: esperado {pis_esperado}, obtido {resultado_baixo['valor_pis']}")
            return False
        
        # Teste 2: Valor alto (com adicional de IRPJ)
        valor_alto = Decimal('100000.00')
        resultado_alto = aliquota.calcular_impostos_nf(valor_alto)
        
        base_ir_alto = valor_alto * Decimal('0.32')  # R$ 32.000
        ir_normal = Decimal('20000.00') * Decimal('0.15')  # 15% sobre R$ 20.000
        ir_adicional = (base_ir_alto - Decimal('20000.00')) * Decimal('0.10')  # 10% sobre excesso
        ir_total_esperado = ir_normal + ir_adicional
        
        if (abs(resultado_alto['valor_ir'] - ir_total_esperado) < Decimal('0.01') and
            resultado_alto['valor_ir_adicional'] > 0):
            print("✓ Cálculo valor alto (com adicional): PASSOU")
        else:
            print("❌ Cálculo valor alto (com adicional): FALHOU")
            print(f"  IR esperado: {ir_total_esperado}, obtido: {resultado_alto['valor_ir']}")
            return False
        
        # Limpeza
        aliquota.delete()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de cálculo: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vigencia_aliquotas():
    """Testa sistema de vigência"""
    print("\n=== TESTE: Sistema de Vigência ===")
    
    try:
        conta = Conta.objects.first()
        if not conta:
            print("❌ Nenhuma conta encontrada para teste")
            return False
        
        # Limpar configurações antigas de teste
        Alicotas.objects.filter(conta=conta, observacoes__contains="TESTE_VIGENCIA").delete()
        
        # Criar configuração antiga (inativa)
        aliquota_antiga = Alicotas.objects.create(
            conta=conta,
            ISS=Decimal('2.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            IRPJ_BASE_CAL=Decimal('32.00'),
            IRPJ_ALIC_1=Decimal('15.00'),
            CSLL_BASE_CAL=Decimal('32.00'),
            CSLL_ALIC_1=Decimal('9.00'),
            ativa=True,
            data_vigencia_inicio=date(2023, 1, 1),
            data_vigencia_fim=date(2023, 12, 31),
            observacoes="TESTE_VIGENCIA - Configuração antiga"
        )
        
        # Criar configuração atual
        aliquota_atual = Alicotas.objects.create(
            conta=conta,
            ISS=Decimal('3.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            IRPJ_BASE_CAL=Decimal('32.00'),
            IRPJ_ALIC_1=Decimal('15.00'),
            CSLL_BASE_CAL=Decimal('32.00'),
            CSLL_ALIC_1=Decimal('9.00'),
            ativa=True,
            data_vigencia_inicio=date(2024, 1, 1),
            observacoes="TESTE_VIGENCIA - Configuração atual"
        )
        
        # Teste 1: Verificar configuração antiga não é vigente
        if not aliquota_antiga.eh_vigente:
            print("✓ Configuração antiga identificada como não vigente: PASSOU")
        else:
            print("❌ Configuração antiga identificada como vigente: FALHOU")
            return False
        
        # Teste 2: Verificar configuração atual é vigente
        if aliquota_atual.eh_vigente:
            print("✓ Configuração atual identificada como vigente: PASSOU")
        else:
            print("❌ Configuração atual identificada como não vigente: FALHOU")
            return False
        
        # Teste 3: Buscar configuração vigente
        configuracao_vigente = Alicotas.obter_alicota_vigente(conta)
        if configuracao_vigente and configuracao_vigente.id == aliquota_atual.id:
            print("✓ Busca de configuração vigente: PASSOU")
        else:
            print("❌ Busca de configuração vigente: FALHOU")
            return False
        
        # Limpeza
        aliquota_antiga.delete()
        aliquota_atual.delete()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de vigência: {e}")
        return False

def test_integracao_nota_fiscal():
    """Testa integração com NotaFiscal"""
    print("\n=== TESTE: Integração com Nota Fiscal ===")
    
    try:
        conta = Conta.objects.first()
        if not conta:
            print("❌ Nenhuma conta encontrada para teste")
            return False
        
        # Limpar dados de teste
        Alicotas.objects.filter(conta=conta, observacoes__contains="TESTE_NF").delete()
        NotaFiscal.objects.filter(numero__contains="TESTE").delete()
        
        # Criar configuração de alíquotas
        aliquota = Alicotas.objects.create(
            conta=conta,
            ISS=Decimal('3.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            IRPJ_BASE_CAL=Decimal('32.00'),
            IRPJ_ALIC_1=Decimal('15.00'),
            CSLL_BASE_CAL=Decimal('32.00'),
            CSLL_ALIC_1=Decimal('9.00'),
            ativa=True,
            observacoes="TESTE_NF - Para teste de nota fiscal"
        )
        
        # Criar nota fiscal
        nota = NotaFiscal.objects.create(
            conta=conta,
            numero="TESTE001",
            val_bruto=Decimal('5000.00'),
            data_emissao=date.today(),
            desc_servico="Teste de serviços médicos"
        )
        
        # Aplicar cálculos
        aliquota.aplicar_impostos_nota_fiscal(nota)
        nota.save()
        
        # Verificar se valores foram calculados
        if (nota.val_ISS > 0 and
            nota.val_PIS > 0 and
            nota.val_COFINS > 0 and
            nota.val_IR > 0 and
            nota.val_CSLL > 0 and
            nota.val_liquido > 0 and
            nota.val_liquido < nota.val_bruto):
            print("✓ Integração com Nota Fiscal: PASSOU")
            print(f"  Valor bruto: R$ {nota.val_bruto}")
            print(f"  Valor líquido: R$ {nota.val_liquido}")
            print(f"  Total impostos: R$ {nota.val_bruto - nota.val_liquido}")
        else:
            print("❌ Integração com Nota Fiscal: FALHOU")
            print(f"  ISS: {nota.val_ISS}")
            print(f"  Líquido: {nota.val_liquido}")
            return False
        
        # Limpeza
        nota.delete()
        aliquota.delete()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DO SISTEMA DE ALÍQUOTAS")
    print("=" * 60)
    
    testes = [
        test_validacao_aliquotas,
        test_calculo_impostos,
        test_vigencia_aliquotas,
        test_integracao_nota_fiscal
    ]
    
    sucessos = 0
    total = len(testes)
    
    for teste in testes:
        try:
            if teste():
                sucessos += 1
        except Exception as e:
            print(f"❌ Erro inesperado em {teste.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {sucessos}/{total} testes passaram")
    
    if sucessos == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando corretamente.")
        return True
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. Verificar implementação.")
        return False

if __name__ == "__main__":
    main()
