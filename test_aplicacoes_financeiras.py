"""
Testes para o modelo simplificado de Aplicações Financeiras

Este arquivo testa o modelo AplicacaoFinanceira que controla rendimentos mensais
de aplicações financeiras e sua integração com o sistema tributário.
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from medicos.models.base import Conta, Empresa
from medicos.models.financeiro import AplicacaoFinanceira, CategoriaMovimentacao


class TestAplicacaoFinanceiraSimplificada(TestCase):
    """Testes para o modelo simplificado de aplicações financeiras"""
    
    def setUp(self):
        """Configura dados de teste"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.conta = Conta.objects.create(
            name='Conta Teste',
            owner=self.user,
            created_by=self.user
        )
        
        self.banco = Empresa.objects.create(
            conta=self.conta,
            nome_fantasia='Banco Teste',
            razao_social='Banco Teste S.A.',
            cnpj='12.345.678/0001-90',
            tipo_pessoa='juridica'
        )
    
    def test_criacao_aplicacao_basica(self):
        """Testa criação básica de aplicação financeira"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('1500.00'),
            irrf=Decimal('225.00'),  # 15%
            descricao='CDB 12 meses'
        )
        
        self.assertEqual(aplicacao.rendimentos, Decimal('1500.00'))
        self.assertEqual(aplicacao.irrf, Decimal('225.00'))
        self.assertEqual(aplicacao.rendimento_liquido, Decimal('1275.00'))
        self.assertEqual(aplicacao.aliquota_efetiva, 15.0)
    
    def test_calculo_automatico_irrf(self):
        """Testa cálculo automático de IRRF para valores acima de R$ 1.000"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('2000.00'),
            # IRRF não informado - deve ser calculado automaticamente
            descricao='LCI'
        )
        
        # Deve aplicar 15% automaticamente
        self.assertEqual(aplicacao.irrf, Decimal('300.00'))
        self.assertEqual(aplicacao.rendimento_liquido, Decimal('1700.00'))
    
    def test_sem_irrf_valores_baixos(self):
        """Testa que valores baixos não têm IRRF automático"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('500.00'),
            descricao='Poupança'
        )
        
        # Não deve ter IRRF automático para valores baixos
        self.assertEqual(aplicacao.irrf, Decimal('0.00'))
        self.assertEqual(aplicacao.rendimento_liquido, Decimal('500.00'))
    
    def test_validacoes_negativas(self):
        """Testa validações para valores inválidos"""
        # Rendimentos negativos
        with self.assertRaises(ValidationError):
            aplicacao = AplicacaoFinanceira(
                conta=self.conta,
                fornecedor=self.banco,
                data=date(2025, 1, 1),
                rendimentos=Decimal('-100.00')
            )
            aplicacao.clean()
        
        # IRRF maior que rendimentos
        with self.assertRaises(ValidationError):
            aplicacao = AplicacaoFinanceira(
                conta=self.conta,
                fornecedor=self.banco,
                data=date(2025, 1, 1),
                rendimentos=Decimal('1000.00'),
                irrf=Decimal('1500.00')
            )
            aplicacao.clean()
    
    def test_gerar_lancamentos_financeiros(self):
        """Testa geração de informações para lançamentos financeiros"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('2000.00'),
            irrf=Decimal('300.00'),
            descricao='CDB 12 meses'
        )
        
        info_lancamentos = aplicacao.gerar_lancamentos_financeiros()
        
        self.assertEqual(info_lancamentos['rendimentos'], Decimal('2000.00'))
        self.assertEqual(info_lancamentos['irrf'], Decimal('300.00'))
        self.assertEqual(info_lancamentos['rendimento_liquido'], Decimal('1700.00'))
        self.assertEqual(len(info_lancamentos['lancamentos']), 2)  # Crédito e débito
        
        # Verificar lançamento de rendimento (crédito)
        credito = info_lancamentos['lancamentos'][0]
        self.assertEqual(credito['tipo'], 'credito')
        self.assertEqual(credito['valor'], Decimal('2000.00'))
        self.assertEqual(credito['categoria'], 'rendimento_aplicacao')
        
        # Verificar lançamento de IRRF (débito)
        debito = info_lancamentos['lancamentos'][1]
        self.assertEqual(debito['tipo'], 'debito')
        self.assertEqual(debito['valor'], Decimal('300.00'))
        self.assertEqual(debito['categoria'], 'irrf_aplicacao')
    
    def test_calcular_ir_devido_empresa(self):
        """Testa cálculo de IR devido pela empresa"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('5000.00'),
            irrf=Decimal('750.00'),
            descricao='CDB 24 meses'
        )
        
        ir_info = aplicacao.calcular_ir_devido_empresa()
        
        self.assertEqual(ir_info['rendimento_bruto'], Decimal('5000.00'))
        self.assertEqual(ir_info['irrf_retido'], Decimal('750.00'))
        self.assertEqual(ir_info['rendimento_liquido'], Decimal('4250.00'))
        self.assertEqual(ir_info['base_calculo_irpj'], Decimal('5000.00'))
        self.assertEqual(ir_info['irrf_compensavel'], Decimal('750.00'))
        self.assertIn('integra base de cálculo IRPJ/CSLL', ir_info['observacoes'])
    
    def test_resumo_periodo(self):
        """Testa geração de resumo para um período"""
        # Criar múltiplas aplicações
        AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('1000.00'),
            irrf=Decimal('150.00')
        )
        
        AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 2, 1),
            rendimentos=Decimal('1200.00'),
            irrf=Decimal('180.00')
        )
        
        AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 3, 1),
            rendimentos=Decimal('800.00'),
            irrf=Decimal('120.00')
        )
        
        # Obter resumo do trimestre
        resumo = AplicacaoFinanceira.obter_resumo_periodo(
            self.conta,
            date(2025, 1, 1),
            date(2025, 3, 31)
        )
        
        self.assertEqual(resumo['total_rendimentos'], Decimal('3000.00'))
        self.assertEqual(resumo['total_irrf'], Decimal('450.00'))
        self.assertEqual(resumo['rendimento_liquido'], Decimal('2550.00'))
        self.assertEqual(resumo['count_aplicacoes'], 3)
    
    def test_str_representation(self):
        """Testa representação string do modelo"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('1500.00'),
            irrf=Decimal('225.00')
        )
        
        expected = f"{self.banco.nome_fantasia} - 01/2025 - R$ 1.500,00"
        self.assertEqual(str(aplicacao), expected)
    
    def test_criacao_categorias_automaticas(self):
        """Testa criação automática de categorias ao gerar lançamentos"""
        aplicacao = AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 1),
            rendimentos=Decimal('1000.00'),
            irrf=Decimal('150.00')
        )
        
        # Antes de gerar lançamentos, não devem existir categorias
        self.assertFalse(
            CategoriaMovimentacao.objects.filter(
                conta=self.conta,
                codigo='rendimento_aplicacao'
            ).exists()
        )
        
        # Gerar lançamentos deve criar as categorias
        aplicacao.gerar_lancamentos_financeiros()
        
        # Verificar se categorias foram criadas
        categoria_rendimento = CategoriaMovimentacao.objects.get(
            conta=self.conta,
            codigo='rendimento_aplicacao'
        )
        categoria_irrf = CategoriaMovimentacao.objects.get(
            conta=self.conta,
            codigo='irrf_aplicacao'
        )
        
        self.assertEqual(categoria_rendimento.natureza, 'receita')
        self.assertEqual(categoria_irrf.natureza, 'despesa')
        self.assertTrue(categoria_rendimento.ativo)
        self.assertTrue(categoria_irrf.ativo)


