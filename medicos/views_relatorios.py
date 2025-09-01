"""
Views dos relatórios do sistema Medicos
Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
"""

# Imports padrão Python
from datetime import datetime, date
from decimal import Decimal
import calendar

# Imports de terceiros
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

# Imports locais - Modelos
from medicos.models import Empresa
from medicos.models.base import Socio
from medicos.models.fiscal import NotaFiscal, Aliquotas

# Imports locais - Builders e relatórios
from medicos.relatorios.builders import (
    montar_relatorio_mensal_empresa,
    montar_relatorio_mensal_socio,
    montar_relatorio_issqn,
    montar_relatorio_outros,
)
from medicos.relatorios.builder_executivo import montar_relatorio_executivo_anual
from medicos.relatorios.apuracao_pis import montar_relatorio_pis_persistente
from medicos.relatorios.apuracao_cofins import montar_relatorio_cofins_persistente
from medicos.relatorios.apuracao_irpj import montar_relatorio_irpj_persistente
from medicos.relatorios.apuracao_irpj_mensal import montar_relatorio_irpj_mensal_persistente
from medicos.relatorios.apuracao_csll import montar_relatorio_csll_persistente

# Helpers
def _obter_mes_ano(request):
    """
    Obtém e padroniza o mês/ano do contexto.
    """
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    return mes_ano

def _contexto_base(request, empresa, menu_nome='Relatórios', cenario_nome=None):
    """
    Monta o contexto base padronizado para todas as views de relatório.
    """
    if empresa is None:
        raise ValueError("empresa deve ser passado explicitamente como objeto Empresa pela view.")
    
    mes_ano = _obter_mes_ano(request)
    request.session['menu_nome'] = menu_nome
    request.session['user_id'] = request.user.id
    
    return {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome,
        'empresa': empresa,
        'empresa_id': empresa.id,
        'user': request.user,
    }

# Views
@login_required
def relatorio_executivo(request, empresa_id):
    """
    View simplificada para relatório executivo anual da empresa.
    Agora utiliza builder dedicado para reduzir complexidade.
    Template: relatorios/relatorio_executivo.html
    """
    from medicos.relatorios.builder_executivo import montar_resumo_demonstrativo_socios, montar_relatorio_executivo_anual
    
    empresa = Empresa.objects.get(id=empresa_id)
    dados_relatorio = montar_relatorio_executivo_anual(empresa_id)
    
    # Obter competência do filtro ou usar mês/ano atual
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    
    # Dados do resumo demonstrativo por sócio
    resumo_demonstrativo = montar_resumo_demonstrativo_socios(empresa_id, mes_ano)
    
    context = _contexto_base(request, empresa=empresa, menu_nome='Demonstrativo', cenario_nome='Relatório Executivo')
    context.update({
        'titulo_pagina': 'Relatório Executivo Anual',
        'mes_ano_selecionado': mes_ano,
        **dados_relatorio,  # Spread dos dados do builder
        **resumo_demonstrativo,  # Spread dos dados do resumo
    })
    
    return render(request, 'relatorios/relatorio_executivo.html', context)


