"""
URLs do Dashboard SaaS
"""

from django.urls import path
from . import views_dashboard

app_name = 'dashboard'

urlpatterns = [
    path('', views_dashboard.dashboard_home, name='home'),
    path('widgets/', views_dashboard.dashboard_widgets, name='widgets'),
    path('relatorio-executivo/', views_dashboard.dashboard_relatorio_executivo, name='relatorio_executivo'),
]
