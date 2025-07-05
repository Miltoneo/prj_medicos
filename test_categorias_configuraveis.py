"""
Testes para a funcionalidade de categorias configuráveis

Este arquivo testa a nova funcionalidade de categorias de movimentação
configuráveis pelos usuários, substituindo as categorias hardcoded.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from medicos.models.base import Conta, Empresa, Socio
from medicos.models.financeiro import CategoriaMovimentacao, DescricaoMovimentacao

User = get_user_model()


class TestCategoriaMovimentacao(TestCase):
    """Testa o modelo CategoriaMovimentacao"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.conta = Conta.objects.create(
            nome='Conta Teste',
            created_by=self.user
        )
    
    def test_criar_categorias_padrao(self):
        """Testa a criação de categorias padrão"""
        categorias = CategoriaMovimentacao.criar_categorias_padrao(self.conta, self.user)
        
        # Verificar se foram criadas
        self.assertGreater(len(categorias), 0)
        
        # Verificar se todas pertencem à conta
        for categoria in categorias:
            self.assertEqual(categoria.conta, self.conta)
            self.assertTrue(categoria.categoria_sistema)
        
        # Verificar categorias específicas
        codigos_esperados = [
            'receita_servicos', 'receita_outros', 'adiantamento_recebido',
            'emprestimo_recebido', 'despesa_operacional', 'despesa_pessoal',
            'transferencia_recebida', 'transferencia_enviada',
            'ajuste_credito', 'ajuste_debito', 'aplicacao_financeira', 'resgate_aplicacao'
        ]
        
        codigos_criados = [cat.codigo for cat in categorias]
        for codigo in codigos_esperados:
            self.assertIn(codigo, codigos_criados)
    
    def test_validacao_codigo_unico(self):
        """Testa validação de código único por conta"""
        # Criar primeira categoria
        cat1 = CategoriaMovimentacao.objects.create(
            conta=self.conta,
            codigo='teste',
            nome='Categoria Teste',
            criada_por=self.user
        )
        
        # Tentar criar segunda categoria com mesmo código
        cat2 = CategoriaMovimentacao(
            conta=self.conta,
            codigo='teste',
            nome='Outra Categoria',
            criada_por=self.user
        )
        
        with self.assertRaises(ValidationError):
            cat2.full_clean()
    
    def test_geracao_codigo_automatico(self):
        """Testa geração automática de código"""
        categoria = CategoriaMovimentacao.objects.create(
            conta=self.conta,
            nome='Categoria Sem Código',
            criada_por=self.user
        )
        
        # Verificar se código foi gerado
        self.assertIsNotNone(categoria.codigo)
        self.assertTrue(len(categoria.codigo) > 0)
    
    def test_propriedades_categoria(self):
        """Testa propriedades da categoria"""
        categoria = CategoriaMovimentacao.objects.create(
            conta=self.conta,
            codigo='teste',
            nome='Categoria Teste',
            natureza='receita',
            cor='#28a745',
            criada_por=self.user
        )
        
        # Testar propriedades
        self.assertEqual(categoria.nome_completo, '[Receita] Categoria Teste')
        self.assertEqual(categoria.cor_css, '#28a745')
        self.assertTrue(categoria.pode_ser_usada_para(1))  # CREDITO
    
    def test_validacao_limites(self):
        """Testa validações de limites"""
        categoria = CategoriaMovimentacao(
            conta=self.conta,
            codigo='teste',
            nome='Categoria Teste',
            percentual_retencao_ir_padrao=150,  # Inválido: > 100%
            criada_por=self.user
        )
        
        with self.assertRaises(ValidationError):
            categoria.full_clean()


