"""
Testes para verificar que o regime tributário da empresa afeta corretamente
a forma de tributação de impostos e que alterações não afetam períodos passados.
"""

from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from medicos.models.base import Conta, Empresa, REGIME_TRIBUTACAO_COMPETENCIA, REGIME_TRIBUTACAO_CAIXA
from medicos.models.fiscal import Aliquotas, RegimeTributarioHistorico


class TestRegimeTributarioHistorico(TestCase):
    """Testes para o modelo RegimeTributarioHistorico"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.conta = Conta.objects.create(name="Conta Teste", cnpj="12345678000199")
        self.empresa = Empresa.objects.create(
            conta=self.conta,
            name="Empresa Teste Ltda",
            cnpj="98765432000188",
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA
        )
        
        self.aliquotas = Aliquotas.objects.create(
            conta=self.conta,
            ISS_CONSULTAS=Decimal('2.00'),
            ISS_PLANTAO=Decimal('2.50'),
            ISS_OUTROS=Decimal('3.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            data_vigencia_inicio=date.today() - timedelta(days=365)
        )
    
    def test_criar_historico_regime(self):
        """Testa criação de histórico de regime tributário"""
        hoje = date.today()
        
        historico = RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=hoje,
            observacoes="Regime inicial"
        )
        
        self.assertEqual(historico.empresa, self.empresa)
        self.assertEqual(historico.regime_tributario, REGIME_TRIBUTACAO_COMPETENCIA)
        self.assertEqual(historico.data_inicio, hoje)
        self.assertTrue(historico.eh_vigente)
    
    def test_nao_permite_sobreposicao_periodos(self):
        """Testa que não permite sobreposição de períodos"""
        hoje = date.today()
        
        # Criar primeiro regime
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30)
        )
        
        # Tentar criar regime sobreposto deve falhar
        with self.assertRaises(ValidationError):
            historico_sobreposto = RegimeTributarioHistorico(
                empresa=self.empresa,
                regime_tributario=REGIME_TRIBUTACAO_CAIXA,
                data_inicio=hoje + timedelta(days=15),  # Sobrepõe com o anterior
                data_fim=hoje + timedelta(days=45)
            )
            historico_sobreposto.clean()
    
    def test_nao_permite_data_inicio_passado_novo_registro(self):
        """Testa que novos registros não podem ter data de início no passado"""
        ontem = date.today() - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            historico_passado = RegimeTributarioHistorico(
                empresa=self.empresa,
                regime_tributario=REGIME_TRIBUTACAO_CAIXA,
                data_inicio=ontem
            )
            historico_passado.clean()
    
    def test_obter_regime_vigente(self):
        """Testa obtenção do regime vigente em uma data específica"""
        # Criar histórico com três períodos
        data_inicio_1 = date(2024, 1, 1)
        data_fim_1 = date(2024, 6, 30)
        data_inicio_2 = date(2024, 7, 1)
        data_fim_2 = date(2024, 12, 31)
        data_inicio_3 = date(2025, 1, 1)
        
        # Período 1: Competência
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=data_inicio_1,
            data_fim=data_fim_1
        )
        
        # Período 2: Caixa
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_CAIXA,
            data_inicio=data_inicio_2,
            data_fim=data_fim_2
        )
        
        # Período 3: Competência (atual)
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=data_inicio_3
        )
        
        # Testar consultas
        regime_marco = RegimeTributarioHistorico.obter_regime_vigente(self.empresa, date(2024, 3, 15))
        self.assertEqual(regime_marco.regime_tributario, REGIME_TRIBUTACAO_COMPETENCIA)
        
        regime_agosto = RegimeTributarioHistorico.obter_regime_vigente(self.empresa, date(2024, 8, 15))
        self.assertEqual(regime_agosto.regime_tributario, REGIME_TRIBUTACAO_CAIXA)
        
        regime_atual = RegimeTributarioHistorico.obter_regime_vigente(self.empresa, date(2025, 7, 5))
        self.assertEqual(regime_atual.regime_tributario, REGIME_TRIBUTACAO_COMPETENCIA)


class TestCalculoImpostosComRegimeHistorico(TestCase):
    """Testes para cálculo de impostos considerando histórico de regimes"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.conta = Conta.objects.create(name="Conta Teste", cnpj="12345678000199")
        self.empresa = Empresa.objects.create(
            conta=self.conta,
            name="Empresa Teste Ltda",
            cnpj="98765432000188",
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA
        )
        
        self.aliquotas = Aliquotas.objects.create(
            conta=self.conta,
            ISS_CONSULTAS=Decimal('2.00'),
            ISS_PLANTAO=Decimal('2.50'),
            ISS_OUTROS=Decimal('3.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            data_vigencia_inicio=date(2024, 1, 1)
        )
        
        # Criar histórico de regimes
        # 2024: Competência
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=date(2024, 1, 1),
            data_fim=date(2024, 12, 31)
        )
        
        # 2025: Caixa
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_CAIXA,
            data_inicio=date(2025, 1, 1)
        )
    
    def test_calculo_com_regime_passado(self):
        """Testa que cálculo de período passado usa regime vigente na época"""
        valor_bruto = Decimal('1000.00')
        data_2024 = date(2024, 6, 15)
        
        resultado = self.aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_bruto,
            tipo_servico='consultas',
            empresa=self.empresa,
            data_referencia=data_2024
        )
        
        # Deve usar regime de competência (vigente em 2024)
        self.assertEqual(resultado['regime_tributario']['codigo'], REGIME_TRIBUTACAO_COMPETENCIA)
        self.assertEqual(resultado['regime_tributario']['fonte'], 'historico')
        self.assertIn("Competência aplicado", ' '.join(resultado['regime_observacoes']))
    
    def test_calculo_com_regime_atual(self):
        """Testa que cálculo atual usa regime vigente hoje"""
        valor_bruto = Decimal('1000.00')
        data_2025 = date(2025, 7, 5)
        
        resultado = self.aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_bruto,
            tipo_servico='consultas',
            empresa=self.empresa,
            data_referencia=data_2025
        )
        
        # Deve usar regime de caixa (vigente em 2025)
        self.assertEqual(resultado['regime_tributario']['codigo'], REGIME_TRIBUTACAO_CAIXA)
        self.assertEqual(resultado['regime_tributario']['fonte'], 'historico')
        self.assertIn("Caixa aplicado", ' '.join(resultado['regime_observacoes']))
    
    def test_calculo_sem_historico_usa_empresa_atual(self):
        """Testa fallback para regime da empresa quando não há histórico"""
        # Remover histórico
        RegimeTributarioHistorico.objects.filter(empresa=self.empresa).delete()
        
        valor_bruto = Decimal('1000.00')
        
        resultado = self.aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_bruto,
            tipo_servico='consultas',
            empresa=self.empresa
        )
        
        # Deve usar regime atual da empresa com aviso
        self.assertEqual(resultado['regime_tributario']['codigo'], REGIME_TRIBUTACAO_COMPETENCIA)
        self.assertEqual(resultado['regime_tributario']['fonte'], 'empresa_atual')
        self.assertIn("recomenda-se configurar histórico", ' '.join(resultado['regime_tributario']['observacoes']))


