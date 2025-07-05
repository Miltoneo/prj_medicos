#!/usr/bin/env python3
"""
Teste completo para verificar funcionalidade do Django Admin e Formulários
com o novo sistema de alíquotas diferenciadas por tipo de serviço médico.
"""

import os
import django
import sys
from decimal import Decimal
from datetime import date, datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from medicos.models import *
from medicos.admin import *
from medicos.forms import *

User = get_user_model()

def test_admin_configuration():
    """Testa se o admin foi configurado corretamente para o novo sistema."""
    print("\n=== TESTE: Configuração do Django Admin ===")
    
    # Verifica se os modelos estão registrados no admin
    from django.contrib import admin
    
    registered_models = [
        Pessoa, Empresa, Socio, NotaFiscal, Aliquotas, Despesa
    ]
    
    for model in registered_models:
        if model in admin.site._registry:
            admin_class = admin.site._registry[model]
            print(f"✓ {model.__name__} registrado no admin com classe {admin_class.__class__.__name__}")
        else:
            print(f"✗ {model.__name__} NÃO registrado no admin")
    
    # Testa configuração específica do NotaFiscalAdmin
    if NotaFiscal in admin.site._registry:
        nf_admin = admin.site._registry[NotaFiscal]
        
        # Verifica se tipo_aliquota está nos fieldsets
        fieldset_fields = []
        for fieldset in nf_admin.fieldsets:
            fieldset_fields.extend(fieldset[1]['fields'])
        
        if 'tipo_aliquota' in fieldset_fields:
            print("✓ Campo tipo_aliquota presente nos fieldsets do NotaFiscalAdmin")
        else:
            print("✗ Campo tipo_aliquota AUSENTE dos fieldsets do NotaFiscalAdmin")
        
        # Verifica se método personalizado existe
        if hasattr(nf_admin, 'get_tipo_aliquota_display'):
            print("✓ Método get_tipo_aliquota_display definido no NotaFiscalAdmin")
        else:
            print("✗ Método get_tipo_aliquota_display AUSENTE no NotaFiscalAdmin")

def test_aliquotas_form():
    """Testa o formulário de alíquotas com os novos campos."""
    print("\n=== TESTE: Formulário de Alíquotas ===")
    
    try:
        # Cria dados de teste
        conta_data = {
            'name': 'Empresa Teste Admin',
            'CNPJ': '12345678000199',
            'email': 'admin@teste.com',
            'endereco': 'Rua Teste, 123'
        }
        conta, created = Empresa.objects.get_or_create(
            CNPJ=conta_data['CNPJ'],
            defaults=conta_data
        )
        
        # Dados do formulário
        form_data = {
            'conta': conta.id,
            'ISS_CONSULTAS': '5.00',
            'ISS_PLANTAO': '3.00', 
            'ISS_OUTROS': '4.00',
            'PIS': '0.65',
            'COFINS': '3.00',
            'IR': '1.50',
            'CSLL': '1.00',
            'data_vigencia_inicio': '2025-01-01',
            'data_vigencia_fim': '2025-12-31',
            'observacoes': 'Teste admin forms'
        }
        
        # Testa formulário
        form = AliquotasForm(data=form_data)
        
        if form.is_valid():
            print("✓ AliquotasForm válido com os novos campos")
            aliquota = form.save()
            print(f"✓ Alíquota salva com ID: {aliquota.id}")
            
            # Verifica se os valores foram salvos corretamente
            assert aliquota.ISS_CONSULTAS == Decimal('5.00')
            assert aliquota.ISS_PLANTAO == Decimal('3.00')
            assert aliquota.ISS_OUTROS == Decimal('4.00')
            print("✓ Valores de ISS diferenciados salvos corretamente")
            
        else:
            print(f"✗ AliquotasForm inválido: {form.errors}")
            
    except Exception as e:
        print(f"✗ Erro no teste do formulário: {e}")

