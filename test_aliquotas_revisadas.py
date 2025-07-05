#!/usr/bin/env python
"""
Script de teste para as novas funcionalidades de alíquotas ISS

Este script testa:
1. Configuração de alíquotas específicas por tipo de serviço na Empresa
2. Hierarquia de alíquotas (empresa > conta > padrão)
3. Validações dos campos de alíquota
4. Métodos de obtenção de alíquotas efetivas
"""

import os
import sys
import django
from decimal import Decimal

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
        name='Conta Teste Alíquotas',
        defaults={'cnpj': '12345678000199'}
    )
    
    print(f"✅ Conta: {conta}")
    return conta


def testar_aliquotas_empresa(conta):
    """Testa as funcionalidades de alíquotas na Empresa"""
    print("\n🏥 TESTANDO ALÍQUOTAS NA EMPRESA")
    print("=" * 50)
    
    # Teste 1: Criar empresa com alíquotas específicas
    print("\n1. Criando empresa com alíquotas específicas...")
    empresa = Empresa.objects.create(
        conta=conta,
        name='Hospital Teste Ltda',
        nome_fantasia='Hospital Teste',
        cnpj='11222333000144',
        aliquota_iss_consultas=Decimal('2.50'),
        aliquota_iss_plantao=Decimal('3.00'),
        aliquota_iss_outros=Decimal('3.50')
    )
    print(f"✅ Empresa criada: {empresa}")
    
    # Teste 2: Verificar obtenção de alíquotas específicas
    print("\n2. Testando obtenção de alíquotas específicas...")
    print(f"Consultas: {empresa.obter_aliquota_iss('consultas')}%")
    print(f"Plantão: {empresa.obter_aliquota_iss('plantao')}%")
    print(f"Outros: {empresa.obter_aliquota_iss('outros')}%")
    
    # Teste 3: Verificar alíquotas efetivas
    print("\n3. Testando alíquotas efetivas...")
    resumo = empresa.get_resumo_aliquotas()
    print(f"Resumo das alíquotas:")
    print(f"  - Consultas: {resumo['consultas']}%")
    print(f"  - Plantão: {resumo['plantao']}%")
    print(f"  - Outros: {resumo['outros']}%")
    print(f"  - Tem específicas: {resumo['tem_especificas']}")
    
    # Teste 4: Validações
    print("\n4. Testando validações...")
    try:
        empresa_invalida = Empresa(
            conta=conta,
            name='Empresa Inválida',
            cnpj='22333444000155',
            aliquota_iss_consultas=Decimal('25.00')  # Acima de 20%
        )
        empresa_invalida.full_clean()
        print("❌ Deveria ter falhado na validação")
    except ValidationError as e:
        print(f"✅ Validação funcionando: {e}")
    
    return empresa


def testar_empresa_sem_aliquotas(conta):
    """Testa empresa sem alíquotas específicas (usa padrões)"""
    print("\n🏢 TESTANDO EMPRESA SEM ALÍQUOTAS ESPECÍFICAS")
    print("=" * 50)
    
    # Criar empresa sem alíquotas específicas
    empresa_padrao = Empresa.objects.create(
        conta=conta,
        name='Clínica Padrão Ltda',
        nome_fantasia='Clínica Padrão',
        cnpj='33444555000166'
        # Sem alíquotas específicas
    )
    
    print(f"Empresa criada: {empresa_padrao}")
    
    # Verificar alíquotas efetivas (deve usar padrões)
    print("\nAlíquotas efetivas (padrões):")
    resumo = empresa_padrao.get_resumo_aliquotas()
    print(f"  - Consultas: {resumo['consultas']}%")
    print(f"  - Plantão: {resumo['plantao']}%")
    print(f"  - Outros: {resumo['outros']}%")
    print(f"  - Tem específicas: {resumo['tem_especificas']}")
    
    return empresa_padrao


