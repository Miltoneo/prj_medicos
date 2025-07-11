from django.urls import path
from . import views_user
from . import views_dashboard
from . import views_relatorios
from . import views_empresa
from . import views_home_cenario
from . import views_dashboard_empresa
from . import views_socio
from . import views_aliquota
from . import views_despesa
from django.contrib.auth import views as auth_views

app_name = 'medicos'

urlpatterns = [
    path('', views_dashboard.dashboard, name='index'),
    path('dashboard/', views_dashboard.dashboard, name='dashboard'),
    path('home/', views_dashboard.dashboard, name='home'),
    path('cenario-home/', views_home_cenario.home_cenario, name='cenario_home'),
    # Dashboard SaaS (migrado de urls_dashboard.py)
    # path('', views_dashboard.dashboard_home, name='home'),
    # path('widgets/', views_dashboard.dashboard_widgets, name='widgets'),
    path('relatorio-executivo/', views_relatorios.relatorio_executivo, name='relatorio_executivo'),
    path('relatorio-executivo/pdf/<int:conta_id>/', views_relatorios.relatorio_executivo_pdf, name='relatorio_executivo_pdf'),
    path('usuarios/', views_user.UserListView.as_view(), name='user_list'),
    path('usuarios/novo/', views_user.UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:user_id>/editar/', views_user.UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<int:user_id>/excluir/', views_user.UserDeleteView.as_view(), name='user_delete'),
    path('usuarios/<int:user_id>/', views_user.UserDetailView.as_view(), name='user_detail'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/medicos/auth/login/'), name='logout'),
    path('set-empresa/', views_empresa.set_empresa, name='set_empresa'),
    path('empresas/', views_empresa.EmpresaListView.as_view(), name='empresa_list'),
    path('empresas/nova/', views_empresa.empresa_create, name='empresa_create'),
    path('empresas/<int:empresa_id>/', views_empresa.empresa_detail, name='empresa_detail'),
    path('empresas/<int:empresa_id>/editar/', views_empresa.empresa_update, name='empresa_update'),
    path('empresas/<int:empresa_id>/excluir/', views_empresa.empresa_delete, name='empresa_delete'),
    path('empresas/<int:empresa_id>/dashboard/', views_dashboard_empresa.dashboard_empresa, name='dashboard_empresa'),
    path('empresas/<int:empresa_id>/socios/', views_dashboard_empresa.lista_socios_empresa, name='lista_socios_empresa'),
    path('empresas/<int:empresa_id>/socios/novo/', views_socio.socio_create, name='socio_create'),
    path('empresas/<int:empresa_id>/socios/<int:socio_id>/editar/', views_socio.socio_edit, name='socio_edit'),
    path('empresas/<int:empresa_id>/socios/<int:socio_id>/desvincular/', views_socio.socio_unlink, name='socio_unlink'),
    path('empresas/<int:empresa_id>/aliquotas/', views_aliquota.ListaAliquotasView.as_view(), name='lista_aliquotas'),
    path('empresas/<int:empresa_id>/aliquotas/<int:aliquota_id>/editar/', views_aliquota.aliquota_edit, name='aliquota_edit'),
    path('empresas/<int:empresa_id>/grupos-despesa/', views_despesa.lista_grupos_despesa, name='lista_grupos_despesa'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/editar/', views_despesa.grupo_despesa_edit, name='grupo_despesa_edit'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/novo/', views_despesa.item_despesa_create, name='item_despesa_create'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/', views_despesa.ItemDespesaListView.as_view(), name='lista_itens_despesa'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/<int:item_id>/editar/', views_despesa.item_despesa_edit, name='item_despesa_edit'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/<int:item_id>/excluir/', views_despesa.item_despesa_delete, name='item_despesa_delete'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/excluir/', views_despesa.grupo_despesa_delete, name='grupo_despesa_delete'),
]