def test_nota_fiscal_form():
    """Testa o formulário de Nota Fiscal com tipo de serviço obrigatório."""
    print("\n=== TESTE: Formulário de Nota Fiscal ===")
    
    try:
        # Cria dados necessários
        empresa_data = {
            'name': 'Empresa NF Teste',
            'CNPJ': '98765432000188',
            'email': 'nf@teste.com',
            'endereco': 'Rua NF, 456'
        }
        empresa, created = Empresa.objects.get_or_create(
            CNPJ=empresa_data['CNPJ'],
            defaults=empresa_data
        )
        
        pessoa_data = {
            'name': 'Dr. João Silva',
            'CPF': '12345678901',
            'email': 'joao@teste.com',
            'endereco': 'Rua Médico, 789'
        }
        pessoa, created = Pessoa.objects.get_or_create(
            CPF=pessoa_data['CPF'],
            defaults=pessoa_data
        )
        
        socio, created = Socio.objects.get_or_create(
            pessoa=pessoa,
            empresa=empresa,
            defaults={'percentual': Decimal('100.00')}
        )
        
        # Teste com tipo_aliquota definido
        form_data = {
            'numero': 'NF-001-TEST',
            'tomador': 'Paciente Teste',
            'socio': socio.id,
            'tipo_aliquota': 'consultas',
            'dtEmissao': '2025-07-01',
            'val_bruto': '1000.00',
            'val_ISS': '50.00',
            'val_PIS': '6.50',
            'val_COFINS': '30.00',
            'val_IR': '15.00',
            'val_CSLL': '10.00',
            'val_liquido': '878.50'
        }
        
        form = Edit_NotaFiscal_Form(data=form_data, socio_choices=[(socio.id, socio.pessoa.name)])
        
        if form.is_valid():
            print("✓ Edit_NotaFiscal_Form válido com tipo_aliquota")
            nf = form.save(commit=False)
            nf.fornecedor = empresa
            nf.save()
            print(f"✓ Nota Fiscal salva com tipo: {nf.get_tipo_aliquota_display()}")
            
        else:
            print(f"✗ Edit_NotaFiscal_Form inválido: {form.errors}")
        
        # Teste sem tipo_aliquota (deve falhar)
        form_data_sem_tipo = form_data.copy()
        del form_data_sem_tipo['tipo_aliquota']
        
        form_sem_tipo = Edit_NotaFiscal_Form(data=form_data_sem_tipo, socio_choices=[(socio.id, socio.pessoa.name)])
        
        if not form_sem_tipo.is_valid():
            print("✓ Formulário corretamente inválido sem tipo_aliquota")
        else:
            print("✗ Formulário deveria ser inválido sem tipo_aliquota")
            
    except Exception as e:
        print(f"✗ Erro no teste do formulário de NF: {e}")

def test_service_type_display():
    """Testa os métodos de exibição do tipo de serviço."""
    print("\n=== TESTE: Exibição do Tipo de Serviço ===")
    
    try:
        # Cria dados mínimos para o teste
        empresa_data = {
            'name': 'Empresa Display Teste',
            'CNPJ': '11111111000111',
            'email': 'display@teste.com',
            'endereco': 'Rua Display, 123'
        }
        empresa, created = Empresa.objects.get_or_create(
            CNPJ=empresa_data['CNPJ'],
            defaults=empresa_data
        )
        
        pessoa_data = {
            'name': 'Dr. Maria Santos',
            'CPF': '11111111111',
            'email': 'maria@teste.com',
            'endereco': 'Rua Dra, 456'
        }
        pessoa, created = Pessoa.objects.get_or_create(
            CPF=pessoa_data['CPF'],
            defaults=pessoa_data
        )
        
        socio, created = Socio.objects.get_or_create(
            pessoa=pessoa,
            empresa=empresa,
            defaults={'percentual': Decimal('100.00')}
        )
        
        # Testa cada tipo de serviço
        tipos_servico = [
            ('consultas', 'Consultas Médicas'),
            ('plantao', 'Plantão/Urgência'),
            ('outros', 'Vacinação/Exames/Procedimentos')
        ]
        
        for codigo, descricao_esperada in tipos_servico:
            nf = NotaFiscal.objects.create(
                numero=f'NF-{codigo.upper()}-001',
                fornecedor=empresa,
                tomador='Paciente Teste',
                socio=socio,
                tipo_aliquota=codigo,
                dtEmissao=date.today(),
                val_bruto=Decimal('1000.00'),
                val_liquido=Decimal('900.00')
            )
            
            # Testa método de descrição
            if hasattr(nf, 'get_tipo_aliquota_description'):
                descricao = nf.get_tipo_aliquota_description()
                if descricao == descricao_esperada:
                    print(f"✓ Descrição correta para '{codigo}': {descricao}")
                else:
                    print(f"✗ Descrição incorreta para '{codigo}': esperado '{descricao_esperada}', obtido '{descricao}'")
            
            # Testa método de código
            if hasattr(nf, 'get_tipo_aliquota_code'):
                codigo_obtido = nf.get_tipo_aliquota_code()
                if codigo_obtido == codigo.upper():
                    print(f"✓ Código correto para '{codigo}': {codigo_obtido}")
                else:
                    print(f"✗ Código incorreto para '{codigo}': esperado '{codigo.upper()}', obtido '{codigo_obtido}'")
                    
    except Exception as e:
        print(f"✗ Erro no teste de exibição: {e}")

