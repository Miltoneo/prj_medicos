
from django.urls import path
from . import views_despesas

urlpatterns = [
    path('lista_consolidado_despesas/<int:empresa_id>/', views_despesas.ConsolidadoDespesasView.as_view(), name='lista_consolidado_despesas'),
    path('lista_despesas_empresa/<int:empresa_id>/', views_despesas.ListaDespesasEmpresaView.as_view(), name='lista_despesas_empresa'),
    path('nova_despesa_empresa/<int:empresa_id>/', views_despesas.NovaDespesaEmpresaView.as_view(), name='nova_despesa_empresa'),
    path('editar_despesa_empresa/<int:empresa_id>/<int:pk>/', views_despesas.EditarDespesaEmpresaView.as_view(), name='editar_despesa_empresa'),
    path('excluir_despesa_empresa/<int:empresa_id>/<int:pk>/', views_despesas.ExcluirDespesaEmpresaView.as_view(), name='excluir_despesa_empresa'),
    path('lista_despesas_socio/<int:empresa_id>/', views_despesas.ListaDespesasSocioView.as_view(), name='lista_despesas_socio'),
]