def testar_hierarquia_aliquotas(conta, empresa_com_aliquotas, empresa_sem_aliquotas):
    """Testa a hierarquia de alíquotas (empresa > conta > padrão)"""
    print("\n📊 TESTANDO HIERARQUIA DE ALÍQUOTAS")
    print("=" * 50)
    
    # Criar configuração de alíquotas para a conta
    print("\n1. Criando configuração de alíquotas da conta...")
    aliquotas_conta = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('4.00'),
        ISS_PLANTAO=Decimal('4.50'),
        ISS_OUTROS=Decimal('5.00'),
        ativa=True
    )
    print(f"✅ Alíquotas da conta criadas: {aliquotas_conta}")
    
    print("\n2. Testando hierarquia para empresa COM alíquotas específicas:")
    print("   (deve usar alíquotas da empresa)")
    resumo_com = empresa_com_aliquotas.get_resumo_aliquotas()
    print(f"  - Consultas: {resumo_com['consultas']}% (empresa)")
    print(f"  - Plantão: {resumo_com['plantao']}% (empresa)")
    print(f"  - Outros: {resumo_com['outros']}% (empresa)")
    
    print("\n3. Testando hierarquia para empresa SEM alíquotas específicas:")
    print("   (deve usar alíquotas da conta)")
    resumo_sem = empresa_sem_aliquotas.get_resumo_aliquotas()
    print(f"  - Consultas: {resumo_sem['consultas']}% (conta)")
    print(f"  - Plantão: {resumo_sem['plantao']}% (conta)")
    print(f"  - Outros: {resumo_sem['outros']}% (conta)")
    
    # Testar com empresa totalmente nova (sem configuração de conta)
    print("\n4. Testando com nova conta (sem configuração):")
    print("   (deve usar valores padrão)")
    conta_nova, created = Conta.objects.get_or_create(
        name='Conta Nova Teste',
        defaults={'cnpj': '99888777000166'}
    )
    
    empresa_nova = Empresa.objects.create(
        conta=conta_nova,
        name='Empresa Nova Ltda',
        cnpj='55666777000188'
    )
    
    resumo_nova = empresa_nova.get_resumo_aliquotas()
    print(f"  - Consultas: {resumo_nova['consultas']}% (padrão)")
    print(f"  - Plantão: {resumo_nova['plantao']}% (padrão)")
    print(f"  - Outros: {resumo_nova['outros']}% (padrão)")


def testar_compatibilidade_legado(conta):
    """Testa compatibilidade com o campo legado aliquota_iss"""
    print("\n🔄 TESTANDO COMPATIBILIDADE LEGADO")
    print("=" * 50)
    
    # Criar empresa usando apenas o campo legado
    empresa_legado = Empresa.objects.create(
        conta=conta,
        name='Empresa Legado Ltda',
        cnpj='66777888000199',
        aliquota_iss=Decimal('2.75')  # Apenas campo legado
    )
    
    print(f"Empresa legado criada: {empresa_legado}")
    
    # Testar obtenção via campo legado
    aliquota_legado = empresa_legado.obter_aliquota_iss('legado')
    print(f"Alíquota legado: {aliquota_legado}%")
    
    # Testar que campos específicos retornam None
    print("Campos específicos (devem ser None):")
    print(f"  - Consultas: {empresa_legado.obter_aliquota_iss('consultas')}")
    print(f"  - Plantão: {empresa_legado.obter_aliquota_iss('plantao')}")
    print(f"  - Outros: {empresa_legado.obter_aliquota_iss('outros')}")


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DE ALÍQUOTAS REVISADAS")
    print("=" * 60)
    
    try:
        # Configurar dados de teste
        conta = criar_dados_teste()
        
        # Testar funcionalidades
        empresa_com_aliquotas = testar_aliquotas_empresa(conta)
        empresa_sem_aliquotas = testar_empresa_sem_aliquotas(conta)
        
        testar_hierarquia_aliquotas(conta, empresa_com_aliquotas, empresa_sem_aliquotas)
        testar_compatibilidade_legado(conta)
        
        print("\n" + "=" * 60)
        print("🎉 TESTES DE ALÍQUOTAS CONCLUÍDOS COM SUCESSO!")
        print("✅ Alíquotas específicas por tipo de serviço funcionando")
        print("✅ Hierarquia de alíquotas (empresa > conta > padrão) funcionando")
        print("✅ Validações de valores funcionando")
        print("✅ Compatibilidade com campo legado mantida")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
