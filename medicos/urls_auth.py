"""
URLs de Autenticação SaaS Multi-Tenant
"""

from django.urls import path
from . import views_auth

app_name = 'auth'

urlpatterns = [
    path('login/', views_auth.tenant_login, name='login_tenant'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('select-account/', views_auth.select_account, name='select_account'),
    path('switch-account/', views_auth.switch_account, name='switch_account'),
    path('license-expired/', views_auth.license_expired, name='license_expired'),
    path('register/', views_auth.register_view, name='register'),
]
