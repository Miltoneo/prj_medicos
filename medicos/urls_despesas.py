
from django.urls import path
from . import views_despesas

urlpatterns = [
    path('lista_consolidado_despesas/<int:empresa_id>/', views_despesas.ConsolidadoDespesasView.as_view(), name='lista_consolidado_despesas'),
    path('lista_despesas_empresa/<int:empresa_id>/', views_despesas.ListaDespesasEmpresaView.as_view(), name='lista_despesas_empresa'),
    path('nova_despesa_empresa/<int:empresa_id>/', views_despesas.NovaDespesaEmpresaView.as_view(), name='nova_despesa_empresa'),
    path('editar_despesa_empresa/<int:empresa_id>/<int:pk>/', views_despesas.EditarDespesaEmpresaView.as_view(), name='editar_despesa_empresa'),
    path('excluir_despesa_empresa/<int:empresa_id>/<int:pk>/', views_despesas.ExcluirDespesaEmpresaView.as_view(), name='excluir_despesa_empresa'),
path('despesas_socio/<int:empresa_id>/', views_despesas.ListaDespesasSocioView.as_view(), name='despesas_socio_lista'),
path('despesas_socio/<int:empresa_id>/novo/', views_despesas.DespesaSocioCreateView.as_view(), name='despesas_socio_form'),
path('despesas_socio/<int:empresa_id>/<int:pk>/editar/', views_despesas.DespesaSocioUpdateView.as_view(), name='despesas_socio_form_edit'),
path('despesas_socio/<int:empresa_id>/<int:pk>/excluir/', views_despesas.DespesaSocioDeleteView.as_view(), name='despesas_socio_confirm_delete'),

    # Rota para copiar despesas do mês anterior
    path('copiar_despesas_mes_anterior/<int:empresa_id>/', views_despesas.copiar_despesas_mes_anterior, name='copiar_despesas_mes_anterior'),
]
