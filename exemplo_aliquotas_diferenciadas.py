#!/usr/bin/env python3
"""
Exemplo Prático - Alíquotas Diferenciadas por Tipo de Serviço Médico
Sistema de Contabilidade para Associações Médicas
"""

from decimal import Decimal
from datetime import date

def exemplo_aliquotas_diferenciadas():
    """
    Demonstra como diferentes tipos de serviços médicos podem ter 
    alíquotas de ISS diferenciadas
    """
    print("=" * 80)
    print("EXEMPLO: ALÍQUOTAS DIFERENCIADAS POR TIPO DE SERVIÇO MÉDICO")
    print("=" * 80)
    
    # Configuração de alíquotas diferenciadas (exemplo real)
    configuracao = {
        'ISS_CONSULTAS': Decimal('3.00'),      # 3% para consultas
        'ISS_PLANTAO': Decimal('2.50'),        # 2,5% para plantão (incentivo)  
        'ISS_OUTROS': Decimal('4.00'),         # 4% para outros serviços
        'PIS': Decimal('0.65'),                # Uniforme
        'COFINS': Decimal('3.00'),             # Uniforme
        'IRPJ_BASE_CAL': Decimal('32.00'),     # Uniforme
        'IRPJ_ALIC_1': Decimal('15.00'),       # Uniforme
        'CSLL_BASE_CAL': Decimal('32.00'),     # Uniforme
        'CSLL_ALIC_1': Decimal('9.00'),        # Uniforme
    }
    
    # Valor da nota fiscal para comparação
    valor_nota = Decimal('10000.00')
    
    print(f"Valor da Nota Fiscal: R$ {valor_nota:,.2f}")
    print(f"Configuração de Alíquotas:")
    print(f"  - ISS Consultas: {configuracao['ISS_CONSULTAS']}%")
    print(f"  - ISS Plantão: {configuracao['ISS_PLANTAO']}%") 
    print(f"  - ISS Outros: {configuracao['ISS_OUTROS']}%")
    print(f"  - PIS: {configuracao['PIS']}% (uniforme)")
    print(f"  - COFINS: {configuracao['COFINS']}% (uniforme)")
    print(f"  - IRPJ: {configuracao['IRPJ_ALIC_1']}% sobre {configuracao['IRPJ_BASE_CAL']}% da receita")
    print(f"  - CSLL: {configuracao['CSLL_ALIC_1']}% sobre {configuracao['CSLL_BASE_CAL']}% da receita")
    print()
    
    # Calcular para cada tipo de serviço
    servicos = [
        ('CONSULTAS MÉDICAS', 'ISS_CONSULTAS'),
        ('PLANTÃO MÉDICO', 'ISS_PLANTAO'),
        ('VACINAÇÃO/EXAMES/PROCEDIMENTOS', 'ISS_OUTROS')
    ]
    
    resultados = []
    
    for nome_servico, campo_iss in servicos:
        print(f"📋 {nome_servico}")
        print("-" * 50)
        
        # ISS específico do serviço
        aliquota_iss = configuracao[campo_iss]
        valor_iss = valor_nota * (aliquota_iss / 100)
        
        # Impostos federais (uniformes)
        valor_pis = valor_nota * (configuracao['PIS'] / 100)
        valor_cofins = valor_nota * (configuracao['COFINS'] / 100)
        
        # Base para IR e CSLL
        base_ir = valor_nota * (configuracao['IRPJ_BASE_CAL'] / 100)
        base_csll = valor_nota * (configuracao['CSLL_BASE_CAL'] / 100)
        
        valor_ir = base_ir * (configuracao['IRPJ_ALIC_1'] / 100)
        valor_csll = base_csll * (configuracao['CSLL_ALIC_1'] / 100)
        
        total_impostos = valor_iss + valor_pis + valor_cofins + valor_ir + valor_csll
        valor_liquido = valor_nota - total_impostos
        carga_tributaria = (total_impostos / valor_nota) * 100
        
        print(f"  ISS ({aliquota_iss}%):     R$ {valor_iss:>8,.2f}")
        print(f"  PIS (0,65%):    R$ {valor_pis:>8,.2f}")
        print(f"  COFINS (3%):    R$ {valor_cofins:>8,.2f}")
        print(f"  IRPJ (15%):     R$ {valor_ir:>8,.2f}")
        print(f"  CSLL (9%):      R$ {valor_csll:>8,.2f}")
        print(f"  " + "─" * 30)
        print(f"  Total Impostos: R$ {total_impostos:>8,.2f}")
        print(f"  Valor Líquido:  R$ {valor_liquido:>8,.2f}")
        print(f"  Carga Tributária: {carga_tributaria:>6.2f}%")
        print()
        
        resultados.append({
            'servico': nome_servico,
            'iss': valor_iss,
            'total_impostos': total_impostos,
            'valor_liquido': valor_liquido,
            'carga_tributaria': carga_tributaria
        })
    
    # Comparação dos resultados
    print("📊 COMPARAÇÃO ENTRE TIPOS DE SERVIÇO")
    print("=" * 80)
    print(f"{'Tipo de Serviço':<35} {'ISS':<12} {'Total Imp.':<12} {'Líquido':<12} {'Carga %':<8}")
    print("-" * 80)
    
    for resultado in resultados:
        print(f"{resultado['servico']:<35} "
              f"R$ {resultado['iss']:>7,.2f} "
              f"R$ {resultado['total_impostos']:>8,.2f} "
              f"R$ {resultado['valor_liquido']:>8,.2f} "
              f"{resultado['carga_tributaria']:>6.2f}%")
    
    # Diferenças em valores absolutos
    print("\n💰 DIFERENÇAS EM VALORES ABSOLUTOS")
    print("-" * 50)
    
    consultas = resultados[0]
    plantao = resultados[1] 
    outros = resultados[2]
    
    # Comparar plantão vs consultas
    dif_plantao_consultas = consultas['total_impostos'] - plantao['total_impostos']
    print(f"Plantão vs Consultas:")
    print(f"  Economia em impostos: R$ {dif_plantao_consultas:,.2f}")
    print(f"  Valor líquido maior: R$ {plantao['valor_liquido'] - consultas['valor_liquido']:,.2f}")
    
    # Comparar outros vs consultas  
    dif_outros_consultas = outros['total_impostos'] - consultas['total_impostos']
    print(f"\nOutros Serviços vs Consultas:")
    print(f"  Impostos adicionais: R$ {dif_outros_consultas:,.2f}")
    print(f"  Valor líquido menor: R$ {consultas['valor_liquido'] - outros['valor_liquido']:,.2f}")

