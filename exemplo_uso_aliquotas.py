#!/usr/bin/env python3
"""
Exemplo prático de uso do Sistema de Alíquotas
Sistema de Contabilidade para Associações Médicas
"""

from decimal import Decimal
from datetime import date
from medicos.models import Conta, Alicotas, NotaFiscal

def exemplo_configuracao_aliquotas():
    """
    Exemplo: Configurar alíquotas para uma associação médica
    """
    print("=== CONFIGURAÇÃO DE ALÍQUOTAS ===")
    
    # Buscar ou criar uma conta (associação médica)
    conta = Conta.objects.get(name="Associação Médica ABC")
    
    # Criar configuração de alíquotas
    aliquota = Alicotas.objects.create(
        conta=conta,
        # Impostos municipais
        ISS=3.00,  # 3% - varia por município
        
        # Contribuições federais
        PIS=0.65,      # 0,65% - padrão federal
        COFINS=3.00,   # 3% - padrão federal
        
        # IRPJ - Lucro Presumido
        IRPJ_BASE_CAL=32.00,                      # 32% da receita para base
        IRPJ_ALIC_1=15.00,                        # 15% normal
        IRPJ_ALIC_2=25.00,                        # 25% total (15% + 10%)
        IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL=20000.00,  # R$ 20.000 limite mensal
        IRPJ_ADICIONAL=10.00,                     # 10% adicional
        
        # CSLL - Contribuição Social
        CSLL_BASE_CAL=32.00,  # 32% da receita para base
        CSLL_ALIC_1=9.00,     # 9% para prestação de serviços
        CSLL_ALIC_2=9.00,     # Mesmo valor
        
        # Controle
        ativa=True,
        data_vigencia_inicio=date(2024, 1, 1),
        observacoes="Configuração padrão para prestação de serviços médicos"
    )
    
    print(f"✓ Alíquotas configuradas: {aliquota}")
    return aliquota

def exemplo_calculo_impostos():
    """
    Exemplo: Calcular impostos para uma nota fiscal
    """
    print("\n=== CÁLCULO DE IMPOSTOS ===")
    
    # Valor da nota fiscal
    valor_bruto = Decimal('10000.00')  # R$ 10.000,00
    
    # Buscar configuração vigente
    conta = Conta.objects.get(name="Associação Médica ABC")
    aliquota = Alicotas.obter_alicota_vigente(conta)
    
    if not aliquota:
        print("❌ Nenhuma configuração de alíquotas vigente encontrada")
        return
    
    # Calcular impostos
    resultado = aliquota.calcular_impostos_nf(valor_bruto, 'consultas')
    
    print(f"Valor Bruto: R$ {resultado['valor_bruto']:,.2f}")
    print(f"ISS (3%): R$ {resultado['valor_iss']:,.2f}")
    print(f"PIS (0,65%): R$ {resultado['valor_pis']:,.2f}")
    print(f"COFINS (3%): R$ {resultado['valor_cofins']:,.2f}")
    print(f"IRPJ: R$ {resultado['valor_ir']:,.2f}")
    print(f"  - Normal (15%): R$ {resultado['valor_ir_normal']:,.2f}")
    print(f"  - Adicional (10%): R$ {resultado['valor_ir_adicional']:,.2f}")
    print(f"CSLL (9%): R$ {resultado['valor_csll']:,.2f}")
    print(f"─" * 40)
    print(f"Total Impostos: R$ {resultado['total_impostos']:,.2f}")
    print(f"Valor Líquido: R$ {resultado['valor_liquido']:,.2f}")
    print(f"Carga Tributária: {(resultado['total_impostos']/resultado['valor_bruto']*100):.2f}%")
    
    return resultado

