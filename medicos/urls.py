from django.urls import path
from . import views_user
from . import views_dashboard
from . import views_relatorios

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
]
