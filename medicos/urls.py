from django.urls import path
from . import views_user
from . import views_dashboard

app_name = 'medicos'

urlpatterns = [
    path('', views_dashboard.dashboard, name='index'),
    path('dashboard/', views_dashboard.dashboard, name='dashboard'),
    path('usuarios/', views_user.UserListView.as_view(), name='user_list'),
    path('usuarios/novo/', views_user.UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:user_id>/editar/', views_user.UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<int:user_id>/excluir/', views_user.UserDeleteView.as_view(), name='user_delete'),
    path('usuarios/<int:user_id>/', views_user.UserDetailView.as_view(), name='user_detail'),
]
