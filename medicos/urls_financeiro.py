from django.urls import path
from .views_financeiro import (
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
]
