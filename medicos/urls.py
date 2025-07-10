from django.urls import path
from . import views_user
from . import views_dashboard
from . import views_relatorios
from . import views_empresa
from django.contrib.auth import views as auth_views

app_name = 'medicos'

urlpatterns = [
    path('', views_dashboard.dashboard, name='index'),
    path('dashboard/', views_dashboard.dashboard, name='dashboard'),
    path('home/', views_dashboard.dashboard, name='home'),
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
    path('empresas/', views_empresa.empresa_list, name='empresa_list'),
    path('empresas/nova/', views_empresa.empresa_create, name='empresa_create'),
    path('empresas/<int:empresa_id>/', views_empresa.empresa_detail, name='empresa_detail'),
    path('empresas/<int:empresa_id>/editar/', views_empresa.empresa_update, name='empresa_update'),
    path('empresas/<int:empresa_id>/excluir/', views_empresa.empresa_delete, name='empresa_delete'),
]