class TestIntegracaoAplicacaoFinanceira(TestCase):
    """Testes de integração das aplicações financeiras com outros sistemas"""
    
    def setUp(self):
        """Configura dados de teste"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.conta = Conta.objects.create(
            name='Conta Teste',
            owner=self.user,
            created_by=self.user
        )
        
        self.banco = Empresa.objects.create(
            conta=self.conta,
            nome_fantasia='Banco XYZ',
            razao_social='Banco XYZ S.A.',
            cnpj='98.765.432/0001-10',
            tipo_pessoa='juridica'
        )
    
    def test_integracao_relatorio_consolidado(self):
        """Testa integração com relatórios consolidados"""
        from medicos.models.relatorios import RelatorioConsolidadoMensal
        
        # Criar aplicações do mês
        AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 15),
            rendimentos=Decimal('2000.00'),
            irrf=Decimal('300.00')
        )
        
        AplicacaoFinanceira.objects.create(
            conta=self.conta,
            fornecedor=self.banco,
            data=date(2025, 1, 20),
            rendimentos=Decimal('1500.00'),
            irrf=Decimal('225.00')
        )
        
        # Criar relatório
        relatorio = RelatorioConsolidadoMensal.objects.create(
            conta=self.conta,
            mes_referencia=date(2025, 1, 1),
            gerado_por=self.user
        )
        
        # Incluir dados de aplicações
        totais = relatorio.incluir_dados_aplicacoes_financeiras()
        
        self.assertEqual(totais['total_rendimentos'], Decimal('3500.00'))
        self.assertEqual(totais['total_irrf'], Decimal('525.00'))
        self.assertEqual(totais['count_aplicacoes'], 2)
        
        # Verificar se foram adicionados aos campos do relatório
        self.assertEqual(relatorio.creditos_financeiro, Decimal('3500.00'))
        self.assertEqual(relatorio.debitos_financeiro, Decimal('525.00'))
        
        # Verificar observações
        self.assertIn('Aplicações Financeiras', relatorio.observacoes)
        self.assertIn('R$ 3.500,00', relatorio.observacoes)
        self.assertIn('R$ 525,00', relatorio.observacoes)


if __name__ == '__main__':
    unittest.main()