class TestDescricaoMovimentacaoRefatorada(TestCase):
    """Testa o modelo DescricaoMovimentacao refatorado"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.conta = Conta.objects.create(
            nome='Conta Teste',
            created_by=self.user
        )
        
        # Criar categorias padrão
        CategoriaMovimentacao.criar_categorias_padrao(self.conta, self.user)
        
        self.categoria_receita = CategoriaMovimentacao.objects.get(
            conta=self.conta,
            codigo='receita_servicos'
        )
    
    def test_criar_descricoes_padrao(self):
        """Testa criação de descrições padrão com novo sistema"""
        descricoes = DescricaoMovimentacao.criar_descricoes_padrao(self.conta, self.user)
        
        # Verificar se foram criadas
        self.assertGreater(len(descricoes), 0)
        
        # Verificar se todas têm categoria_movimentacao
        for desc in descricoes:
            self.assertIsNotNone(desc.categoria_movimentacao)
            self.assertEqual(desc.conta, self.conta)
    
    def test_propriedade_categoria_compatibilidade(self):
        """Testa propriedade categoria para compatibilidade"""
        descricao = DescricaoMovimentacao.objects.create(
            conta=self.conta,
            nome='Teste Descrição',
            categoria_movimentacao=self.categoria_receita,
            criada_por=self.user
        )
        
        # Verificar propriedade de compatibilidade
        self.assertEqual(descricao.categoria, 'receita_servicos')
        self.assertEqual(descricao.categoria_display, 'Receita de Serviços')
    
    def test_metodos_de_busca_atualizados(self):
        """Testa métodos de busca com nova estrutura"""
        # Criar descrição de teste
        descricao = DescricaoMovimentacao.objects.create(
            conta=self.conta,
            nome='Teste Descrição',
            categoria_movimentacao=self.categoria_receita,
            tipo_movimentacao='credito',
            criada_por=self.user
        )
        
        # Testar métodos de busca
        ativas = DescricaoMovimentacao.obter_ativas(self.conta)
        self.assertIn(descricao, ativas)
        
        creditos = DescricaoMovimentacao.obter_creditos(self.conta)
        self.assertIn(descricao, creditos)
        
        por_categoria = DescricaoMovimentacao.obter_por_categoria(
            self.conta, 
            self.categoria_receita
        )
        self.assertIn(descricao, por_categoria)


class TestIntegracaoCompleta(TestCase):
    """Testa a integração completa do sistema refatorado"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.conta = Conta.objects.create(
            nome='Conta Teste',
            created_by=self.user
        )
    
    def test_fluxo_completo_nova_conta(self):
        """Testa fluxo completo para uma nova conta"""
        # 1. Criar categorias padrão
        categorias = CategoriaMovimentacao.criar_categorias_padrao(self.conta, self.user)
        self.assertGreater(len(categorias), 0)
        
        # 2. Criar descrições padrão
        descricoes = DescricaoMovimentacao.criar_descricoes_padrao(self.conta, self.user)
        self.assertGreater(len(descricoes), 0)
        
        # 3. Verificar relacionamentos
        for descricao in descricoes:
            self.assertIsNotNone(descricao.categoria_movimentacao)
            self.assertEqual(descricao.conta, self.conta)
            self.assertTrue(descricao.categoria_movimentacao.conta, self.conta)
        
        # 4. Verificar compatibilidade
        primeira_descricao = descricoes[0]
        categoria_codigo = primeira_descricao.categoria
        self.assertIsNotNone(categoria_codigo)
        self.assertIsInstance(categoria_codigo, str)
    
    def test_criacao_categoria_personalizada(self):
        """Testa criação de categoria personalizada pelo usuário"""
        categoria_custom = CategoriaMovimentacao.objects.create(
            conta=self.conta,
            codigo='receita_custom',
            nome='Receita Personalizada',
            natureza='receita',
            tipo_movimentacao='credito',
            cor='#ff6b6b',
            icone='fas fa-star',
            ordem=999,
            criada_por=self.user
        )
        
        # Criar descrição usando categoria personalizada
        descricao_custom = DescricaoMovimentacao.objects.create(
            conta=self.conta,
            nome='Descrição Personalizada',
            categoria_movimentacao=categoria_custom,
            tipo_movimentacao='credito',
            criada_por=self.user
        )
        
        # Verificar funcionamento
        self.assertEqual(descricao_custom.categoria, 'receita_custom')
        self.assertEqual(descricao_custom.categoria_display, 'Receita Personalizada')
        self.assertIn('Receita Personalizada', descricao_custom.nome_completo)
    
    def test_edicao_categoria_existente(self):
        """Testa edição de categoria existente"""
        # Criar categorias padrão
        CategoriaMovimentacao.criar_categorias_padrao(self.conta, self.user)
        
        # Obter categoria para editar
        categoria = CategoriaMovimentacao.objects.get(
            conta=self.conta,
            codigo='receita_servicos'
        )
        
        # Editar categoria
        categoria.nome = 'Receita de Serviços Médicos Especializados'
        categoria.cor = '#0066cc'
        categoria.ordem = 5
        categoria.save()
        
        # Verificar alterações
        categoria.refresh_from_db()
        self.assertEqual(categoria.nome, 'Receita de Serviços Médicos Especializados')
        self.assertEqual(categoria.cor, '#0066cc')
        self.assertEqual(categoria.ordem, 5)


if __name__ == '__main__':
    pytest.main([__file__])
