# -*- coding: utf-8 -*-
"""
URLs para funcionalidades SaaS avançadas
Sistema de Gerenciamento Médico - prj_medicos

URLs para as novas funcionalidades SaaS:
- Configuração de preferências da conta
- Visualização de logs de auditoria
- Dashboard de métricas e analytics
- Exportação de dados

Criado em: 10/09/2025
Fonte: Implementação de melhores práticas SaaS conforme .github/copilot-instructions.md
"""

from django.urls import path
from . import views_saas

urlpatterns = [
    # Configurações SaaS - Específicas da Conta (não da empresa)
    path('conta/<int:conta_id>/saas/configuracoes/', 
         views_saas.saas_configuracoes, 
         name='saas_configuracoes'),
    
    # Auditoria - Específica da Conta
    path('conta/<int:conta_id>/saas/auditoria/', 
         views_saas.saas_auditoria, 
         name='saas_auditoria'),
    
    # Dashboard de Métricas - Específico da Conta
    path('conta/<int:conta_id>/saas/metrics/', 
         views_saas.saas_metrics_dashboard, 
         name='saas_metrics_dashboard'),
    
    # API para coleta de métricas - Específica da Conta
    path('conta/<int:conta_id>/saas/api/collect-metric/', 
         views_saas.saas_collect_metric, 
         name='saas_collect_metric'),
    
    # Exportação de dados - Específica da Conta
    path('conta/<int:conta_id>/saas/export/', 
         views_saas.saas_export_data, 
         name='saas_export_data'),
]
