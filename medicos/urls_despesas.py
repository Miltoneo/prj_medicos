from django.urls import path
from . import views_despesas

urlpatterns = [
    path('consolidado/<int:empresa_id>/', views_despesas.ConsolidadoDespesasView.as_view(), name='consolidado_despesas'),
    path('empresa/<int:empresa_id>/', views_despesas.ListaDespesasEmpresaView.as_view(), name='lista_despesas_empresa'),
    path('socio/<int:empresa_id>/', views_despesas.ListaDespesasSocioView.as_view(), name='lista_despesas_socio'),
]
