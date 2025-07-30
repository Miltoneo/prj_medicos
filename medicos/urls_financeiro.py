from django.urls import path
from .views_descricao_movimentacao import (
    DescricaoMovimentacaoFinanceiraListView,
    DescricaoMovimentacaoFinanceiraCreateView,
    DescricaoMovimentacaoFinanceiraUpdateView,
    DescricaoMovimentacaoFinanceiraDeleteView,
)

app_name = 'financeiro'

urlpatterns = [
    path('empresas/<int:empresa_id>/descricoes-movimentacao/', DescricaoMovimentacaoFinanceiraListView.as_view(), name='lista_descricoes_movimentacao'),
    path('empresas/<int:empresa_id>/descricoes-movimentacao/novo/', DescricaoMovimentacaoFinanceiraCreateView.as_view(), name='descricao_movimentacao_create'),
    path('empresas/<int:empresa_id>/descricoes-movimentacao/<int:pk>/editar/', DescricaoMovimentacaoFinanceiraUpdateView.as_view(), name='descricao_movimentacao_edit'),
    path('empresas/<int:empresa_id>/descricoes-movimentacao/<int:pk>/excluir/', DescricaoMovimentacaoFinanceiraDeleteView.as_view(), name='descricao_movimentacao_delete'),

    # Financeiro Movimentação CRUD
    path('empresas/<int:empresa_id>/lancamentos/novo/',
         __import__('medicos.views_financeiro_lancamentos').views_financeiro_lancamentos.FinanceiroCreateView.as_view(),
         name='financeiro_create'),
    path('empresas/<int:empresa_id>/lancamentos/<int:pk>/editar/',
         __import__('medicos.views_financeiro_lancamentos').views_financeiro_lancamentos.FinanceiroUpdateView.as_view(),
         name='financeiro_edit'),
    path('empresas/<int:empresa_id>/lancamentos/<int:pk>/excluir/',
         __import__('medicos.views_financeiro_lancamentos').views_financeiro_lancamentos.FinanceiroDeleteView.as_view(),
         name='financeiro_delete'),
    path('empresas/<int:empresa_id>/lancamentos/',
         __import__('medicos.views_financeiro_lancamentos').views_financeiro_lancamentos.FinanceiroListView.as_view(),
         name='lancamentos'),
]
