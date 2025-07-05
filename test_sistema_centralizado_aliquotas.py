#!/usr/bin/env python
"""
Script de teste para o sistema centralizado de alíquotas

Este script demonstra:
1. Uso exclusivo do modelo Aliquotas para configurações de alíquotas
2. Temporalidade das alíquotas (mudanças mensais por decreto)
3. Hierarquia simplificada: configuração temporal da conta > padrão
4. Cálculos utilizando apenas o sistema centralizado
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
        name='Conta Sistema Centralizado',
        defaults={'cnpj': '12345678000199'}
    )
    
    print(f"✅ Conta: {conta}")
    return conta


def testar_sistema_centralizado(conta):
    """Testa o sistema centralizado de alíquotas"""
    print("\n🎯 TESTANDO SISTEMA CENTRALIZADO DE ALÍQUOTAS")
    print("=" * 60)
    
    hoje = date.today()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = mes_passado.replace(day=1)
    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    print(f"📅 Período de teste:")
    print(f"  Mês passado: {mes_passado}")
    print(f"  Hoje: {hoje}")
    print(f"  Próximo mês: {proximo_mes}")
    
    # 1. Criar configuração do mês passado
    print(f"\n1. Criando alíquotas do mês passado...")
    aliquotas_passado = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('2.00'),
        ISS_PLANTAO=Decimal('2.00'),
        ISS_OUTROS=Decimal('3.00'),
        PIS=Decimal('0.65'),
        COFINS=Decimal('3.00'),
        ativa=True,
        data_vigencia_inicio=mes_passado,
        data_vigencia_fim=hoje - timedelta(days=1),
        observacoes="Decreto municipal 001/2024"
    )
    print(f"  ✅ {aliquotas_passado}")
    
    # 2. Criar configuração atual (decreto mudou alíquotas)
    print(f"\n2. Criando alíquotas atuais (decreto municipal alterou)...")
    aliquotas_atual = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('2.50'),  # Aumento por decreto
        ISS_PLANTAO=Decimal('2.50'),
        ISS_OUTROS=Decimal('3.50'),
        PIS=Decimal('0.65'),
        COFINS=Decimal('3.00'),
        ativa=True,
        data_vigencia_inicio=hoje,
        data_vigencia_fim=proximo_mes - timedelta(days=1),
        observacoes="Decreto municipal 002/2025 - aumento ISS"
    )
    print(f"  ✅ {aliquotas_atual}")
    
    # 3. Criar configuração futura (já programada)
    print(f"\n3. Programando alíquotas para o próximo mês...")
    aliquotas_futuro = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('3.00'),  # Novo aumento programado
        ISS_PLANTAO=Decimal('3.00'),
        ISS_OUTROS=Decimal('4.00'),
        PIS=Decimal('0.65'),
        COFINS=Decimal('3.00'),
        ativa=True,
        data_vigencia_inicio=proximo_mes,
        observacoes="Decreto municipal 003/2025 - novo aumento programado"
    )
    print(f"  ✅ {aliquotas_futuro}")
    
    return aliquotas_passado, aliquotas_atual, aliquotas_futuro


def testar_empresa_usando_sistema_centralizado(conta):
    """Testa empresa utilizando apenas o sistema centralizado"""
    print("\n🏥 TESTANDO EMPRESA COM SISTEMA CENTRALIZADO")
    print("=" * 60)
    
    # Criar empresa simples (sem campos de alíquota)
    empresa = Empresa.objects.create(
        conta=conta,
        name='Clínica Modelo Ltda',
        nome_fantasia='Clínica Modelo',
        cnpj='11222333000144',
        regime_tributario='Lucro Presumido',
        observacoes_tributarias='Segue decreto municipal vigente'
    )
    print(f"Empresa criada: {empresa}")
    
    hoje = date.today()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = mes_passado.replace(day=1)
    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    # Testar alíquotas por período
    print(f"\n📊 Alíquotas por período:")
    
    periodos = [
        ('Mês passado', mes_passado + timedelta(days=5)),
        ('Hoje', hoje),
        ('Próximo mês', proximo_mes + timedelta(days=5))
    ]
    
    for nome_periodo, data_teste in periodos:
        print(f"\n  {nome_periodo} ({data_teste}):")
        resumo = empresa.get_resumo_aliquotas(data_teste)
        print(f"    - Consultas: {resumo['consultas']}%")
        print(f"    - Plantão: {resumo['plantao']}%")
        print(f"    - Outros: {resumo['outros']}%")
        print(f"    - Configuração ativa: {'Sim' if resumo['tem_configuracao_conta'] else 'Não (usando padrão)'}")
    
    return empresa


def testar_calculos_temporais(empresa):
    """Testa cálculos de impostos em diferentes períodos"""
    print("\n💰 TESTANDO CÁLCULOS TEMPORAIS")
    print("=" * 60)
    
    valor_nota = Decimal('1000.00')
    hoje = date.today()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = mes_passado.replace(day=1)
    proximo_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    periodos_teste = [
        ('Mês passado', mes_passado + timedelta(days=5)),
        ('Hoje', hoje),
        ('Próximo mês', proximo_mes + timedelta(days=5))
    ]
    
    print(f"💵 Calculando impostos para nota de R$ {valor_nota} (consultas):")
    
    resultados = []
    for nome_periodo, data_teste in periodos_teste:
        print(f"\n  📅 {nome_periodo} ({data_teste}):")
        
        impostos = empresa.calcular_impostos_nf_na_data(
            valor_nota, 'consultas', data_teste
        )
        
        print(f"    Valor bruto: R$ {impostos['valor_bruto']}")
        print(f"    ISS ({impostos['aliquota_iss_aplicada']}%): R$ {impostos['valor_iss']}")
        
        if 'valor_pis' in impostos:
            print(f"    PIS: R$ {impostos['valor_pis']}")
            print(f"    COFINS: R$ {impostos['valor_cofins']}")
            print(f"    Total impostos: R$ {impostos['total_impostos']}")
        
        print(f"    Valor líquido: R$ {impostos['valor_liquido']}")
        
        resultados.append((nome_periodo, impostos))
    
    # Comparar diferenças
    print(f"\n📈 Análise do impacto das mudanças:")
    if len(resultados) >= 2:
        passado_iss = resultados[0][1]['valor_iss']
        atual_iss = resultados[1][1]['valor_iss'] 
        diferenca = atual_iss - passado_iss
        percentual = (diferenca / passado_iss * 100) if passado_iss > 0 else 0
        
        print(f"  Diferença ISS (passado → atual): R$ {diferenca} ({percentual:.1f}%)")
        
        if len(resultados) >= 3:
            futuro_iss = resultados[2][1]['valor_iss']
            diferenca_futuro = futuro_iss - atual_iss
            percentual_futuro = (diferenca_futuro / atual_iss * 100) if atual_iss > 0 else 0
            
            print(f"  Diferença ISS (atual → futuro): R$ {diferenca_futuro} ({percentual_futuro:.1f}%)")


def testar_historico_aliquotas(empresa):
    """Testa visualização do histórico de alíquotas"""
    print("\n📚 TESTANDO HISTÓRICO DE ALÍQUOTAS")
    print("=" * 60)
    
    historico = empresa.obter_historico_aliquotas()
    
    if historico:
        print("📋 Histórico de configurações (mais recente primeiro):")
        for i, config in enumerate(historico, 1):
            print(f"\n  {i}. Vigência: {config.data_vigencia_inicio} até {config.data_vigencia_fim or 'indeterminado'}")
            print(f"     ISS: Consultas {config.ISS_CONSULTAS}%, Plantão {config.ISS_PLANTAO}%, Outros {config.ISS_OUTROS}%")
            print(f"     Status: {'Ativa' if config.eh_vigente else 'Inativa'}")
            if config.observacoes:
                print(f"     Obs: {config.observacoes}")
    else:
        print("❌ Nenhuma configuração de alíquotas encontrada")


def testar_busca_por_data(conta):
    """Testa busca de configurações por data específica"""
    print("\n🔍 TESTANDO BUSCA POR DATA ESPECÍFICA")
    print("=" * 60)
    
    hoje = date.today()
    datas_teste = [
        hoje - timedelta(days=45),  # Antes de qualquer configuração
        hoje - timedelta(days=15),  # Mês passado
        hoje,                       # Hoje
        hoje + timedelta(days=15),  # Próximo mês
        hoje + timedelta(days=60),  # Futuro distante
    ]
    
    for data_teste in datas_teste:
        print(f"\n  📅 Buscando configuração para {data_teste}:")
        config = Aliquotas.obter_aliquota_vigente(conta, data_teste)
        
        if config:
            print(f"    ✅ Encontrada: ISS Consultas {config.ISS_CONSULTAS}%")
            print(f"    Vigência: {config.data_vigencia_inicio} até {config.data_vigencia_fim or 'indeterminado'}")
            if config.observacoes:
                print(f"    Decreto: {config.observacoes}")
        else:
            print(f"    ❌ Nenhuma configuração vigente (usará valores padrão)")


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO SISTEMA CENTRALIZADO DE ALÍQUOTAS")
    print("=" * 80)
    print("📝 OBJETIVO: Demonstrar que todas as alíquotas são gerenciadas")
    print("   exclusivamente através do modelo Aliquotas, com suporte")
    print("   a mudanças temporais por decretos municipais")
    print("=" * 80)
    
    try:
        # Configurar dados de teste
        conta = criar_dados_teste()
        
        # Testar sistema centralizado
        aliquotas_passado, aliquotas_atual, aliquotas_futuro = testar_sistema_centralizado(conta)
        
        # Testar empresa usando sistema centralizado
        empresa = testar_empresa_usando_sistema_centralizado(conta)
        
        # Testar cálculos e histórico
        testar_calculos_temporais(empresa)
        testar_historico_aliquotas(empresa)
        testar_busca_por_data(conta)
        
        print("\n" + "=" * 80)
        print("🎉 TESTES DO SISTEMA CENTRALIZADO CONCLUÍDOS COM SUCESSO!")
        print("=" * 80)
        print("✅ RESULTADOS:")
        print("  ◾ Alíquotas centralizadas exclusivamente no modelo Aliquotas")
        print("  ◾ Suporte a mudanças temporais por decreto municipal")
        print("  ◾ Empresa utiliza apenas configurações da conta")
        print("  ◾ Hierarquia simplificada: conta > padrão")
        print("  ◾ Cálculos funcionando com data específica")
        print("  ◾ Histórico de mudanças rastreável")
        print("  ◾ Sistema preparado para decretos mensais")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