@login_required
def relatorio_mensal_empresa(request, empresa_id):
    """
    View padronizada para relatório mensal da empresa.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_empresa.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_mensal_empresa(empresa_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Mensal Empresa')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Relatório Mensal da Empresa',
    })
    return render(request, 'relatorios/relatorio_mensal_empresa.html', context)

def _obter_socio_selecionado(empresa, socio_id_raw):
    """
    Obtém o sócio selecionado ou o primeiro disponível.
    """
    socios = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
    socio_selecionado = None
    socio_id = None
    
    if socio_id_raw:
        try:
            socio_id = int(socio_id_raw)
            socio_selecionado = socios.filter(id=socio_id).first()
        except (ValueError, TypeError):
            socio_selecionado = None
    
    if not socio_selecionado:
        socio_selecionado = socios.first()
        socio_id = socio_selecionado.id if socio_selecionado else None
    
    return socios, socio_selecionado, socio_id

def _processar_movimentacoes_financeiras(relatorio_obj):
    """
    Processa e normaliza movimentações financeiras.
    """
    lista_movimentacoes = getattr(relatorio_obj, 'lista_movimentacoes_financeiras', [])
    for mov in lista_movimentacoes:
        if isinstance(mov, dict):
            if 'tipo' not in mov or mov['tipo'] in (None, ''):
                mov['tipo'] = mov.get('descricao', '-')
        else:
            if not hasattr(mov, 'tipo') or mov.tipo in (None, ''):
                mov.tipo = getattr(mov, 'descricao', '-')
    return lista_movimentacoes

# Views
@login_required
def relatorio_financeiro_empresa(request, empresa_id):
    """View básica para Relatório Financeiro Empresa."""
    empresa = Empresa.objects.get(pk=empresa_id)
    context = {
        'empresa': empresa,
        'empresa_id': empresa_id,
        'titulo_pagina': 'Relatório Financeiro Empresa',
    }
    return render(request, 'relatorios/relatorio_financeiro_empresa.html', context)

def _obter_contexto_aliquotas(empresa, base_calculo_ir):
    """
    Obtém contexto de alíquotas para cálculos de IR.
    """
    try:
        aliquota = Aliquotas.objects.filter(empresa=empresa).first()
        if aliquota:
            valor_base_adicional = aliquota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL
            aliquota_adicional = aliquota.IRPJ_ADICIONAL
            excedente = max(base_calculo_ir - float(valor_base_adicional), 0)
            return {
                'valor_base_adicional': valor_base_adicional,
                'aliquota_adicional': aliquota_adicional,
                'base_calculo_ir': base_calculo_ir,
                'excedente_adicional': excedente,
            }
    except Exception:
        pass
    
    return {
        'valor_base_adicional': 0,
        'aliquota_adicional': 0,
        'base_calculo_ir': 0,
        'excedente_adicional': 0,
    }

@login_required
def relatorio_mensal_socio(request, empresa_id):
    """
    View padronizada para relatório mensal do sócio.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_mensal_socio.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    
    # Obter sócio selecionado
    socio_id_raw = request.GET.get('socio_id')
    socios, socio_selecionado, socio_id = _obter_socio_selecionado(empresa, socio_id_raw)
    
    # Obter dados do relatório
    relatorio_dict = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)
    relatorio_obj = relatorio_dict['relatorio']
    
    # Processar movimentações financeiras
    lista_movimentacoes = _processar_movimentacoes_financeiras(relatorio_obj)
    # Obter movimentações da conta corrente (lançamentos bancários) usando sistema de saldo anterior
    try:
        from medicos.models.conta_corrente import MovimentacaoContaCorrente, SaldoMensalContaCorrente
        from medicos.relatorios.builders import obter_saldo_anterior_conta_corrente
        
        ano_str, mes_str = mes_ano.split('-') if mes_ano and '-' in mes_ano else (None, None)
        if ano_str and mes_str:
            ano = int(ano_str)
            mes = int(mes_str)
            competencia = date(ano, mes, 1)
            
            print(f"DEBUG View: Consultando conta corrente para socio_id={socio_id}, competencia={competencia}")
            
            # 1. Tentar buscar saldo mensal processado (preferencial)
            try:
                saldo_mensal = SaldoMensalContaCorrente.objects.get(
                    empresa_id=empresa_id,
                    socio_id=socio_id,
                    competencia=competencia
                )
                
                # Usar dados do fechamento mensal
                saldo_anterior = saldo_mensal.saldo_anterior
                total_creditos_conta_corrente = saldo_mensal.total_creditos
                total_debitos_conta_corrente = saldo_mensal.total_debitos
                saldo_conta_corrente = saldo_mensal.saldo_final
                mes_fechado = saldo_mensal.fechado
                
                print(f"DEBUG View: Usando saldo mensal processado - fechado={mes_fechado}")
                
            except SaldoMensalContaCorrente.DoesNotExist:
                # 2. Fallback: calcular dinamicamente (mês ainda não processado)
                print("DEBUG View: Saldo mensal não encontrado, calculando dinamicamente")
                
                # Buscar saldo anterior usando builder
                saldo_anterior = obter_saldo_anterior_conta_corrente(empresa_id, socio_id, competencia)
                
                # Movimentações do mês atual
                primeiro_dia = competencia
                ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
                
                movimentacoes_conta_corrente_qs = MovimentacaoContaCorrente.objects.filter(
                    socio_id=socio_id,
                    data_movimentacao__range=[primeiro_dia, ultimo_dia]
                ).select_related('descricao_movimentacao', 'socio', 'instrumento_bancario', 'nota_fiscal').order_by('data_movimentacao', 'id')
                
                movimentacoes_conta_corrente = list(movimentacoes_conta_corrente_qs)
                
                # Calcular totais da conta corrente
                total_creditos_conta_corrente = sum(mov.valor for mov in movimentacoes_conta_corrente_qs if mov.valor > 0)
                total_debitos_conta_corrente = abs(sum(mov.valor for mov in movimentacoes_conta_corrente_qs if mov.valor < 0))
                
                # Calcular saldo da conta corrente: Saldo anterior + Créditos - Débitos
                saldo_conta_corrente = float(saldo_anterior) + float(total_creditos_conta_corrente) - float(total_debitos_conta_corrente)
                mes_fechado = False
            
            print(f"DEBUG View: saldo_anterior = {saldo_anterior}")
            print(f"DEBUG View: total_creditos_conta_corrente = {total_creditos_conta_corrente}")
            print(f"DEBUG View: total_debitos_conta_corrente = {total_debitos_conta_corrente}")
            print(f"DEBUG View: saldo_conta_corrente calculado = {saldo_conta_corrente}")
            
        else:
            print("DEBUG View: mes_ano inválido")
            saldo_anterior = 0
            total_creditos_conta_corrente = 0
            total_debitos_conta_corrente = 0
            saldo_conta_corrente = 0
            mes_fechado = False
            movimentacoes_conta_corrente = []
            
    except Exception as exc:
        # Don't silently swallow exceptions — log them to stdout for debugging during development
        print(f"ERROR View: erro ao consultar conta corrente: {exc}")
        saldo_anterior = 0
        total_creditos_conta_corrente = 0
        total_debitos_conta_corrente = 0
        saldo_conta_corrente = 0
        mes_fechado = False
        movimentacoes_conta_corrente = []
    
    # Montar dicionário do relatório com todos os dados necessários
    # Preferir listas calculadas pelo builder (relatorio_dict) quando presentes
    despesas_sem_rateio_lista = relatorio_dict.get('lista_despesas_sem_rateio') if isinstance(relatorio_dict, dict) else None
    despesas_com_rateio_lista = relatorio_dict.get('lista_despesas_com_rateio') if isinstance(relatorio_dict, dict) else None

    relatorio = {
        'socios': list(socios),
        'socio_id': socio_id,
        'socio_nome': socio_selecionado.pessoa.name if socio_selecionado else '',
        'competencia': mes_ano,
        'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M'),
        # Dados financeiros básicos: preferir valores diretos do builder quando disponíveis
        'despesas_com_rateio': despesas_com_rateio_lista if despesas_com_rateio_lista is not None else getattr(relatorio_obj, 'lista_despesas_com_rateio', []),
        'despesas_sem_rateio': despesas_sem_rateio_lista if despesas_sem_rateio_lista is not None else getattr(relatorio_obj, 'lista_despesas_sem_rateio', []),
        'despesa_com_rateio': getattr(relatorio_obj, 'despesa_com_rateio', 0),
        'despesa_sem_rateio': getattr(relatorio_obj, 'despesa_sem_rateio', 0),
        'despesa_geral': getattr(relatorio_obj, 'despesa_geral', 0),
        'despesas_total': getattr(relatorio_obj, 'despesas_total', 0),
    'movimentacoes_financeiras': lista_movimentacoes,
    'movimentacoes_conta_corrente': movimentacoes_conta_corrente,
    'total_creditos_conta_corrente': total_creditos_conta_corrente,
    'total_debitos_conta_corrente': total_debitos_conta_corrente,
    'saldo_conta_corrente': saldo_conta_corrente,
        'saldo_movimentacao_financeira': getattr(relatorio_obj, 'saldo_movimentacao_financeira', 0),
        'notas_fiscais': getattr(relatorio_obj, 'lista_notas_fiscais', []),
        # Totais da empresa
        'total_notas_emitidas_mes': getattr(relatorio_obj, 'total_notas_emitidas_mes', 0),
        'total_notas_bruto': getattr(relatorio_obj, 'total_notas_bruto', 0),
        'total_notas_liquido': getattr(relatorio_obj, 'total_notas_liquido', 0),
        # Impostos do sócio
        'total_iss': getattr(relatorio_obj, 'total_iss', 0),
        'total_pis': getattr(relatorio_obj, 'total_pis', 0),
        'total_cofins': getattr(relatorio_obj, 'total_cofins', 0),
        'total_irpj': getattr(relatorio_obj, 'total_irpj', 0),
        'total_irpj_adicional': getattr(relatorio_obj, 'total_irpj_adicional', 0),
        'total_csll': getattr(relatorio_obj, 'total_csll', 0),
        # Impostos devidos do sócio
        'total_iss_devido': getattr(relatorio_obj, 'total_iss_devido', 0),
        'total_pis_devido': getattr(relatorio_obj, 'total_pis_devido', 0),
        'total_cofins_devido': getattr(relatorio_obj, 'total_cofins_devido', 0),
        'total_irpj_devido': getattr(relatorio_obj, 'total_irpj_devido', 0),
        'total_csll_devido': getattr(relatorio_obj, 'total_csll_devido', 0),
        'total_iss_retido': getattr(relatorio_obj, 'total_iss_retido', 0),
        'total_pis_retido': getattr(relatorio_obj, 'total_pis_retido', 0),
        'total_cofins_retido': getattr(relatorio_obj, 'total_cofins_retido', 0),
        'total_irpj_retido': getattr(relatorio_obj, 'total_irpj_retido', 0),
        'total_csll_retido': getattr(relatorio_obj, 'total_csll_retido', 0),
        # Dados de apuração
        'receita_bruta_recebida': getattr(relatorio_obj, 'receita_bruta_recebida', 0),
        'receita_liquida': getattr(relatorio_obj, 'receita_liquida', 0),
        'impostos_total': getattr(relatorio_obj, 'impostos_total', 0),
        'impostos_devido_total': getattr(relatorio_obj, 'impostos_devido_total', 0),
        'impostos_retido_total': getattr(relatorio_obj, 'impostos_retido_total', 0),
        'saldo_apurado': getattr(relatorio_obj, 'saldo_apurado', 0),
        'saldo_a_transferir': getattr(relatorio_obj, 'saldo_a_transferir', 0),
        'imposto_provisionado_mes_anterior': getattr(relatorio_obj, 'imposto_provisionado_mes_anterior', 0),
        # Totais das notas fiscais do sócio (para linha de totais da tabela)
        'total_nf_valor_bruto': getattr(relatorio_obj, 'total_nf_valor_bruto', 0),
        'total_nf_iss': getattr(relatorio_obj, 'total_nf_iss', 0),
        'total_nf_pis': getattr(relatorio_obj, 'total_nf_pis', 0),
        'total_nf_cofins': getattr(relatorio_obj, 'total_nf_cofins', 0),
        'total_nf_irpj': getattr(relatorio_obj, 'total_nf_irpj', 0),
        'total_nf_csll': getattr(relatorio_obj, 'total_nf_csll', 0),
        'total_nf_outros': getattr(relatorio_obj, 'total_nf_outros', 0),
        'total_nf_valor_liquido': getattr(relatorio_obj, 'total_nf_valor_liquido', 0),
        # Totais das notas fiscais emitidas do sócio (para linha de totais da tabela)
        'notas_fiscais_emitidas': getattr(relatorio_obj, 'lista_notas_fiscais_emitidas', []),
        'total_nf_emitidas_valor_bruto': getattr(relatorio_obj, 'total_nf_emitidas_valor_bruto', 0),
        'total_nf_emitidas_iss': getattr(relatorio_obj, 'total_nf_emitidas_iss', 0),
        'total_nf_emitidas_pis': getattr(relatorio_obj, 'total_nf_emitidas_pis', 0),
        'total_nf_emitidas_cofins': getattr(relatorio_obj, 'total_nf_emitidas_cofins', 0),
        'total_nf_emitidas_irpj': getattr(relatorio_obj, 'total_nf_emitidas_irpj', 0),
        'total_nf_emitidas_csll': getattr(relatorio_obj, 'total_nf_emitidas_csll', 0),
        'total_nf_emitidas_outros': getattr(relatorio_obj, 'total_nf_emitidas_outros', 0),
        'total_nf_emitidas_valor_liquido': getattr(relatorio_obj, 'total_nf_emitidas_valor_liquido', 0),
        # Campos específicos para o cálculo de IRPJ utilizados no template
        'base_calculo_consultas': relatorio_dict.get('base_calculo_consultas', 0),
        'base_calculo_outros': relatorio_dict.get('base_calculo_outros', 0),
        'base_calculo_ir_total': relatorio_dict.get('base_calculo_ir_total', 0),
        # Faturamento por tipo de serviço
        'faturamento_consultas': getattr(relatorio_obj, 'faturamento_consultas', 0),
        'faturamento_plantao': getattr(relatorio_obj, 'faturamento_plantao', 0),
        'faturamento_outros': getattr(relatorio_obj, 'faturamento_outros', 0),
    }
    # debug prints removed
    
    # Montar contexto final
    context = _contexto_base(request, empresa=empresa, menu_nome='Demonstrativo', cenario_nome='Relatório Mensal Sócio')
    print(f"DEBUG View: total_receitas do relatorio_dict = {relatorio_dict.get('total_receitas', 'NÃO ENCONTRADO')}")
    print(f"DEBUG View: total_despesas_outros do relatorio_dict = {relatorio_dict.get('total_despesas_outros', 'NÃO ENCONTRADO')}")
    print(f"DEBUG View: base_consultas_socio_regime = {relatorio_dict.get('base_consultas_socio_regime', 'NÃO ENCONTRADO')}")
    print(f"DEBUG View: base_outros_socio_regime = {relatorio_dict.get('base_outros_socio_regime', 'NÃO ENCONTRADO')}")
    context.update({
        'relatorio': relatorio,
        # Regra do projeto: título deve ser passado via 'titulo_pagina'
        'titulo_pagina': f"Relatório Mensal do Sócio - {socio_selecionado.pessoa.name if socio_selecionado else ''}",
        'valor_adicional_rateio': relatorio_dict.get('valor_adicional_rateio', 0),
        'participacao_socio_percentual': relatorio_dict.get('participacao_socio_percentual', 0),
        'receita_bruta_socio': relatorio_dict.get('receita_bruta_socio', 0),
        'total_receitas': relatorio_dict.get('total_receitas', 0),
        'total_despesas_outros': relatorio_dict.get('total_despesas_outros', 0),
        # Expor chaves de compatibilidade diretamente no contexto para templates que esperam nomes antigos
        'despesas_sem_rateio': relatorio.get('despesas_sem_rateio', []),
        'despesas_com_rateio': relatorio.get('despesas_com_rateio', []),
        # Campos específicos para o quadro "Resumo Conta Corrente"
        'saldo_anterior': saldo_anterior,
        'total_creditos_conta_corrente': total_creditos_conta_corrente,
        'total_debitos_conta_corrente': total_debitos_conta_corrente,
        'saldo_conta_corrente': saldo_conta_corrente,
        'mes_fechado': mes_fechado,
    })
    
    # Adicionar contexto de alíquotas
    base_calculo_ir = relatorio.get('base_calculo_ir_total', 0)
    context.update(_obter_contexto_aliquotas(empresa, base_calculo_ir))
    
    # Adicionar campos específicos do espelho de cálculo
    context.update({
        'base_calculo_consultas_ir': relatorio_dict.get('base_calculo_consultas_ir', 0),
        'base_calculo_outros_ir': relatorio_dict.get('base_calculo_outros_ir', 0),
        'base_consultas_medicas': relatorio_dict.get('base_consultas_medicas', 0),
        'base_outros_servicos': relatorio_dict.get('base_outros_servicos', 0),
        'base_consultas_socio_regime': relatorio_dict.get('base_consultas_socio_regime', 0),
        'base_outros_socio_regime': relatorio_dict.get('base_outros_socio_regime', 0),
        'valor_base_adicional': relatorio_dict.get('valor_base_adicional', 0),
        'excedente_adicional': relatorio_dict.get('excedente_adicional', 0),
        'aliquota_adicional': relatorio_dict.get('aliquota_adicional', 0),
        # Alíquotas dos impostos
        'aliquota_pis': relatorio_dict.get('aliquota_pis', 0),
        'aliquota_cofins': relatorio_dict.get('aliquota_cofins', 0),
        'aliquota_irpj': relatorio_dict.get('aliquota_irpj', 0),
        'aliquota_csll': relatorio_dict.get('aliquota_csll', 0),
        'aliquota_iss': relatorio_dict.get('aliquota_iss', 0),
    })
    
    return render(request, 'relatorios/relatorio_mensal_socio.html', context)

