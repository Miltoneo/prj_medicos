"""
Views do Dashboard SaaS - Sistema Multi-Tenant
Implementa dashboard contextual por conta com métricas e widgets.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Conta, Pessoa, Empresa, NotaFiscal, 
    Despesa, ContaMembership, Licenca
)
from .middleware.tenant_middleware import get_current_account


@login_required
def dashboard_home(request):
    """
    Dashboard principal SaaS com métricas por conta
    """
    # Validar contexto do tenant
    conta_atual = get_current_account()
    if not conta_atual:
        messages.error(request, 'Conta não selecionada. Faça login novamente.')
        return redirect('medicos:auth:login_tenant')
    
    # Verificar se usuário tem acesso à conta
    try:
        usuario_conta = ContaMembership.objects.get(
            user=request.user,
            conta=conta_atual
        )
    except ContaMembership.DoesNotExist:
        messages.error(request, 'Você não tem acesso a esta conta.')
        return redirect('medicos:auth:select_account')
    
    # Período para métricas (últimos 30 dias)
    data_inicio = timezone.now() - timedelta(days=30)
    
    # === MÉTRICAS GERAIS ===
    total_pessoas = Pessoa.objects.filter(conta=conta_atual).count()
    total_empresas = Empresa.objects.filter(conta=conta_atual).count()
    
    # === MÉTRICAS FINANCEIRAS ===
    # Notas Fiscais do período
    nf_periodo = NotaFiscal.objects.filter(
        conta=conta_atual,
        dtEmissao__gte=data_inicio
    )
    
    total_faturamento = nf_periodo.aggregate(
        total=Sum('val_bruto')
    )['total'] or Decimal('0.00')
    
    # Assumindo que não há campo status, vamos usar dtRecebimento para determinar se está paga
    nf_pagas = nf_periodo.filter(dtRecebimento__isnull=False).count()
    nf_pendentes = nf_periodo.filter(dtRecebimento__isnull=True).count()
    
    # Despesas do período
    despesas_periodo = Despesa.objects.filter(
        conta=conta_atual,
        data__gte=data_inicio
    )
    
    total_despesas = despesas_periodo.aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0.00')
    
    # === MÉTRICAS DE USUÁRIOS ===
    usuarios_ativos = ContaMembership.objects.filter(
        conta=conta_atual
    ).count()
    
    # === GRÁFICOS E WIDGETS ===
    # Faturamento por mês (últimos 6 meses)
    meses_faturamento = []
    for i in range(6):
        data_mes = timezone.now() - timedelta(days=30*i)
        inicio_mes = data_mes.replace(day=1)
        if i == 0:
            fim_mes = timezone.now()
        else:
            fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        faturamento_mes = NotaFiscal.objects.filter(
            conta=conta_atual,
            dtEmissao__gte=inicio_mes,
            dtEmissao__lte=fim_mes
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0.00')
        
        meses_faturamento.append({
            'mes': data_mes.strftime('%b/%Y'),
            'valor': float(faturamento_mes)
        })
    
    meses_faturamento.reverse()
    
    # Distribuição de status das NFs (baseado em dtRecebimento)
    nf_pagas_count = nf_periodo.filter(dtRecebimento__isnull=False).count()
    nf_pendentes_count = nf_periodo.filter(dtRecebimento__isnull=True).count()
    
    status_nf = [
        {'status': 'Pagas', 'total': nf_pagas_count},
        {'status': 'Pendentes', 'total': nf_pendentes_count}
    ]
    
    # Últimas atividades
    ultimas_nf = NotaFiscal.objects.filter(
        conta=conta_atual
    ).order_by('-dtEmissao')[:5]
    
    ultimas_despesas = Despesa.objects.filter(
        conta=conta_atual
    ).order_by('-data')[:5]
    
    # === ALERTAS E NOTIFICAÇÕES ===
    alertas = []
    
    # Verificar licença próxima do vencimento
    try:
        licenca = conta_atual.licenca
        dias_vencimento = (licenca.data_fim - timezone.now().date()).days
        if dias_vencimento <= 7:
            alertas.append({
                'tipo': 'warning' if dias_vencimento > 0 else 'danger',
                'titulo': 'Licença expirando' if dias_vencimento > 0 else 'Licença expirada',
                'mensagem': f'A licença vence em {dias_vencimento} dias' if dias_vencimento > 0 else 'A licença está expirada',
                'acao': 'Renovar licença',
                'url': '#'
            })
    except Licenca.DoesNotExist:
        alertas.append({
            'tipo': 'danger',
            'titulo': 'Licença não encontrada',
            'mensagem': 'Esta conta não possui licença configurada',
            'acao': 'Configurar licença',
            'url': '#'
        })
    
    # Verificar limite de usuários
    try:
        limite_usuarios = conta_atual.licenca.limite_usuarios
    except Licenca.DoesNotExist:
        limite_usuarios = 1
        
    if usuarios_ativos >= limite_usuarios:
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Limite de usuários atingido',
            'mensagem': f'Você está usando {usuarios_ativos} de {limite_usuarios} usuários',
            'acao': 'Upgrade da licença',
            'url': '#'
        })
    
    # NFs vencidas (assumindo que são as que não foram recebidas há mais de 30 dias)
    data_vencimento = timezone.now().date() - timedelta(days=30)
    nf_vencidas = NotaFiscal.objects.filter(
        conta=conta_atual,
        dtEmissao__lt=data_vencimento,
        dtRecebimento__isnull=True
    ).count()
    
    if nf_vencidas > 0:
        alertas.append({
            'tipo': 'danger',
            'titulo': 'Notas fiscais vencidas',
            'mensagem': f'{nf_vencidas} nota(s) fiscal(is) não recebida(s)',
            'acao': 'Ver detalhes',
            'url': '/financeiro/notas-fiscais/?vencidas=1'
        })
    
    context = {
        'conta_atual': conta_atual,
        'usuario_conta': usuario_conta,
        
        # Métricas gerais
        'total_pessoas': total_pessoas,
        'total_empresas': total_empresas,
        'usuarios_ativos': usuarios_ativos,
        
        # Métricas financeiras
        'total_faturamento': total_faturamento,
        'total_despesas': total_despesas,
        'saldo_periodo': total_faturamento - total_despesas,
        'nf_pagas': nf_pagas,
        'nf_pendentes': nf_pendentes,
        
        # Gráficos
        'meses_faturamento': meses_faturamento,
        'status_nf': status_nf,
        
        # Atividades recentes
        'ultimas_nf': ultimas_nf,
        'ultimas_despesas': ultimas_despesas,
        
        # Alertas
        'alertas': alertas,
        
        # Metadados
        'periodo_inicio': data_inicio.strftime('%d/%m/%Y'),
        'periodo_fim': timezone.now().strftime('%d/%m/%Y'),
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_widgets(request):
    """
    Endpoint para widgets AJAX do dashboard
    """
    conta_atual = get_current_account()
    if not conta_atual:
        return redirect('medicos:auth:login_tenant')
    
    widget_type = request.GET.get('widget')
    
    if widget_type == 'faturamento_mensal':
        # Dados de faturamento mensal para gráfico
        meses = []
        for i in range(12):
            data_mes = timezone.now() - timedelta(days=30*i)
            inicio_mes = data_mes.replace(day=1)
            if i == 0:
                fim_mes = timezone.now()
            else:
                fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            faturamento = NotaFiscal.objects.filter(
                conta=conta_atual,
                dtEmissao__gte=inicio_mes,
                dtEmissao__lte=fim_mes
            ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0.00')
            
            meses.append({
                'mes': data_mes.strftime('%Y-%m'),
                'label': data_mes.strftime('%b/%Y'),
                'valor': float(faturamento)
            })
        
        meses.reverse()
        return JsonResponse({'meses': meses})
    
    elif widget_type == 'top_pessoas':
        # Top pessoas por faturamento
        top_pessoas = Pessoa.objects.filter(
            conta=conta_atual
        ).annotate(
            total_nf=Sum('socio__notafiscal__val_bruto')
        ).filter(
            total_nf__isnull=False
        ).order_by('-total_nf')[:10]
        
        dados = [{
            'nome': pessoa.name,
            'cpf': pessoa.CPF,
            'total': float(pessoa.total_nf or 0)
        } for pessoa in top_pessoas]
        
        return JsonResponse({'pessoas': dados})
    
    return JsonResponse({'error': 'Widget não encontrado'})


@login_required
def dashboard_relatorio_executivo(request):
    """
    Relatório executivo da conta com métricas avançadas
    """
    conta_atual = get_current_account()
    if not conta_atual:
        return redirect('medicos:auth:login_tenant')
    
    # Verificar permissão (apenas admin/proprietário)
    usuario_conta = ContaMembership.objects.get(
        user=request.user,
        conta=conta_atual
    )
    
    if usuario_conta.role not in ['admin']:
        messages.error(request, 'Acesso negado. Apenas administradores podem ver este relatório.')
        return redirect('medicos:dashboard:home')
    
    # Período configurável
    periodo = request.GET.get('periodo', '30')  # dias
    try:
        dias = int(periodo)
    except:
        dias = 30
    
    data_inicio = timezone.now() - timedelta(days=dias)
    
    # === ANÁLISES AVANÇADAS ===
    
    # Crescimento de faturamento
    periodo_anterior = timezone.now() - timedelta(days=dias*2)
    
    faturamento_atual = NotaFiscal.objects.filter(
        conta=conta_atual,
        dtEmissao__gte=data_inicio
    ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0.00')
    
    faturamento_anterior = NotaFiscal.objects.filter(
        conta=conta_atual,
        dtEmissao__gte=periodo_anterior,
        dtEmissao__lt=data_inicio
    ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0.00')
    
    if faturamento_anterior > 0:
        crescimento_faturamento = ((faturamento_atual - faturamento_anterior) / faturamento_anterior) * 100
    else:
        crescimento_faturamento = 0
    
    # Top empresas por faturamento
    top_empresas = Empresa.objects.filter(
        conta=conta_atual
    ).annotate(
        total_faturado=Sum('notafiscal__val_bruto')
    ).filter(
        total_faturado__isnull=False
    ).order_by('-total_faturado')[:10]
    
    # Análise de inadimplência (NFs não recebidas há mais de 30 dias)
    data_inadimplencia = timezone.now().date() - timedelta(days=30)
    nf_vencidas_valor = NotaFiscal.objects.filter(
        conta=conta_atual,
        dtEmissao__lt=data_inadimplencia,
        dtRecebimento__isnull=True
    ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0.00')
    
    total_pendente = NotaFiscal.objects.filter(
        conta=conta_atual,
        dtRecebimento__isnull=True
    ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0.00')
    
    if total_pendente > 0:
        taxa_inadimplencia = (nf_vencidas_valor / total_pendente) * 100
    else:
        taxa_inadimplencia = 0
    
    context = {
        'conta_atual': conta_atual,
        'periodo_dias': dias,
        'data_inicio': data_inicio,
        
        # Métricas de crescimento
        'faturamento_atual': faturamento_atual,
        'faturamento_anterior': faturamento_anterior,
        'crescimento_faturamento': crescimento_faturamento,
        
        # Rankings
        'top_empresas': top_empresas,
        
        # Análise financeira
        'nf_vencidas_valor': nf_vencidas_valor,
        'taxa_inadimplencia': taxa_inadimplencia,
        'total_pendente': total_pendente,
    }
    
    return render(request, 'dashboard/relatorio_executivo.html', context)