class TestAlteracaoRegimeEmpresa(TestCase):
    """Testes para alteração de regime tributário da empresa"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.conta = Conta.objects.create(name="Conta Teste", cnpj="12345678000199")
        self.empresa = Empresa.objects.create(
            conta=self.conta,
            name="Empresa Teste Ltda",
            cnpj="98765432000188",
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA
        )
    
    def test_alteracao_regime_futuro(self):
        """Testa alteração de regime com data futura"""
        amanha = date.today() + timedelta(days=1)
        
        novo_registro = self.empresa.alterar_regime_tributario(
            novo_regime=REGIME_TRIBUTACAO_CAIXA,
            data_inicio=amanha,
            observacoes="Mudança para regime de caixa"
        )
        
        # Verificar que novo registro foi criado
        self.assertEqual(novo_registro.regime_tributario, REGIME_TRIBUTACAO_CAIXA)
        self.assertEqual(novo_registro.data_inicio, amanha)
        
        # Verificar que empresa foi atualizada
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.regime_tributario, REGIME_TRIBUTACAO_CAIXA)
    
    def test_nao_permite_alteracao_passado(self):
        """Testa que não permite alteração com data no passado"""
        ontem = date.today() - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            self.empresa.alterar_regime_tributario(
                novo_regime=REGIME_TRIBUTACAO_CAIXA,
                data_inicio=ontem
            )
    
    def test_obter_regime_vigente_na_data(self):
        """Testa método de obtenção de regime vigente na data"""
        # Criar histórico
        hoje = date.today()
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=hoje
        )
        
        regime_info = self.empresa.obter_regime_vigente_na_data(hoje)
        
        self.assertEqual(regime_info['codigo'], REGIME_TRIBUTACAO_COMPETENCIA)
        self.assertEqual(regime_info['fonte'], 'historico')


class TestIntegracaoRegimeTributacao(TestCase):
    """Testes de integração para verificar o fluxo completo"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.conta = Conta.objects.create(name="Clínica Exemplo", cnpj="12345678000199")
        self.empresa = Empresa.objects.create(
            conta=self.conta,
            name="Clínica Exemplo Ltda",
            cnpj="98765432000188",
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA
        )
        
        self.aliquotas = Aliquotas.objects.create(
            conta=self.conta,
            ISS_CONSULTAS=Decimal('2.00'),
            PIS=Decimal('0.65'),
            COFINS=Decimal('3.00'),
            data_vigencia_inicio=date(2024, 1, 1)
        )
    
    def test_fluxo_completo_mudanca_regime(self):
        """Testa fluxo completo de mudança de regime e impacto nos cálculos"""
        valor_nota = Decimal('1000.00')
        
        # 1. Criar regime inicial (2024 - Competência)
        RegimeTributarioHistorico.objects.create(
            empresa=self.empresa,
            regime_tributario=REGIME_TRIBUTACAO_COMPETENCIA,
            data_inicio=date(2024, 1, 1),
            data_fim=date(2024, 12, 31)
        )
        
        # 2. Calcular impostos para período passado (2024)
        resultado_2024 = self.aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_nota,
            empresa=self.empresa,
            data_referencia=date(2024, 6, 15)
        )
        
        # 3. Alterar regime para 2025 (Caixa)
        self.empresa.alterar_regime_tributario(
            novo_regime=REGIME_TRIBUTACAO_CAIXA,
            data_inicio=date(2025, 1, 1),
            observacoes="Mudança anual para regime de caixa"
        )
        
        # 4. Calcular impostos para período atual (2025)
        resultado_2025 = self.aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_nota,
            empresa=self.empresa,
            data_referencia=date(2025, 7, 5)
        )
        
        # 5. Verificar que período passado não foi afetado
        resultado_2024_apos_mudanca = self.aliquotas.calcular_impostos_com_regime(
            valor_bruto=valor_nota,
            empresa=self.empresa,
            data_referencia=date(2024, 6, 15)
        )
        
        # Verificações
        self.assertEqual(resultado_2024['regime_tributario']['codigo'], REGIME_TRIBUTACAO_COMPETENCIA)
        self.assertEqual(resultado_2025['regime_tributario']['codigo'], REGIME_TRIBUTACAO_CAIXA)
        self.assertEqual(resultado_2024_apos_mudanca['regime_tributario']['codigo'], REGIME_TRIBUTACAO_COMPETENCIA)
        
        # Regime passado permanece inalterado após mudança
        self.assertEqual(
            resultado_2024['regime_tributario']['codigo'],
            resultado_2024_apos_mudanca['regime_tributario']['codigo']
        )