def calcular_adicional_ir_mensal(empresa_id, ano):
    """
    Calcula o adicional de IR mensal sempre considerando data de emissão das notas.
    Lei 9.249/1995, Art. 3º, §1º - adicional sempre por competência (data emissão).
    """
    empresa = Empresa.objects.get(id=empresa_id)
    aliquotas = Aliquotas.obter_aliquota_vigente(empresa)
    
    resultado_mensal = []
    
    for mes in range(1, 13):
        # ADICIONAL DE IR: SEMPRE considera data de emissão (independente do regime da empresa)
        notas_adicional = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month=mes
        )
        
        # Receitas por tipo de serviço (sempre por data de emissão)
        receita_consultas = notas_adicional.filter(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(
            total=Sum('val_bruto')
        )['total'] or Decimal('0')
        
        receita_outros = notas_adicional.exclude(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(
            total=Sum('val_bruto')
        )['total'] or Decimal('0')
        
        # Base de cálculo aplicando presunções sobre receitas por data de emissão
        base_consultas = receita_consultas * (aliquotas.IRPJ_PRESUNCAO_CONSULTA / Decimal('100'))
        base_outros = receita_outros * (aliquotas.IRPJ_PRESUNCAO_OUTROS / Decimal('100'))
        base_total = base_consultas + base_outros
        
        # Adicional mensal
        limite_mensal = Decimal('20000.00')  # R$ 20.000,00/mês
        excedente = max(Decimal('0'), base_total - limite_mensal)
        adicional = excedente * Decimal('0.10')  # 10%
        
        resultado_mensal.append({
            'mes': mes,
            'receita_consultas': receita_consultas,
            'receita_outros': receita_outros,
            'base_consultas': base_consultas,
            'base_outros': base_outros,
            'base_total': base_total,
            'limite_mensal': limite_mensal,
            'excedente': excedente,
            'adicional': adicional,
        })
    
    return resultado_mensal

def calcular_adicional_ir_trimestral(empresa_id, ano):
    """
    Calcula o adicional de IR trimestral sempre considerando data de emissão das notas.
    Lei 9.249/1995, Art. 3º, §1º - adicional sempre por competência (data emissão).
    """
    empresa = Empresa.objects.get(id=empresa_id)
    aliquotas = Aliquotas.obter_aliquota_vigente(empresa)
    
    # Definir trimestres
    trimestres = [
        (1, [1, 2, 3]),    # T1: Jan, Fev, Mar
        (2, [4, 5, 6]),    # T2: Abr, Mai, Jun
        (3, [7, 8, 9]),    # T3: Jul, Ago, Set
        (4, [10, 11, 12])  # T4: Out, Nov, Dez
    ]
    
    resultado_trimestral = []
    
    for num_tri, meses in trimestres:
        # ADICIONAL DE IR: SEMPRE considera data de emissão (independente do regime da empresa)
        notas_adicional = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses
        )
        
        # Receitas por tipo de serviço (sempre por data de emissão)
        receita_consultas = notas_adicional.filter(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(
            total=Sum('val_bruto')
        )['total'] or Decimal('0')
        
        receita_outros = notas_adicional.exclude(tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS).aggregate(
            total=Sum('val_bruto')
        )['total'] or Decimal('0')
        
        receita_bruta = receita_consultas + receita_outros
        
        # Base de cálculo aplicando presunções sobre receitas por data de emissão
        base_consultas = receita_consultas * (aliquotas.IRPJ_PRESUNCAO_CONSULTA / Decimal('100'))
        base_outros = receita_outros * (aliquotas.IRPJ_PRESUNCAO_OUTROS / Decimal('100'))
        base_total = base_consultas + base_outros
        
        # Adicional trimestral
        limite_trimestral = Decimal('60000.00')  # R$ 60.000,00/trimestre
        excedente = max(Decimal('0'), base_total - limite_trimestral)
        adicional = excedente * Decimal('0.10')  # 10%
        
        resultado_trimestral.append({
            'trimestre': f'T{num_tri}',
            'receita_consultas': receita_consultas,
            'receita_outros': receita_outros,
            'receita_bruta': receita_bruta,
            'base_consultas': base_consultas,
            'base_outros': base_outros,
            'base_total': base_total,
            'limite_trimestral': limite_trimestral,
            'excedente': excedente,
            'adicional': adicional,
        })
    
    return resultado_trimestral

@login_required
def relatorio_apuracao(request, empresa_id):
    """
    View padronizada para apuração de impostos (ISSQN, PIS, COFINS, etc).
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/apuracao_de_impostos.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    ano = mes_ano.split('-')[0] if '-' in mes_ano else mes_ano[:4]
    competencias = [f'{mes:02d}/{ano}' for mes in range(1, 13)]
    trimestres = [f'T{n}' for n in range(1, 5)]
    
    # Relatório ISSQN
    relatorio_issqn = montar_relatorio_issqn(empresa_id, mes_ano)
    # Obter alíquota ISSQN para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_issqn = relatorio_issqn['linhas'][0].get('aliquota', 0) if relatorio_issqn['linhas'] else 0
    linhas_issqn = [
        {'descricao': 'Base cálculo', 'valores': [linha['valor_bruto'] for linha in relatorio_issqn['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_issqn}%)', 'valores': [linha['valor_iss'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha['imposto_retido_nf'] for linha in relatorio_issqn['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha['valor_iss'] - linha['imposto_retido_nf'] for linha in relatorio_issqn['linhas']]},
    ]

    # Relatório PIS
    relatorio_pis = montar_relatorio_pis_persistente(empresa_id, ano)
    # Obter alíquota PIS para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_pis = relatorio_pis['linhas'][0].get('aliquota', 0) if relatorio_pis['linhas'] else 0
    linhas_pis = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_pis}%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_pis['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_pis['linhas']]},
    ]

    # Relatório COFINS
    relatorio_cofins = montar_relatorio_cofins_persistente(empresa_id, ano)
    # Obter alíquota COFINS para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_cofins = relatorio_cofins['linhas'][0].get('aliquota', 0) if relatorio_cofins['linhas'] else 0
    linhas_cofins = [
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': f'Imposto devido ({aliquota_cofins}%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Crédito mês anterior', 'valores': [linha.get('credito_mes_anterior', 0) for linha in relatorio_cofins['linhas']]},
        {'descricao': 'Crédito mês seguinte', 'valores': [linha.get('credito_mes_seguinte', 0) for linha in relatorio_cofins['linhas']]},
    ]

    # Relatório IRPJ Mensal
    relatorio_irpj_mensal = montar_relatorio_irpj_mensal_persistente(empresa_id, ano)
    # Obter alíquota IRPJ para exibir na descrição (geralmente é a mesma para todo o ano)
    aliquota_irpj = relatorio_irpj_mensal['linhas'][0].get('aliquota', 0) if relatorio_irpj_mensal['linhas'] else 0
    
    # Obter alíquotas da empresa para cálculos corretos
    aliquotas_empresa = Aliquotas.obter_aliquota_vigente(empresa)
    
    linhas_irpj_mensal = [
    {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'Base consultas (32%)', 'valores': [linha.get('base_calculo_consultas', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'Base outros (8%)', 'valores': [linha.get('base_calculo_outros', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'TOTAL BASE DE CALCULO', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'TOTAL IMPOSTO DEVIDO (15%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'CALCULO DO ADICIONAL DE IR', 'valores': [linha.get('adicional', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'IMPOSTO RETIDO NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'TOTAL IMPOSTO A PAGAR', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_irpj_mensal['linhas']]},
    ]

    # Espelho do Adicional de IR Mensal (sempre por data de emissão)
    dados_adicional_mensal = calcular_adicional_ir_mensal(empresa_id, ano)
    
    linhas_espelho_adicional_mensal = [
        {'descricao': 'Total notas fiscais emitidas: consultas médicas', 'valores': [dados['receita_consultas'] for dados in dados_adicional_mensal]},
        {'descricao': 'Total notas fiscais emitidas: outros serviços', 'valores': [dados['receita_outros'] for dados in dados_adicional_mensal]},
        {'descricao': 'Base sobre notas fiscais emitidas do tipo "consultas médicas"', 'valores': [dados['base_consultas'] for dados in dados_adicional_mensal]},
        {'descricao': 'Base sobre notas fiscais emitidas do tipo "outros serviços"', 'valores': [dados['base_outros'] for dados in dados_adicional_mensal]},
        {'descricao': 'Total base de cálculo', 'valores': [dados['base_total'] for dados in dados_adicional_mensal]},
        {'descricao': 'Valor base para adicional', 'valores': [dados['limite_mensal'] for dados in dados_adicional_mensal]},
        {'descricao': 'Excedente', 'valores': [dados['excedente'] for dados in dados_adicional_mensal]},
        {'descricao': 'Alíquota de adicional de IR (10%)', 'valores': [Decimal('10.00') for _ in dados_adicional_mensal]},
        {'descricao': 'Total Adicional de IR', 'valores': [dados['adicional'] for dados in dados_adicional_mensal]},
    ]

    # Relatório IRPJ
    relatorio_irpj = montar_relatorio_irpj_persistente(empresa_id, ano)
    linhas_irpj = [
        {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Receita bruta', 'valores': [linha.get('receita_bruta', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Base cálculo', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Rendimentos aplicações', 'valores': [linha.get('rendimentos_aplicacoes', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Base cálculo total', 'valores': [linha.get('base_calculo_total', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Imposto devido', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Adicional', 'valores': [linha.get('adicional', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Retenção aplicação financeira', 'valores': [linha.get('retencao_aplicacao_financeira', 0) for linha in relatorio_irpj['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_irpj['linhas']]},
    ]

    # Relatório CSLL
    relatorio_csll = montar_relatorio_csll_persistente(empresa_id, ano)
    # Obter alíquotas da empresa para exibir percentuais corretos
    aliquotas_empresa = Aliquotas.obter_aliquota_vigente(empresa)
    linhas_csll = [
        {'descricao': 'Receita consultas', 'valores': [linha.get('receita_consultas', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Receita outros', 'valores': [linha.get('receita_outros', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Receita bruta', 'valores': [linha.get('receita_bruta', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': f'Base consultas ({aliquotas_empresa.CSLL_PRESUNCAO_CONSULTA}%)', 'valores': [linha.get('base_calculo_consultas', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': f'Base outros ({aliquotas_empresa.CSLL_PRESUNCAO_OUTROS}%)', 'valores': [linha.get('base_calculo_outros', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'TOTAL BASE DE CALCULO', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Rendimentos aplicações', 'valores': [linha.get('rendimentos_aplicacoes', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Base cálculo total', 'valores': [linha.get('base_calculo_total', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': f'Imposto devido ({aliquotas_empresa.CSLL_ALIQUOTA}%)', 'valores': [linha.get('imposto_devido', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Imposto retido NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_csll['linhas']]},
        {'descricao': 'Imposto a pagar', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_csll['linhas']]},
    ]

    # Espelho do Adicional de IR Trimestral (sempre por data de emissão)
    dados_adicional_trimestral = calcular_adicional_ir_trimestral(empresa_id, ano)
    
    espelho_adicional_trimestral = []
    for dados in dados_adicional_trimestral:
        espelho_adicional_trimestral.append({
            'competencia': dados['trimestre'],
            'receita_bruta': dados['receita_bruta'],
            'receita_consultas': dados['receita_consultas'],
            'receita_outros': dados['receita_outros'],
            'base_calculo_consultas': dados['base_consultas'],
            'base_calculo_outros': dados['base_outros'],
            'base_calculo_total': dados['base_total'],
            'limite_isencao': dados['limite_trimestral'],
            'excedente': dados['excedente'],
            'aliquota_adicional': Decimal('10.00'),
            'adicional_devido': dados['adicional'],
        })

    # Espelho do Adicional de IR Mensal (baseado nos dados da tabela IRPJ Mensal)
    # IMPORTANTE: Usa dados já calculados pelos builders que consideram regime de tributação
    espelho_adicional_mensal = []
    mes_exemplo = 7  # Julho (posição 6 no array, pois começa em 0)
    
    # Usar os dados já calculados do relatório IRPJ Mensal
    if relatorio_irpj_mensal['linhas'] and len(relatorio_irpj_mensal['linhas']) > mes_exemplo - 1:
        linha_julho = relatorio_irpj_mensal['linhas'][mes_exemplo - 1]  # Julho é o índice 6 (7-1)
        
        # Buscar sócios ativos da empresa para mostrar dados individuais baseados na empresa
        socios_ativos = Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name')
        
        # Para o espelho, vamos usar os dados da empresa e dividi-los proporcionalmente pelos sócios
        # (ou usar dados individuais se existirem no relatório)
        receita_consultas_total = linha_julho.get('receita_consultas', 0)
        receita_outros_total = linha_julho.get('receita_outros', 0)
        base_calculo_total = linha_julho.get('base_calculo', 0)
        adicional_total = linha_julho.get('adicional', 0)
        
        # Se há sócios, distribuir proporcionalmente (simplificado para demonstração)
        if socios_ativos.exists():
            num_socios = socios_ativos.count()
            aliquota_config = Aliquotas.objects.filter(empresa=empresa).first()
            limite_adicional = Decimal(str(aliquota_config.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL)) if aliquota_config else Decimal('20000.00')
            
            for socio in socios_ativos:
                # Dividir proporcionalmente pelos sócios (método simplificado)
                receita_consultas_socio = receita_consultas_total / num_socios
                receita_outros_socio = receita_outros_total / num_socios
                base_calculo_socio = base_calculo_total / num_socios
                
                # Calcular excedente e adicional para cada sócio
                excedente_socio = max(base_calculo_socio - limite_adicional, Decimal('0'))
                adicional_socio = adicional_total / num_socios if adicional_total > 0 else Decimal('0')
                
                espelho_adicional_mensal.append({
                    'socio_nome': socio.pessoa.name,
                    'receita_consultas': receita_consultas_socio,
                    'receita_outros': receita_outros_socio,
                    'receita_total': receita_consultas_socio + receita_outros_socio,
                    'base_total': base_calculo_socio,
                    'limite_adicional': limite_adicional,
                    'excedente': excedente_socio,
                    'adicional_devido': adicional_socio,
                })
    
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração de Impostos')
    context.update({
        'ano': ano,
        'competencias': competencias,
        'trimestres': trimestres,
        'linhas_issqn': linhas_issqn,
        'linhas_pis': linhas_pis,
        'totais_pis': relatorio_pis.get('totais', {}),
        'linhas_cofins': linhas_cofins,
        'totais_cofins': relatorio_cofins.get('totais', {}),
        'linhas_irpj_mensal': linhas_irpj_mensal,
        'linhas_espelho_adicional_mensal': linhas_espelho_adicional_mensal,
        'linhas_irpj': linhas_irpj,
        'linhas_csll': linhas_csll,
        'espelho_adicional_trimestral': espelho_adicional_trimestral,
        'espelho_adicional_mensal': espelho_adicional_mensal,
        'titulo_pagina': 'Apuração de Impostos',
    })
    return render(request, 'relatorios/apuracao_de_impostos.html', context)


@login_required
def relatorio_outros(request, empresa_id):
    """
    View padronizada para apuração de outros relatórios.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_outros.html
    """
    empresa = Empresa.objects.get(id=empresa_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_outros(empresa_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Apuração Outros')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Apuração Outros',
    })
    return render(request, 'relatorios/relatorio_outros.html', context)


@login_required
def relatorio_executivo_pdf(request, conta_id):
    """
    View padronizada para geração do PDF do relatório executivo.
    Fonte: .github/documentacao_especifica_instructions.md, seção Relatórios
    Template: relatorios/relatorio_executivo.html
    """
    empresa = Empresa.objects.get(id=conta_id)
    mes_ano = _obter_mes_ano(request)
    relatorio = montar_relatorio_mensal_empresa(conta_id, mes_ano)['relatorio']
    context = _contexto_base(request, empresa=empresa, menu_nome='Relatórios', cenario_nome='Relatório Executivo PDF')
    context.update({
        'relatorio': relatorio,
        'titulo_pagina': 'Relatório Executivo PDF',
    })
    return render(request, 'relatorios/relatorio_executivo.html', context)