def test_automatic_tax_calculation():
    """Testa o cálculo automático de impostos baseado no tipo de serviço."""
    print("\n=== TESTE: Cálculo Automático de Impostos ===")
    
    try:
        # Limpa dados de teste anteriores
        Aliquotas.objects.filter(observacoes__contains="TESTE_AUTO_CALC").delete()
        
        # Cria dados de teste
        empresa_data = {
            'name': 'Empresa Calc Teste',
            'CNPJ': '22222222000122',
            'email': 'calc@teste.com',
            'endereco': 'Rua Calc, 789'
        }
        empresa, created = Empresa.objects.get_or_create(
            CNPJ=empresa_data['CNPJ'],
            defaults=empresa_data
        )
        
        # Cria alíquota com ISS diferenciado
        aliquota = Aliquotas.objects.create(
            conta=empresa,
            ISS_CONSULTAS=Decimal('5.00'),  # 5%
            ISS_PLANTAO=Decimal('3.00'),    # 3%
            ISS_OUTROS=Decimal('4.00'),     # 4%
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            IR=Decimal('1.50'),
            CSLL=Decimal('1.00'),
            data_vigencia_inicio=date.today(),
            observacoes="TESTE_AUTO_CALC"
        )
        
        pessoa_data = {
            'name': 'Dr. Pedro Auto',
            'CPF': '22222222222',
            'email': 'pedro@teste.com',
            'endereco': 'Rua Auto, 101'
        }
        pessoa, created = Pessoa.objects.get_or_create(
            CPF=pessoa_data['CPF'],
            defaults=pessoa_data
        )
        
        socio, created = Socio.objects.get_or_create(
            pessoa=pessoa,
            empresa=empresa,
            defaults={'percentual': Decimal('100.00')}
        )
        
        # Testa cálculo para cada tipo de serviço
        valor_bruto = Decimal('1000.00')
        
        tipos_teste = [
            ('consultas', Decimal('50.00')),  # 5% de ISS
            ('plantao', Decimal('30.00')),    # 3% de ISS
            ('outros', Decimal('40.00'))      # 4% de ISS
        ]
        
        for tipo, iss_esperado in tipos_teste:
            nf = NotaFiscal.objects.create(
                numero=f'NF-AUTO-{tipo.upper()}-001',
                fornecedor=empresa,
                tomador='Paciente Auto Teste',
                socio=socio,
                tipo_aliquota=tipo,
                dtEmissao=date.today(),
                val_bruto=valor_bruto,
                val_liquido=valor_bruto  # Será recalculado
            )
            
            # Testa método de cálculo automático se existir
            if hasattr(nf, 'calcular_impostos_automatico'):
                nf.calcular_impostos_automatico()
                
                if nf.val_ISS == iss_esperado:
                    print(f"✓ ISS calculado corretamente para '{tipo}': {nf.val_ISS}")
                else:
                    print(f"✗ ISS incorreto para '{tipo}': esperado {iss_esperado}, obtido {nf.val_ISS}")
            else:
                print(f"• Método calcular_impostos_automatico não implementado")
                
            # Testa aplicação via alíquota
            impostos = aliquota.calcular_impostos_nf(nf)
            if impostos and 'ISS' in impostos:
                iss_calculado = impostos['ISS']
                if iss_calculado == iss_esperado:
                    print(f"✓ Cálculo via Aliquotas.calcular_impostos_nf correto para '{tipo}': {iss_calculado}")
                else:
                    print(f"✗ Cálculo via Aliquotas.calcular_impostos_nf incorreto para '{tipo}': esperado {iss_esperado}, obtido {iss_calculado}")
                    
    except Exception as e:
        print(f"✗ Erro no teste de cálculo automático: {e}")

def main():
    """Executa todos os testes de admin e formulários."""
    print("=" * 80)
    print("TESTE COMPLETO: Django Admin e Formulários")
    print("Sistema de Alíquotas Diferenciadas por Tipo de Serviço Médico")
    print("=" * 80)
    
    test_admin_configuration()
    test_aliquotas_form()
    test_nota_fiscal_form()
    test_service_type_display()
    test_automatic_tax_calculation()
    
    print("\n" + "=" * 80)
    print("TESTE DE ADMIN E FORMULÁRIOS CONCLUÍDO")
    print("=" * 80)

if __name__ == '__main__':
    main()
