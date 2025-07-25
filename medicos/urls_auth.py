"""
URLs de Autenticação SaaS Multi-Tenant
"""

from django.urls import path
from . import views_auth
from django.contrib.auth import views as auth_views

app_name = 'auth'

urlpatterns = [
    path('login/', views_auth.tenant_login, name='login_tenant'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('select-account/', views_auth.select_account, name='select_account'),
    path('switch-account/', views_auth.switch_account, name='switch_account'),
    path('license-expired/', views_auth.license_expired, name='license_expired'),
    path('register/', views_auth.register_view, name='register'),
    path('activate/<uidb64>/<token>/', views_auth.activate_account, name='activate_account'),
    path('password-reset/', views_auth.password_reset_view, name='password_reset'),
    path('', views_auth.index, name='index'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]
