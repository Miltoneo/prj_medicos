# -*- coding: utf-8 -*-
"""
Utilitários para funcionalidades SaaS avançadas
Sistema de Gerenciamento Médico - prj_medicos

Este módulo fornece funções para trabalhar com as novas funcionalidades SaaS:
- Gerenciamento de preferências da conta
- Registro de auditoria automática
- Coleta e análise de métricas

Criado em: 10/09/2025
Fonte: Implementação de melhores práticas SaaS conforme .github/copilot-instructions.md
"""

from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conta, ContaPreferencias, ContaAuditLog, ContaMetrics

User = get_user_model()


class SaaSPreferencesManager:
    """
    Gerenciador de preferências da conta com valores padrão inteligentes
    """
    
    @staticmethod
    def get_or_create_preferences(conta):
        """
        Obtém ou cria preferências para uma conta
        
        Args:
            conta (Conta): Instância da conta
            
        Returns:
            ContaPreferencias: Instância das preferências
        """
        preferences, created = ContaPreferencias.objects.get_or_create(
            conta=conta,
            defaults={
                'tema': 'claro',
                'idioma': 'pt-br',
                'timezone': 'America/Sao_Paulo',
                'formato_data_padrao': 'dd/mm/yyyy',
                'moeda_padrao': 'BRL',
                'decimais_valor': 2,
                'notificacoes_email': True,
                'notificacoes_vencimento': True,
                'dias_antecedencia_vencimento': 5,
                'sessao_timeout_minutos': 120,
                'requerer_2fa': False,
                'backup_automatico': False,
                'frequencia_backup': 'semanal',
            }
        )
        return preferences
    
    @staticmethod
    def update_preferences(conta, **kwargs):
        """
        Atualiza preferências da conta
        
        Args:
            conta (Conta): Instância da conta
            **kwargs: Campos a serem atualizados
            
        Returns:
            ContaPreferencias: Instância atualizada
        """
        preferences = SaaSPreferencesManager.get_or_create_preferences(conta)
        for key, value in kwargs.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        preferences.save()
        return preferences