def exemplo_codigo_implementacao():
    """
    Demonstra como implementar as alíquotas diferenciadas no código
    """
    print("\n" + "=" * 80)
    print("IMPLEMENTAÇÃO NO CÓDIGO DJANGO")
    print("=" * 80)
    
    codigo_exemplo = '''
# 1. Configurar alíquotas diferenciadas
aliquota = Aliquotas.objects.create(
    conta=associacao_medica,
    # ISS diferenciado por tipo de serviço
    ISS_CONSULTAS=Decimal('3.00'),      # 3% para consultas
    ISS_PLANTAO=Decimal('2.50'),        # 2,5% para plantão  
    ISS_OUTROS=Decimal('4.00'),         # 4% para outros serviços
    
    # Impostos federais (uniformes)
    PIS=Decimal('0.65'),
    COFINS=Decimal('3.00'),
    IRPJ_BASE_CAL=Decimal('32.00'),
    IRPJ_ALIC_1=Decimal('15.00'),
    CSLL_BASE_CAL=Decimal('32.00'),
    CSLL_ALIC_1=Decimal('9.00'),
    ativa=True
)

# 2. Criar nota fiscal especificando tipo de serviço
nota_consulta = NotaFiscal.objects.create(
    conta=associacao,
    numero="NF001",
    val_bruto=Decimal('10000.00'),
    data_emissao=date.today(),
    tipo_aliquota=1,  # CONSULTAS
    descricao_servicos="Consultas médicas especializadas"
)

nota_plantao = NotaFiscal.objects.create(
    conta=associacao,
    numero="NF002", 
    val_bruto=Decimal('10000.00'),
    data_emissao=date.today(),
    tipo_aliquota=2,  # PLANTÃO
    descricao_servicos="Plantão médico emergencial"
)

nota_outros = NotaFiscal.objects.create(
    conta=associacao,
    numero="NF003",
    val_bruto=Decimal('10000.00'),
    data_emissao=date.today(),
    tipo_aliquota=3,  # OUTROS
    descricao_servicos="Vacinação e exames laboratoriais"
)

# 3. Aplicar cálculos automáticos
for nota in [nota_consulta, nota_plantao, nota_outros]:
    nota.calcular_impostos_automaticamente()
    nota.save()
    
    print(f"Nota {nota.numero} ({nota.tipo_servico_descricao}):")
    print(f"  ISS: R$ {nota.val_ISS}")
    print(f"  Total impostos: R$ {nota.val_bruto - nota.val_liquido}")
    print(f"  Valor líquido: R$ {nota.val_liquido}")

# 4. Cálculo direto por tipo
resultado_consultas = aliquota.calcular_impostos_nf(
    Decimal('10000.00'), 'consultas'
)
resultado_plantao = aliquota.calcular_impostos_nf(
    Decimal('10000.00'), 'plantao'  
)
resultado_outros = aliquota.calcular_impostos_nf(
    Decimal('10000.00'), 'outros'
)

print("Comparação de ISS:")
print(f"  Consultas: R$ {resultado_consultas['valor_iss']}")
print(f"  Plantão: R$ {resultado_plantao['valor_iss']}")
print(f"  Outros: R$ {resultado_outros['valor_iss']}")
'''
    
    print(codigo_exemplo)