def exemplo_nota_fiscal_automatica():
    """
    Exemplo: Criar nota fiscal com cálculo automático
    """
    print("\n=== NOTA FISCAL AUTOMÁTICA ===")
    
    conta = Conta.objects.get(name="Associação Médica ABC")
    
    # Criar nota fiscal apenas com valor bruto
    nota = NotaFiscal.objects.create(
        conta=conta,
        numero="000123",
        val_bruto=Decimal('15000.00'),  # R$ 15.000,00
        data_emissao=date.today(),
        desc_servico="Consultas médicas especializadas"
    )
    
    print(f"✓ Nota fiscal criada: {nota.numero}")
    print(f"Valor Bruto: R$ {nota.val_bruto:,.2f}")
    
    # Buscar alíquotas e aplicar cálculos
    aliquota = Alicotas.obter_alicota_vigente(conta)
    if aliquota:
        aliquota.aplicar_impostos_nota_fiscal(nota)
        nota.save()
        
        print(f"✓ Impostos calculados automaticamente:")
        print(f"  ISS: R$ {nota.val_ISS:,.2f}")
        print(f"  PIS: R$ {nota.val_PIS:,.2f}")
        print(f"  COFINS: R$ {nota.val_COFINS:,.2f}")
        print(f"  IRPJ: R$ {nota.val_IR:,.2f}")
        print(f"  CSLL: R$ {nota.val_CSLL:,.2f}")
        print(f"  Valor Líquido: R$ {nota.val_liquido:,.2f}")
    else:
        print("❌ Configuração de alíquotas não encontrada")
    
    return nota

def exemplo_analise_cenarios():
    """
    Exemplo: Análise de diferentes cenários tributários
    """
    print("\n=== ANÁLISE DE CENÁRIOS ===")
    
    valores_teste = [5000, 10000, 25000, 50000, 100000]
    conta = Conta.objects.get(name="Associação Médica ABC")
    aliquota = Alicotas.obter_alicota_vigente(conta)
    
    print(f"{'Valor Bruto':>12} {'Total Impostos':>15} {'Valor Líquido':>15} {'Carga %':>10}")
    print("─" * 60)
    
    for valor in valores_teste:
        resultado = aliquota.calcular_impostos_nf(Decimal(str(valor)))
        carga = resultado['total_impostos'] / resultado['valor_bruto'] * 100
        
        print(f"R$ {valor:>8,.0f} "
              f"R$ {resultado['total_impostos']:>11,.2f} "
              f"R$ {resultado['valor_liquido']:>11,.2f} "
              f"{carga:>7.2f}%")

def exemplo_historico_aliquotas():
    """
    Exemplo: Controle de histórico de alíquotas
    """
    print("\n=== HISTÓRICO DE ALÍQUOTAS ===")
    
    conta = Conta.objects.get(name="Associação Médica ABC")
    
    # Criar nova configuração (ex: mudança na legislação)
    nova_aliquota = Alicotas.objects.create(
        conta=conta,
        ISS=3.50,  # Aumento do ISS municipal
        PIS=0.65,
        COFINS=3.00,
        IRPJ_BASE_CAL=32.00,
        IRPJ_ALIC_1=15.00,
        IRPJ_ALIC_2=25.00,
        IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL=20000.00,
        IRPJ_ADICIONAL=10.00,
        CSLL_BASE_CAL=32.00,
        CSLL_ALIC_1=9.00,
        CSLL_ALIC_2=9.00,
        ativa=True,
        data_vigencia_inicio=date(2024, 7, 1),  # Nova vigência
        observacoes="Aumento do ISS conforme Lei Municipal 123/2024"
    )
    
    # Desativar configuração anterior
    aliquota_anterior = Alicotas.objects.filter(
        conta=conta,
        ativa=True,
        data_vigencia_inicio__lt=date(2024, 7, 1)
    ).first()
    
    if aliquota_anterior:
        aliquota_anterior.data_vigencia_fim = date(2024, 6, 30)
        aliquota_anterior.save()
        print(f"✓ Configuração anterior finalizada em {aliquota_anterior.data_vigencia_fim}")
    
    print(f"✓ Nova configuração criada: ISS {nova_aliquota.ISS}% (vigência: {nova_aliquota.data_vigencia_inicio})")
    
    # Listar histórico
    historico = Alicotas.objects.filter(conta=conta).order_by('-data_vigencia_inicio')
    print("\nHistórico de configurações:")
    for config in historico:
        status = "ATIVA" if config.eh_vigente else "INATIVA"
        print(f"  {config.data_vigencia_inicio} - ISS: {config.ISS}% - {status}")

if __name__ == "__main__":
    """
    Executar exemplos do sistema de alíquotas
    """
    try:
        # 1. Configurar alíquotas
        exemplo_configuracao_aliquotas()
        
        # 2. Calcular impostos
        exemplo_calculo_impostos()
        
        # 3. Nota fiscal automática
        exemplo_nota_fiscal_automatica()
        
        # 4. Análise de cenários
        exemplo_analise_cenarios()
        
        # 5. Histórico de alíquotas
        exemplo_historico_aliquotas()
        
        print("\n✅ Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
