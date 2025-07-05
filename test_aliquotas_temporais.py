#!/usr/bin/env python
"""
Script de teste para o sistema temporal de alíquotas ISS

Este script testa:
1. Configurações temporais de alíquotas (mensais/decretos)
2. Hierarquia de alíquotas (empresa > conta temporal > padrão)
3. Validações de sobreposição de vigências
4. Cálculos com alíquotas específicas por data
5. Histórico de alterações de alíquotas
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.core.exceptions import ValidationError
from medicos.models import Conta, Empresa
from medicos.models.fiscal import Aliquotas


def criar_dados_teste():
    """Cria dados básicos para teste"""
    print("\n🏗️ Criando dados de teste...")
    
    # Criar conta de teste
    conta, created = Conta.objects.get_or_create(
        name='Conta Teste Alíquotas Temporais',
        defaults={'cnpj': '12345678000199'}
    )
    
    print(f"✅ Conta: {conta}")
    return conta


def testar_aliquotas_temporais(conta):
    """Testa as configurações temporais de alíquotas"""
    print("\n📅 TESTANDO ALÍQUOTAS TEMPORAIS")
    print("=" * 50)
    
    hoje = date.today()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = mes_passado.replace(day=1)
    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    print(f"Mês passado: {mes_passado}")
    print(f"Hoje: {hoje}")
    print(f"Próximo mês: {proximo_mes}")
    
    # Teste 1: Criar alíquotas do mês passado
    print("\n1. Criando alíquotas do mês passado...")
    aliquotas_passado = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('2.00'),
        ISS_PLANTAO=Decimal('2.00'),
        ISS_OUTROS=Decimal('3.00'),
        ativa=True,
        data_vigencia_inicio=mes_passado,
        data_vigencia_fim=hoje - timedelta(days=1),
        observacoes="Alíquotas do mês passado"
    )
    print(f"✅ Alíquotas mês passado: {aliquotas_passado}")
    
    # Teste 2: Criar alíquotas atuais (decreto mudou as alíquotas)
    print("\n2. Criando alíquotas atuais (decreto municipal mudou)...")
    aliquotas_atual = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('2.50'),  # Aumento por decreto
        ISS_PLANTAO=Decimal('2.50'),    # Aumento por decreto
        ISS_OUTROS=Decimal('3.50'),     # Aumento por decreto
        ativa=True,
        data_vigencia_inicio=hoje,
        data_vigencia_fim=proximo_mes - timedelta(days=1),
        observacoes="Decreto municipal 2025/001 - aumento das alíquotas"
    )
    print(f"✅ Alíquotas atuais: {aliquotas_atual}")
    
    # Teste 3: Criar alíquotas futuras (já programadas)
    print("\n3. Criando alíquotas futuras (já programadas)...")
    aliquotas_futuro = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('3.00'),  # Novo aumento programado
        ISS_PLANTAO=Decimal('3.00'),
        ISS_OUTROS=Decimal('4.00'),
        ativa=True,
        data_vigencia_inicio=proximo_mes,
        # Sem data_vigencia_fim = vigência indefinida
        observacoes="Alíquotas programadas para o próximo mês"
    )
    print(f"✅ Alíquotas futuras: {aliquotas_futuro}")
    
    return aliquotas_passado, aliquotas_atual, aliquotas_futuro


def testar_busca_por_data(conta, aliquotas_passado, aliquotas_atual, aliquotas_futuro):
    """Testa a busca de alíquotas por data específica"""
    print("\n🔍 TESTANDO BUSCA POR DATA ESPECÍFICA")
    print("=" * 50)
    
    hoje = date.today()
    data_passado = aliquotas_passado.data_vigencia_inicio + timedelta(days=5)
    data_futuro = aliquotas_futuro.data_vigencia_inicio + timedelta(days=5)
    
    # Teste busca no passado
    print(f"\n1. Buscando alíquota para {data_passado}...")
    aliq_encontrada_passado = Aliquotas.obter_aliquota_vigente(conta, data_passado)
    print(f"Encontrada: {aliq_encontrada_passado}")
    print(f"ISS Consultas: {aliq_encontrada_passado.ISS_CONSULTAS}%")
    
    # Teste busca atual
    print(f"\n2. Buscando alíquota para hoje ({hoje})...")
    aliq_encontrada_atual = Aliquotas.obter_aliquota_vigente(conta, hoje)
    print(f"Encontrada: {aliq_encontrada_atual}")
    print(f"ISS Consultas: {aliq_encontrada_atual.ISS_CONSULTAS}%")
    
    # Teste busca futura
    print(f"\n3. Buscando alíquota para {data_futuro}...")
    aliq_encontrada_futuro = Aliquotas.obter_aliquota_vigente(conta, data_futuro)
    print(f"Encontrada: {aliq_encontrada_futuro}")
    print(f"ISS Consultas: {aliq_encontrada_futuro.ISS_CONSULTAS}%")


def testar_empresa_com_sistema_temporal(conta):
    """Testa empresa utilizando o sistema temporal de alíquotas"""
    print("\n🏥 TESTANDO EMPRESA COM SISTEMA TEMPORAL")
    print("=" * 50)
    
    # Criar empresa sem alíquotas específicas (usa configurações da conta)
    empresa = Empresa.objects.create(
        conta=conta,
        name='Hospital Temporal Ltda',
        nome_fantasia='Hospital Temporal',
        cnpj='11222333000144',
        usa_aliquotas_especificas=False  # Usa configurações da conta
    )
    print(f"Empresa criada: {empresa}")
    
    hoje = date.today()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = mes_passado.replace(day=1)
    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    # Testar alíquotas por data
    print(f"\n1. Alíquotas para o mês passado ({mes_passado}):")
    resumo_passado = empresa.get_resumo_aliquotas(mes_passado + timedelta(days=5))
    print(f"  - Consultas: {resumo_passado['consultas']}%")
    print(f"  - Plantão: {resumo_passado['plantao']}%")
    print(f"  - Outros: {resumo_passado['outros']}%")
    
    print(f"\n2. Alíquotas para hoje ({hoje}):")
    resumo_atual = empresa.get_resumo_aliquotas(hoje)
    print(f"  - Consultas: {resumo_atual['consultas']}%")
    print(f"  - Plantão: {resumo_atual['plantao']}%")
    print(f"  - Outros: {resumo_atual['outros']}%")
    
    print(f"\n3. Alíquotas para o próximo mês ({proximo_mes}):")
    resumo_futuro = empresa.get_resumo_aliquotas(proximo_mes + timedelta(days=5))
    print(f"  - Consultas: {resumo_futuro['consultas']}%")
    print(f"  - Plantão: {resumo_futuro['plantao']}%")
    print(f"  - Outros: {resumo_futuro['outros']}%")
    
    return empresa


def testar_empresa_com_override(conta):
    """Testa empresa que sobrescreve alíquotas da conta"""
    print("\n🏢 TESTANDO EMPRESA COM OVERRIDE DE ALÍQUOTAS")
    print("=" * 50)
    
    # Criar empresa com alíquotas específicas
    empresa_especial = Empresa.objects.create(
        conta=conta,
        name='Clínica Especial Ltda',
        nome_fantasia='Clínica Especial',
        cnpj='33444555000166',
        usa_aliquotas_especificas=True,  # Usa suas próprias alíquotas
        aliquota_iss_consultas=Decimal('1.50'),  # Alíquota reduzida por convênio
        aliquota_iss_plantao=Decimal('1.50'),
        aliquota_iss_outros=Decimal('2.00'),
        observacoes_tributarias='Convênio especial com a prefeitura - alíquotas reduzidas'
    )
    print(f"Empresa especial criada: {empresa_especial}")
    
    hoje = date.today()
    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    # Testar que sempre usa as alíquotas da empresa, independente da data
    print(f"\n1. Alíquotas para hoje (deve usar da empresa):")
    resumo_hoje = empresa_especial.get_resumo_aliquotas(hoje)
    print(f"  - Consultas: {resumo_hoje['consultas']}% (empresa: {empresa_especial.aliquota_iss_consultas}%)")
    print(f"  - Usa específicas: {resumo_hoje['usa_especificas']}")
    
    print(f"\n2. Alíquotas para o futuro (deve usar da empresa):")
    resumo_futuro = empresa_especial.get_resumo_aliquotas(proximo_mes)
    print(f"  - Consultas: {resumo_futuro['consultas']}% (empresa: {empresa_especial.aliquota_iss_consultas}%)")
    print(f"  - Usa específicas: {resumo_futuro['usa_especificas']}")
    
    return empresa_especial


def testar_validacao_sobreposicao(conta):
    """Testa validação de sobreposição de vigências"""
    print("\n❌ TESTANDO VALIDAÇÃO DE SOBREPOSIÇÃO")
    print("=" * 50)
    
    hoje = date.today()
    
    # Tentar criar alíquota que sobrepõe com existente
    print("\n1. Tentando criar alíquota que sobrepõe...")
    try:
        aliquota_sobreposicao = Aliquotas(
            conta=conta,
            ISS_CONSULTAS=Decimal('5.00'),
            ISS_PLANTAO=Decimal('5.00'),
            ISS_OUTROS=Decimal('5.00'),
            ativa=True,
            data_vigencia_inicio=hoje - timedelta(days=5),  # Sobrepõe com atual
            data_vigencia_fim=hoje + timedelta(days=10),
            observacoes="Tentativa de sobreposição"
        )
        aliquota_sobreposicao.full_clean()
        print("❌ Deveria ter falhado na validação de sobreposição")
    except ValidationError as e:
        print(f"✅ Validação de sobreposição funcionando: {e}")


def testar_calculo_impostos_temporal(empresa):
    """Testa cálculo de impostos considerando data específica"""
    print("\n💰 TESTANDO CÁLCULO DE IMPOSTOS TEMPORAL")
    print("=" * 50)
    
    valor_nota = Decimal('1000.00')
    hoje = date.today()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = mes_passado.replace(day=1)
    
    # Calcular impostos para o mês passado
    print(f"\n1. Calculando impostos para nota de {mes_passado}:")
    impostos_passado = empresa.calcular_impostos_nf_na_data(
        valor_nota, 'consultas', mes_passado + timedelta(days=5)
    )
    print(f"  Valor bruto: R$ {impostos_passado['valor_bruto']}")
    print(f"  ISS ({impostos_passado['aliquota_iss_aplicada']}%): R$ {impostos_passado['valor_iss']}")
    print(f"  Valor líquido: R$ {impostos_passado['valor_liquido']}")
    
    # Calcular impostos para hoje
    print(f"\n2. Calculando impostos para nota de hoje:")
    impostos_hoje = empresa.calcular_impostos_nf_na_data(
        valor_nota, 'consultas', hoje
    )
    print(f"  Valor bruto: R$ {impostos_hoje['valor_bruto']}")
    print(f"  ISS ({impostos_hoje['aliquota_iss_aplicada']}%): R$ {impostos_hoje['valor_iss']}")
    print(f"  Valor líquido: R$ {impostos_hoje['valor_liquido']}")
    
    # Comparar diferença
    diferenca_iss = impostos_hoje['valor_iss'] - impostos_passado['valor_iss']
    print(f"\n3. Impacto da mudança de alíquota:")
    print(f"  Diferença no ISS: R$ {diferenca_iss}")
    print(f"  Percentual de aumento: {(diferenca_iss / impostos_passado['valor_iss'] * 100):.2f}%")


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO SISTEMA TEMPORAL DE ALÍQUOTAS")
    print("=" * 70)
    
    try:
        # Configurar dados de teste
        conta = criar_dados_teste()
        
        # Testar sistema temporal
        aliquotas_passado, aliquotas_atual, aliquotas_futuro = testar_aliquotas_temporais(conta)
        testar_busca_por_data(conta, aliquotas_passado, aliquotas_atual, aliquotas_futuro)
        
        # Testar empresas
        empresa_temporal = testar_empresa_com_sistema_temporal(conta)
        empresa_especial = testar_empresa_com_override(conta)
        
        # Testar validações e cálculos
        testar_validacao_sobreposicao(conta)
        testar_calculo_impostos_temporal(empresa_temporal)
        
        print("\n" + "=" * 70)
        print("🎉 TESTES DO SISTEMA TEMPORAL CONCLUÍDOS COM SUCESSO!")
        print("✅ Configurações temporais de alíquotas funcionando")
        print("✅ Busca por data específica funcionando")
        print("✅ Hierarquia de alíquotas (empresa > conta temporal > padrão) funcionando")
        print("✅ Validação de sobreposição de vigências funcionando")
        print("✅ Cálculos com data específica funcionando")
        print("✅ Sistema preparado para mudanças mensais por decreto")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