class SaaSAuditManager:
    """
    Gerenciador de auditoria automática para ações do sistema
    """
    
    @staticmethod
    def log_action(conta, user, acao, objeto_tipo=None, objeto_id=None, 
                   objeto_nome=None, descricao=None, dados_anteriores=None, 
                   dados_novos=None, ip_address=None, user_agent=None):
        """
        Registra uma ação de auditoria
        
        Args:
            conta (Conta): Conta relacionada
            user (User): Usuário que executou a ação
            acao (str): Tipo de ação (choices do model)
            objeto_tipo (str): Tipo do objeto afetado
            objeto_id (str): ID do objeto afetado
            objeto_nome (str): Nome do objeto afetado
            descricao (str): Descrição da ação
            dados_anteriores (dict): Dados antes da modificação
            dados_novos (dict): Dados após a modificação
            ip_address (str): IP do usuário
            user_agent (str): User agent do navegador
            
        Returns:
            ContaAuditLog: Registro de auditoria criado
        """
        return ContaAuditLog.objects.create(
            conta=conta,
            user=user,
            acao=acao,
            objeto_tipo=objeto_tipo,
            objeto_id=objeto_id,
            objeto_nome=objeto_nome,
            descricao=descricao,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_login(conta, user, ip_address=None, user_agent=None):
        """
        Registra login do usuário
        """
        return SaaSAuditManager.log_action(
            conta=conta,
            user=user,
            acao='login',
            descricao=f'Login do usuário {user.email}',
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_create(conta, user, objeto, descricao=None, ip_address=None):
        """
        Registra criação de objeto
        """
        return SaaSAuditManager.log_action(
            conta=conta,
            user=user,
            acao='create',
            objeto_tipo=objeto.__class__.__name__,
            objeto_id=str(objeto.pk),
            objeto_nome=str(objeto),
            descricao=descricao or f'Criação de {objeto.__class__.__name__}',
            dados_novos={'id': objeto.pk, 'nome': str(objeto)},
            ip_address=ip_address
        )
    
    @staticmethod
    def log_update(conta, user, objeto, dados_anteriores=None, descricao=None, ip_address=None):
        """
        Registra atualização de objeto
        """
        return SaaSAuditManager.log_action(
            conta=conta,
            user=user,
            acao='update',
            objeto_tipo=objeto.__class__.__name__,
            objeto_id=str(objeto.pk),
            objeto_nome=str(objeto),
            descricao=descricao or f'Atualização de {objeto.__class__.__name__}',
            dados_anteriores=dados_anteriores,
            dados_novos={'id': objeto.pk, 'nome': str(objeto)},
            ip_address=ip_address
        )


class SaaSMetricsManager:
    """
    Gerenciador de métricas e analytics da conta
    """
    
    @staticmethod
    def record_metric(conta, metrica_tipo, valor, data=None, periodo_tipo='dia', 
                     unidade='quantidade', metadados=None):
        """
        Registra uma métrica
        
        Args:
            conta (Conta): Conta relacionada
            metrica_tipo (str): Tipo da métrica (choices do model)
            valor (Decimal): Valor da métrica
            data (date): Data da métrica (padrão: hoje)
            periodo_tipo (str): Tipo de período
            unidade (str): Unidade da métrica
            metadados (dict): Dados adicionais
            
        Returns:
            ContaMetrics: Métrica criada
        """
        if data is None:
            data = timezone.now().date()
            
        # Verifica se já existe métrica para o mesmo tipo e data
        metric, created = ContaMetrics.objects.get_or_create(
            conta=conta,
            metrica_tipo=metrica_tipo,
            data=data,
            periodo_tipo=periodo_tipo,
            defaults={
                'valor': valor,
                'unidade': unidade,
                'metadados': metadados or {}
            }
        )
        
        if not created:
            # Atualiza valor existente
            metric.valor = valor
            metric.unidade = unidade
            if metadados:
                metric.metadados = metadados
            metric.save()
        
        return metric
    
    @staticmethod
    def increment_metric(conta, metrica_tipo, incremento=1, data=None, periodo_tipo='dia'):
        """
        Incrementa uma métrica existente
        """
        if data is None:
            data = timezone.now().date()
            
        metric, created = ContaMetrics.objects.get_or_create(
            conta=conta,
            metrica_tipo=metrica_tipo,
            data=data,
            periodo_tipo=periodo_tipo,
            defaults={'valor': incremento}
        )
        
        if not created:
            metric.valor += incremento
            metric.save()
        
        return metric
    
    @staticmethod
    def get_metric_summary(conta, metrica_tipo, periodo_dias=30):
        """
        Obtém resumo de uma métrica por período
        
        Args:
            conta (Conta): Conta relacionada
            metrica_tipo (str): Tipo da métrica
            periodo_dias (int): Número de dias para análise
            
        Returns:
            dict: Resumo com total, média, máximo, mínimo
        """
        from django.db.models import Sum, Avg, Max, Min, Count
        from datetime import timedelta
        
        data_inicio = timezone.now().date() - timedelta(days=periodo_dias)
        
        metrics = ContaMetrics.objects.filter(
            conta=conta,
            metrica_tipo=metrica_tipo,
            data__gte=data_inicio
        )
        
        summary = metrics.aggregate(
            total=Sum('valor'),
            media=Avg('valor'),
            maximo=Max('valor'),
            minimo=Min('valor'),
            count=Count('id')
        )
        
        return {
            'periodo_dias': periodo_dias,
            'total_registros': summary['count'] or 0,
            'total': summary['total'] or 0,
            'media': summary['media'] or 0,
            'maximo': summary['maximo'] or 0,
            'minimo': summary['minimo'] or 0,
        }


# Decorador para auditoria automática
def audit_action(acao, objeto_tipo=None):
    """
    Decorador para registrar automaticamente ações de auditoria
    
    Usage:
        @audit_action('create', 'DespesaSocio')
        def create_despesa(request, ...):
            # lógica da view
            pass
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Executa a função original
            result = view_func(request, *args, **kwargs)
            
            # Registra auditoria se usuário e conta estão disponíveis
            if hasattr(request, 'user') and hasattr(request, 'conta'):
                try:
                    SaaSAuditManager.log_action(
                        conta=request.conta,
                        user=request.user,
                        acao=acao,
                        objeto_tipo=objeto_tipo,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )
                except Exception as e:
                    # Log error mas não interrompe o fluxo
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erro ao registrar auditoria: {e}")
            
            return result
        return wrapper
    return decorator


# Context processor para preferências
def saas_preferences_context(request):
    """
    Context processor para disponibilizar preferências da conta em templates
    
    Usage em settings.py:
        TEMPLATES[0]['OPTIONS']['context_processors'].append(
            'medicos.utils_saas.saas_preferences_context'
        )
    """
    context = {}
    
    if hasattr(request, 'conta') and request.conta:
        try:
            preferences = SaaSPreferencesManager.get_or_create_preferences(request.conta)
            context['conta_preferences'] = preferences
        except Exception:
            # Em caso de erro, usa valores padrão
            context['conta_preferences'] = None
    
    return context
