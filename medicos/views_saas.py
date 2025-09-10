# -*- coding: utf-8 -*-
"""
Views para funcionalidades SaaS avançadas
Sistema de Gerenciamento Médico - prj_medicos

Views para demonstrar o uso das novas funcionalidades SaaS:
- Configuração de preferências da conta
- Visualização de logs de auditoria
- Dashboard de métricas e analytics

Criado em: 10/09/2025
Fonte: Implementação de melhores práticas SaaS conforme .github/copilot-instructions.md
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import Conta, ContaPreferencias, ContaAuditLog, ContaMetrics, ContaMembership
from .utils_saas import SaaSPreferencesManager, SaaSAuditManager, SaaSMetricsManager, audit_action


@login_required
def saas_configuracoes(request, conta_id):
    """
    View para configurações SaaS da conta
    """
    # Obtém a conta através do membership, validando acesso do usuário
    try:
        membership = ContaMembership.objects.select_related('conta').get(
            user=request.user, 
            conta_id=conta_id,
            is_active=True
        )
        conta = membership.conta
    except ContaMembership.DoesNotExist:
        messages.error(request, 'Acesso negado a esta conta.')
        return redirect('medicos:home')
    
    context = {
        'titulo_pagina': 'Configurações da Conta',
        'conta_id': conta_id,
    }
    
    # Obtém preferências da conta
    preferences = SaaSPreferencesManager.get_or_create_preferences(conta)
    
    if request.method == 'POST':
        # Atualiza preferências
        try:
            updated_data = {}
            
            # Campos de configuração da interface
            if 'tema' in request.POST:
                updated_data['tema'] = request.POST['tema']
            if 'idioma' in request.POST:
                updated_data['idioma'] = request.POST['idioma']
            if 'formato_data_padrao' in request.POST:
                updated_data['formato_data_padrao'] = request.POST['formato_data_padrao']
            
            # Campos de notificação
            updated_data['notificacoes_email'] = 'notificacoes_email' in request.POST
            updated_data['notificacoes_vencimento'] = 'notificacoes_vencimento' in request.POST
            
            if 'dias_antecedencia_vencimento' in request.POST:
                updated_data['dias_antecedencia_vencimento'] = int(request.POST['dias_antecedencia_vencimento'])
            
            # Campos de segurança
            if 'sessao_timeout_minutos' in request.POST:
                updated_data['sessao_timeout_minutos'] = int(request.POST['sessao_timeout_minutos'])
            
            updated_data['requerer_2fa'] = 'requerer_2fa' in request.POST
            
            # Campos de backup
            updated_data['backup_automatico'] = 'backup_automatico' in request.POST
            if 'frequencia_backup' in request.POST:
                updated_data['frequencia_backup'] = request.POST['frequencia_backup']
            
            # Atualiza preferências
            preferences = SaaSPreferencesManager.update_preferences(conta, **updated_data)
            
            # Registra auditoria
            SaaSAuditManager.log_action(
                conta=conta,
                user=request.user,
                acao='config_change',
                objeto_tipo='ContaPreferencias',
                objeto_id=str(preferences.conta.id),
                objeto_nome='Preferências da Conta',
                descricao='Atualização das configurações da conta',
                dados_novos=updated_data,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Registra métrica
            SaaSMetricsManager.increment_metric(
                conta=conta,
                metrica_tipo='config_change'
            )
            
            messages.success(request, 'Configurações atualizadas com sucesso!')
            return redirect('medicos:saas_configuracoes', conta_id=conta_id)
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar configurações: {str(e)}')
    
    context['preferences'] = preferences
    return render(request, 'saas/configuracoes.html', context)


@login_required
def saas_auditoria(request, conta_id):
    """
    View para visualizar logs de auditoria da conta
    """
    # Obtém a conta através do membership, validando acesso do usuário
    try:
        membership = ContaMembership.objects.select_related('conta').get(
            user=request.user, 
            conta_id=conta_id,
            is_active=True
        )
        conta = membership.conta
    except ContaMembership.DoesNotExist:
        messages.error(request, 'Acesso negado a esta conta.')
        return redirect('medicos:home')
    
    context = {
        'titulo_pagina': 'Logs de Auditoria',
        'conta_id': conta_id,
    }
    
    # Filtros
    acao_filter = request.GET.get('acao', '')
    user_filter = request.GET.get('user', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Query base
    logs = ContaAuditLog.objects.filter(conta=conta).order_by('-timestamp')
    
    # Aplicar filtros
    if acao_filter:
        logs = logs.filter(acao=acao_filter)
    
    if user_filter:
        logs = logs.filter(user__email__icontains=user_filter)
    
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=data_inicio_dt)
        except ValueError:
            messages.warning(request, 'Formato de data inválido para data início')
    
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            # Adiciona 23:59:59 para incluir todo o dia
            data_fim_dt = data_fim_dt.replace(hour=23, minute=59, second=59)
            logs = logs.filter(timestamp__lte=data_fim_dt)
        except ValueError:
            messages.warning(request, 'Formato de data inválido para data fim')
    
    # Paginação
    paginator = Paginator(logs, 50)  # 50 logs por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Opções para filtros
    acoes_disponiveis = ContaAuditLog.objects.filter(conta=conta).values_list('acao', flat=True).distinct()
    
    context.update({
        'page_obj': page_obj,
        'acoes_disponiveis': acoes_disponiveis,
        'filtros': {
            'acao': acao_filter,
            'user': user_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    })
    
    return render(request, 'saas/auditoria.html', context)


@login_required
def saas_metrics_dashboard(request, conta_id):
    """
    Dashboard de métricas e analytics da conta
    """
    # Obtém a conta através do membership, validando acesso do usuário
    try:
        membership = ContaMembership.objects.select_related('conta').get(
            user=request.user, 
            conta_id=conta_id,
            is_active=True
        )
        conta = membership.conta
    except ContaMembership.DoesNotExist:
        messages.error(request, 'Acesso negado a esta conta.')
        return redirect('medicos:home')
    
    context = {
        'titulo_pagina': 'Dashboard de Métricas',
        'conta_id': conta_id,
    }
    
    # Período para análise (últimos 30 dias por padrão)
    periodo_dias = int(request.GET.get('periodo', 30))
    
    # Métricas principais
    metrics_summary = {}
    
    # Lista de métricas para exibir
    metricas_principais = [
        'usuarios_ativos',
        'logins_dia',
        'relatorios_gerados',
        'despesas_lancadas',
        'receitas_lancadas',
        'notas_fiscais'
    ]
    
    for metrica in metricas_principais:
        try:
            summary = SaaSMetricsManager.get_metric_summary(
                conta, 
                metrica, 
                periodo_dias
            )
            metrics_summary[metrica] = summary
        except Exception as e:
            metrics_summary[metrica] = {'error': str(e)}
    
    # Dados para gráficos (últimos 7 dias)
    data_inicio = datetime.now().date() - timedelta(days=7)
    chart_data = {}
    
    for metrica in metricas_principais[:3]:  # Só as 3 principais para o gráfico
        daily_data = ContaMetrics.objects.filter(
            conta=conta,
            metrica_tipo=metrica,
            data__gte=data_inicio
        ).order_by('data')
        
        chart_data[metrica] = {
            'dates': [item.data.strftime('%d/%m') for item in daily_data],
            'values': [float(item.valor) for item in daily_data]
        }
    
    # Estatísticas gerais da conta
    total_users = conta.memberships.filter(is_active=True).count()
    total_empresas = conta.empresas.count()
    
    # Últimas atividades (últimos 10 logs)
    recent_activities = ContaAuditLog.objects.filter(
        conta=conta
    ).order_by('-timestamp')[:10]
    
    context.update({
        'metrics_summary': metrics_summary,
        'chart_data': json.dumps(chart_data),
        'periodo_dias': periodo_dias,
        'total_users': total_users,
        'total_empresas': total_empresas,
        'recent_activities': recent_activities,
        'metricas_principais': metricas_principais,
    })
    
    return render(request, 'saas/metrics_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def saas_collect_metric(request, conta_id):
    """
    Endpoint AJAX para coletar métricas em tempo real
    """
    # Obtém a conta através do membership
    membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
    conta = membership.conta if membership else None
    
    if not conta:
        return JsonResponse({'error': 'Conta não encontrada para o usuário atual'}, status=403)
    
    try:
        data = json.loads(request.body)
        metrica_tipo = data.get('metrica_tipo')
        valor = data.get('valor', 1)
        metadados = data.get('metadados', {})
        
        if not metrica_tipo:
            return JsonResponse({'error': 'Tipo de métrica é obrigatório'}, status=400)
        
        # Registra a métrica
        metric = SaaSMetricsManager.record_metric(
            conta=conta,
            metrica_tipo=metrica_tipo,
            valor=valor,
            metadados=metadados
        )
        
        return JsonResponse({
            'success': True,
            'metric_id': metric.id,
            'valor': float(metric.valor)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def saas_export_data(request, conta_id):
    """
    Exportação de dados da conta (auditoria, métricas, etc.)
    """
    import csv
    from django.http import HttpResponse
    
    # Obtém a conta através do membership
    membership = ContaMembership.objects.filter(user=request.user, is_active=True).first()
    conta = membership.conta if membership else None
    
    if not conta:
        messages.error(request, 'Conta não encontrada para o usuário atual.')
        return redirect('medicos:home')
    
    export_type = request.GET.get('type', 'audit')
    
    if export_type == 'audit':
        # Exportar logs de auditoria
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="auditoria_{conta.name}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Data/Hora', 'Usuário', 'Ação', 'Objeto', 'Descrição', 'IP'])
        
        logs = ContaAuditLog.objects.filter(conta=conta).order_by('-timestamp')
        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                log.user.email if log.user else 'Sistema',
                log.get_acao_display(),
                f"{log.objeto_tipo} - {log.objeto_nome}" if log.objeto_tipo else '',
                log.descricao,
                log.ip_address or ''
            ])
        
        # Registra a exportação
        SaaSAuditManager.log_action(
            conta=conta,
            user=request.user,
            acao='export',
            objeto_tipo='ContaAuditLog',
            descricao='Exportação de logs de auditoria',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return response
    
    elif export_type == 'metrics':
        # Exportar métricas
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="metricas_{conta.name}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Data', 'Tipo de Métrica', 'Valor', 'Unidade', 'Período'])
        
        metrics = ContaMetrics.objects.filter(conta=conta).order_by('-data')
        for metric in metrics:
            writer.writerow([
                metric.data.strftime('%d/%m/%Y'),
                metric.get_metrica_tipo_display(),
                metric.valor,
                metric.unidade,
                metric.get_periodo_tipo_display()
            ])
        
        # Registra a exportação
        SaaSAuditManager.log_action(
            conta=conta,
            user=request.user,
            acao='export',
            objeto_tipo='ContaMetrics',
            descricao='Exportação de métricas',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return response
    
    else:
        messages.error(request, 'Tipo de exportação inválido')
        return redirect('medicos:saas_metrics_dashboard', conta_id=conta_id)
