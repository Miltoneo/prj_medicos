from django.urls import path
from . import views_contacorrente

urlpatterns = [
    # =====================
    # Conta Corrente Views
    # =====================
    path('empresas/<int:empresa_id>/lancamentos/', views_contacorrente.MovimentacaoContaCorrenteListView.as_view(), name='contacorrente_lancamentos'),
    path('empresas/<int:empresa_id>/lancamentos/novo/', views_contacorrente.MovimentacaoContaCorrenteCreateView.as_view(), name='contacorrente_create'),
    path('empresas/<int:empresa_id>/lancamentos/<int:pk>/editar/', views_contacorrente.MovimentacaoContaCorrenteUpdateView.as_view(), name='contacorrente_edit'),
    path('empresas/<int:empresa_id>/lancamentos/<int:pk>/excluir/', views_contacorrente.MovimentacaoContaCorrenteDeleteView.as_view(), name='contacorrente_delete'),
]