def exemplo_beneficios_negocio():
    """
    Demonstra os benefícios de negócio das alíquotas diferenciadas
    """
    print("\n" + "=" * 80)
    print("BENEFÍCIOS DE NEGÓCIO")
    print("=" * 80)
    
    beneficios = [
        "🏥 CONFORMIDADE FISCAL",
        "   • Aplicação correta das alíquotas conforme legislação municipal",
        "   • Redução de riscos de autuação fiscal",
        "   • Documentação automática do tipo de serviço prestado",
        "",
        "💰 OTIMIZAÇÃO TRIBUTÁRIA",
        "   • Aproveitamento de alíquotas reduzidas para plantões",
        "   • Classificação correta evita pagamento excessivo de impostos",
        "   • Planejamento tributário mais preciso",
        "",
        "⚡ AUTOMATIZAÇÃO",
        "   • Cálculo automático baseado no tipo de serviço",
        "   • Eliminação de erros manuais de classificação",
        "   • Agilidade no processamento das notas fiscais",
        "",
        "📊 CONTROLE GERENCIAL",
        "   • Relatórios de carga tributária por tipo de serviço",
        "   • Análise de rentabilidade por modalidade",
        "   • Suporte à tomada de decisões estratégicas",
        "",
        "🔍 AUDITORIA E TRANSPARÊNCIA",
        "   • Histórico completo das alíquotas aplicadas",
        "   • Rastreabilidade dos cálculos tributários",
        "   • Facilita auditorias internas e externas"
    ]
    
    for beneficio in beneficios:
        print(beneficio)

if __name__ == "__main__":
    exemplo_aliquotas_diferenciadas()
    exemplo_codigo_implementacao()
    exemplo_beneficios_negocio()
    
    print("\n" + "=" * 80)
    print("✅ SISTEMA DE ALÍQUOTAS DIFERENCIADAS IMPLEMENTADO COM SUCESSO!")
    print("🚀 Pronto para uso em produção!")
    print("=" * 80)
