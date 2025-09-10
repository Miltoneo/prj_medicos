# -*- coding: utf-8 -*-
"""
Administração Django para funcionalidades SaaS avançadas
Sistema de Gerenciamento Médico - prj_medicos

Configurações do Django Admin para as novas funcionalidades SaaS:
- ContaPreferencias: Configurações de cada conta
- ContaAuditLog: Logs de auditoria com filtros avançados
- ContaMetrics: Métricas com visualizações e estatísticas

Criado em: 10/09/2025
Fonte: Implementação de melhores práticas SaaS conforme .github/copilot-instructions.md
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta
from .models import ContaPreferencias, ContaAuditLog, ContaMetrics


@admin.register(ContaPreferencias)
class ContaPreferenciasAdmin(admin.ModelAdmin):
    """
    Administração para Preferências da Conta
    """
    list_display = [
        'conta_nome', 'tema', 'idioma', 'notificacoes_email', 
        'backup_automatico', 'requerer_2fa', 'updated_at'
    ]
    list_filter = [
        'tema', 'idioma', 'notificacoes_email', 'backup_automatico', 
        'requerer_2fa', 'frequencia_backup', 'created_at'
    ]
    search_fields = ['conta__name', 'conta__cnpj']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Conta', {
            'fields': ('conta',)
        }),
        ('Interface e Aparência', {
            'fields': ('tema', 'idioma', 'timezone', 'formato_data_padrao', 'moeda_padrao', 'decimais_valor'),
            'classes': ('collapse',)
        }),
        ('Notificações', {
            'fields': ('notificacoes_email', 'notificacoes_vencimento', 'dias_antecedencia_vencimento'),
            'classes': ('collapse',)
        }),
        ('Segurança', {
            'fields': ('sessao_timeout_minutos', 'requerer_2fa'),
            'classes': ('collapse',)
        }),
        ('Backup e Exportação', {
            'fields': ('backup_automatico', 'frequencia_backup'),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def conta_nome(self, obj):
        return obj.conta.name
    conta_nome.short_description = 'Conta'
    conta_nome.admin_order_field = 'conta__name'

    def has_delete_permission(self, request, obj=None):
        # Não permitir exclusão de preferências
        return False


@admin.register(ContaAuditLog)
class ContaAuditLogAdmin(admin.ModelAdmin):
    """
    Administração para Logs de Auditoria
    """
    list_display = [
        'timestamp_formatted', 'conta_nome', 'user_email', 'acao_formatted', 
        'objeto_info', 'ip_address'
    ]
    list_filter = [
        'acao', 'timestamp', 'conta', 'user', 'objeto_tipo'
    ]
    search_fields = [
        'conta__name', 'user__email', 'objeto_nome', 'descricao', 'ip_address'
    ]
    readonly_fields = [
        'conta', 'user', 'timestamp', 'acao', 'objeto_tipo', 'objeto_id', 
        'objeto_nome', 'descricao', 'dados_anteriores', 'dados_novos', 
        'ip_address', 'user_agent'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    # Limitar o número de itens por página para performance
    list_per_page = 100
    list_max_show_all = 500
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('timestamp', 'conta', 'user', 'acao')
        }),
        ('Objeto Afetado', {
            'fields': ('objeto_tipo', 'objeto_id', 'objeto_nome', 'descricao')
        }),
        ('Dados da Modificação', {
            'fields': ('dados_anteriores', 'dados_novos'),
            'classes': ('collapse',)
        }),
        ('Informações Técnicas', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def timestamp_formatted(self, obj):
        return obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    timestamp_formatted.short_description = 'Data/Hora'
    timestamp_formatted.admin_order_field = 'timestamp'
    
    def conta_nome(self, obj):
        return obj.conta.name
    conta_nome.short_description = 'Conta'
    conta_nome.admin_order_field = 'conta__name'
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'Sistema'
    user_email.short_description = 'Usuário'
    user_email.admin_order_field = 'user__email'
    
    def acao_formatted(self, obj):
        color_map = {
            'login': 'green',
            'logout': 'orange',
            'create': 'blue',
            'update': 'purple',
            'delete': 'red',
            'export': 'brown',
            'import': 'teal',
            'config_change': 'navy',
        }
        color = color_map.get(obj.acao, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_acao_display()
        )
    acao_formatted.short_description = 'Ação'
    acao_formatted.admin_order_field = 'acao'
    
    def objeto_info(self, obj):
        if obj.objeto_tipo and obj.objeto_nome:
            return f"{obj.objeto_tipo}: {obj.objeto_nome}"
        elif obj.objeto_tipo:
            return obj.objeto_tipo
        return '-'
    objeto_info.short_description = 'Objeto'
    
    def has_add_permission(self, request):
        # Logs são criados automaticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs não devem ser editados
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permitir exclusão apenas para superusuários (limpeza de dados antigos)
        return request.user.is_superuser
    
    def get_queryset(self, request):
        # Otimizar query para melhor performance
        return super().get_queryset(request).select_related('conta', 'user')


@admin.register(ContaMetrics)
class ContaMetricsAdmin(admin.ModelAdmin):
    """
    Administração para Métricas da Conta
    """
    list_display = [
        'data', 'conta_nome', 'metrica_tipo_formatted', 'valor_formatted', 
        'periodo_tipo', 'created_at'
    ]
    list_filter = [
        'metrica_tipo', 'periodo_tipo', 'data', 'conta'
    ]
    search_fields = ['conta__name', 'metrica_tipo']
    readonly_fields = ['created_at']
    date_hierarchy = 'data'
    ordering = ['-data', 'conta__name', 'metrica_tipo']
    
    # Permitir filtragem por data personalizada
    list_per_page = 50
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('conta', 'metrica_tipo', 'valor', 'unidade')
        }),
        ('Período', {
            'fields': ('data', 'periodo_tipo')
        }),
        ('Dados Adicionais', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def conta_nome(self, obj):
        return obj.conta.name
    conta_nome.short_description = 'Conta'
    conta_nome.admin_order_field = 'conta__name'
    
    def metrica_tipo_formatted(self, obj):
        icon_map = {
            'usuarios_ativos': '👥',
            'logins_dia': '🔑',
            'relatorios_gerados': '📊',
            'despesas_lancadas': '💸',
            'receitas_lancadas': '💰',
            'notas_fiscais': '📄',
            'backup_executado': '💾',
            'storage_usado': '🗄️',
            'api_calls': '🔗',
            'tempo_sessao_medio': '⏱️',
        }
        icon = icon_map.get(obj.metrica_tipo, '📈')
        return f"{icon} {obj.get_metrica_tipo_display()}"
    metrica_tipo_formatted.short_description = 'Tipo de Métrica'
    metrica_tipo_formatted.admin_order_field = 'metrica_tipo'
    
    def valor_formatted(self, obj):
        if obj.unidade == 'quantidade':
            return f"{obj.valor:,.0f}"
        elif obj.unidade == 'MB':
            return f"{obj.valor:,.1f} MB"
        elif obj.unidade == 'minutos':
            return f"{obj.valor:,.1f} min"
        else:
            return f"{obj.valor:,.2f} {obj.unidade}"
    valor_formatted.short_description = 'Valor'
    valor_formatted.admin_order_field = 'valor'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conta')
    
    # Adicionar ações customizadas
    actions = ['calcular_resumo_selecionados']
    
    def calcular_resumo_selecionados(self, request, queryset):
        """
        Ação para calcular resumo das métricas selecionadas
        """
        total = queryset.aggregate(
            total_valor=Sum('valor'),
            media_valor=Avg('valor'),
            count=Count('id')
        )
        
        message = (
            f"Resumo de {total['count']} métricas selecionadas: "
            f"Total: {total['total_valor']:,.2f}, "
            f"Média: {total['media_valor']:,.2f}"
        )
        
        self.message_user(request, message)
    
    calcular_resumo_selecionados.short_description = "Calcular resumo das métricas selecionadas"


# Personalizar o título do admin
admin.site.site_header = "Administração SaaS - Sistema Médico"
admin.site.site_title = "Admin SaaS"
admin.site.index_title = "Painel de Administração SaaS"
