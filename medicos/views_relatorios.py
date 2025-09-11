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
        'titulo_pagina': 'Relatório Mensal Empresa',
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
    
    # Lançamento automático sempre ativado (sem opções de configuração)
    auto_lancar_impostos = True
    atualizar_lancamentos = True
    
    # Obter dados do relatório com lançamento automático sempre ativado
    relatorio_dict = montar_relatorio_mensal_socio(
        empresa_id, 
        mes_ano, 
        socio_id=socio_id,
        auto_lancar_impostos=auto_lancar_impostos,
        atualizar_lancamentos_existentes=atualizar_lancamentos
    )
    relatorio_obj = relatorio_dict['relatorio']
    
    # Processar movimentações financeiras
    lista_movimentacoes = _processar_movimentacoes_financeiras(relatorio_obj)
    
    # Extrato Conta Corrente removido conforme solicitado
    mes_fechado = False
    
    # Montar dicionário do relatório com todos os dados necessários
    # Carregar Despesas Apropriadas (mesmo código da view despesas_socio_lista)
    from medicos.models.despesas import DespesaSocio, DespesaRateada, ItemDespesaRateioMensal
    despesas_apropriadas = []
    total_despesas_apropriadas = 0
    if socio_id and mes_ano:
        try:
            ano_str, mes_str = mes_ano.split('-')
            ano = int(ano_str)
            mes = int(mes_str)
            
            # Despesas individuais do sócio
            despesas_individuais = DespesaSocio.objects.filter(
                socio_id=socio_id,
                socio__empresa_id=empresa_id,
                data__year=ano, 
                data__month=mes
            ).select_related('socio', 'item_despesa', 'item_despesa__grupo_despesa')

            # Despesas rateadas do sócio
            rateadas_qs = DespesaRateada.objects.filter(
                item_despesa__grupo_despesa__empresa_id=empresa_id,
                data__year=ano, data__month=mes
            ).select_related('item_despesa', 'item_despesa__grupo_despesa')
            
            # Processar despesas rateadas
            for despesa in rateadas_qs:
                rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                    despesa.item_despesa, Socio.objects.get(id=socio_id), despesa.data
                )
                if rateio is not None:
                    valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
                    socio_obj = Socio.objects.get(id=socio_id)
                    item_desc = getattr(despesa.item_despesa, 'descricao', None) or '-'
                    grupo_obj = getattr(despesa.item_despesa, 'grupo_despesa', None)
                    grupo_desc = getattr(grupo_obj, 'descricao', None) or '-'
                    
                    despesas_apropriadas.append({
                        'data': despesa.data,
                        'socio': socio_obj,
                        'descricao': item_desc,
                        'grupo': grupo_desc,
                        'valor_total': despesa.valor,
                        'taxa_rateio': rateio.percentual_rateio,
                        'valor_apropriado': valor_apropriado,
                        'id': None,  # Não permite editar/excluir no relatório
                    })

            # Processar despesas individuais
            for d in despesas_individuais:
                despesas_apropriadas.append({
                    'data': d.data,
                    'socio': d.socio,
                    'descricao': getattr(d.item_despesa, 'descricao', '-'),
                    'grupo': getattr(getattr(d.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    'valor_total': d.valor,
                    'taxa_rateio': '-',
                    'valor_apropriado': d.valor,
                    'id': d.id,
                })
                
            total_despesas_apropriadas = sum([d.get('valor_apropriado', 0) or 0 for d in despesas_apropriadas])
            
            # Ordenar despesas apropriadas por grupo (crescente) e depois por data (decrescente)
            despesas_apropriadas.sort(key=lambda x: (x['grupo'], -x['data'].toordinal() if x['data'] else 0))
            
        except Exception as e:
            print(f"ERROR View: erro ao carregar despesas apropriadas: {e}")
            despesas_apropriadas = []
            total_despesas_apropriadas = 0

    relatorio = {
        'socios': list(socios),
        'socio_id': socio_id,
        'socio_nome': socio_selecionado.pessoa.name if socio_selecionado else '',
        'competencia': mes_ano,
        'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M'),
        # Dados financeiros básicos
        'despesa_geral': getattr(relatorio_obj, 'despesa_geral', 0),
        'despesas_total': getattr(relatorio_obj, 'despesas_total', 0),
        # Despesas Apropriadas (nova funcionalidade)
        'despesas_apropriadas': despesas_apropriadas,
        'total_despesas_apropriadas': total_despesas_apropriadas,
    'movimentacoes_financeiras': lista_movimentacoes,
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
        'titulo_pagina': 'Relatório Mensal do Sócio',
        'valor_adicional_rateio': relatorio_dict.get('valor_adicional_rateio', 0),
        'receita_bruta_socio': relatorio_dict.get('receita_bruta_socio', 0),
        'total_receitas': relatorio_dict.get('total_receitas', 0),
        'total_despesas_outros': relatorio_dict.get('total_despesas_outros', 0),
        # Resultado do lançamento automático de impostos (se solicitado)
        'resultado_lancamento_automatico': relatorio_dict.get('resultado_lancamento_automatico'),
        'auto_lancar_impostos': auto_lancar_impostos,
        # Quadro Resumo Conta Corrente removido
        'mes_fechado': mes_fechado,
    })
    
    # Adicionar contexto de alíquotas
    base_calculo_ir = relatorio.get('base_calculo_ir_total', 0)
    context.update(_obter_contexto_aliquotas(empresa, base_calculo_ir))
    
    # Adicionar parâmetros de data para funcionalidade de lançamento de impostos
    ano_str, mes_str = mes_ano.split('-') if mes_ano and '-' in mes_ano else (None, None)
    if ano_str and mes_str:
        try:
            context.update({
                'mes': int(mes_str),
                'ano': int(ano_str),
            })
        except (ValueError, TypeError):
            # Se há erro na conversão, usar data atual como fallback
            from datetime import datetime
            hoje = datetime.now()
            context.update({
                'mes': hoje.month,
                'ano': hoje.year,
            })
    else:
        # Se mes_ano está vazio, usar data atual
        from datetime import datetime
        hoje = datetime.now()
        context.update({
            'mes': hoje.month,
            'ano': hoje.year,
        })
    
    # Adicionar campos auxiliares para o template
    context.update({
        'base_consultas_medicas': relatorio_dict.get('base_consultas_medicas', 0),
        'base_outros_servicos': relatorio_dict.get('base_outros_servicos', 0),
        'base_consultas_socio_regime': relatorio_dict.get('base_consultas_socio_regime', 0),
        'base_outros_socio_regime': relatorio_dict.get('base_outros_socio_regime', 0),
        # Alíquotas dos impostos
        'aliquota_pis': relatorio_dict.get('aliquota_pis', 0),
        'aliquota_cofins': relatorio_dict.get('aliquota_cofins', 0),
        'aliquota_irpj': relatorio_dict.get('aliquota_irpj', 0),
        'aliquota_csll': relatorio_dict.get('aliquota_csll', 0),
        'aliquota_iss': relatorio_dict.get('aliquota_iss', 0),
    })
    
    return render(request, 'relatorios/relatorio_mensal_socio.html', context)


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
        ).exclude(status_recebimento='cancelado')  # Excluir notas canceladas
        
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
    {'descricao': f'Base consultas ({aliquotas_empresa.IRPJ_PRESUNCAO_CONSULTA}%)', 'valores': [linha.get('base_calculo_consultas', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': f'Base outros ({aliquotas_empresa.IRPJ_PRESUNCAO_OUTROS}%)', 'valores': [linha.get('base_calculo_outros', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'TOTAL BASE DE CALCULO', 'valores': [linha.get('base_calculo', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': f'TOTAL IMPOSTO DEVIDO ({aliquotas_empresa.IRPJ_ALIQUOTA}%)', 'valores': [linha.get('imposto_devido', 0) + linha.get('adicional', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'IMPOSTO RETIDO NF', 'valores': [linha.get('imposto_retido_nf', 0) for linha in relatorio_irpj_mensal['linhas']]},
    {'descricao': 'TOTAL IMPOSTO A PAGAR', 'valores': [linha.get('imposto_a_pagar', 0) for linha in relatorio_irpj_mensal['linhas']]}
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

    # Dados Apuração Trimestral IRPJ (consolidando 3 meses por trimestre)
    # Estrutura: valores mensais + totais trimestrais conforme anexo
    dados_irpj_trimestral = {
        'receita_consultas': [],
        'receita_outros': [],
        'receita_bruta': [],
        'base_consultas': [],
        'base_outros': [],
        'base_calculo': [],
        'rendimentos_aplicacoes': [],
        'base_calculo_total': [],
        'imposto_devido_15': [],
        'adicional_ir': [],
        'total_imposto_devido': [],
        'imposto_retido_nf': [],
        'retencao_aplicacao': [],
        'imposto_a_pagar': [],
    }
    
    # Preparar dados mensais (12 meses) + totais trimestrais (4 trimestres)
    for mes in range(1, 13):  # Meses 1-12
        if mes <= len(relatorio_irpj_mensal['linhas']):
            linha_mes = relatorio_irpj_mensal['linhas'][mes - 1]
            
            receita_consultas = linha_mes.get('receita_consultas', 0)
            receita_outros = linha_mes.get('receita_outros', 0)
            base_calculo = linha_mes.get('base_calculo', 0)
            rendimentos_aplicacoes = linha_mes.get('rendimentos_aplicacoes', 0)
            imposto_devido = linha_mes.get('imposto_devido', 0)
            adicional = linha_mes.get('adicional', 0)
            imposto_retido_nf = linha_mes.get('imposto_retido_nf', 0)
            retencao_aplicacao = linha_mes.get('retencao_aplicacao_financeira', 0)
            
            # Calcular valores derivados usando alíquotas configuradas
            receita_bruta = receita_consultas + receita_outros
            irpj_presuncao_consultas = aliquotas_empresa.IRPJ_PRESUNCAO_CONSULTA / Decimal('100')
            irpj_presuncao_outros = aliquotas_empresa.IRPJ_PRESUNCAO_OUTROS / Decimal('100')
            base_consultas = receita_consultas * irpj_presuncao_consultas
            base_outros = receita_outros * irpj_presuncao_outros
            base_calculo_total = base_calculo + rendimentos_aplicacoes
            total_imposto_devido = imposto_devido + adicional
            imposto_a_pagar = total_imposto_devido - imposto_retido_nf - retencao_aplicacao
            
            # Adicionar aos arrays
            dados_irpj_trimestral['receita_consultas'].append(receita_consultas)
            dados_irpj_trimestral['receita_outros'].append(receita_outros)
            dados_irpj_trimestral['receita_bruta'].append(receita_bruta)
            dados_irpj_trimestral['base_consultas'].append(base_consultas)
            dados_irpj_trimestral['base_outros'].append(base_outros)
            dados_irpj_trimestral['base_calculo'].append(base_calculo)
            dados_irpj_trimestral['rendimentos_aplicacoes'].append(rendimentos_aplicacoes)
            dados_irpj_trimestral['base_calculo_total'].append(base_calculo_total)
            dados_irpj_trimestral['imposto_devido_15'].append(imposto_devido)
            dados_irpj_trimestral['adicional_ir'].append(adicional)
            dados_irpj_trimestral['total_imposto_devido'].append(total_imposto_devido)
            dados_irpj_trimestral['imposto_retido_nf'].append(imposto_retido_nf)
            dados_irpj_trimestral['retencao_aplicacao'].append(retencao_aplicacao)
            dados_irpj_trimestral['imposto_a_pagar'].append(imposto_a_pagar)
        else:
            # Preencher com zeros se não há dados para o mês
            for key in dados_irpj_trimestral.keys():
                dados_irpj_trimestral[key].append(Decimal('0'))
    
    # Calcular totais trimestrais
    totais_trimestrais = {
        'receita_consultas': [],
        'receita_outros': [],
        'receita_bruta': [],
        'base_consultas': [],
        'base_outros': [],
        'base_calculo': [],
        'rendimentos_aplicacoes': [],
        'base_calculo_total': [],
        'imposto_devido_15': [],
        'adicional_ir': [],
        'total_imposto_devido': [],
        'imposto_retido_nf': [],
        'retencao_aplicacao': [],
        'imposto_a_pagar': [],
    }
    
    # Agrupar por trimestres (T1, T2, T3, T4)
    for trimestre_num in range(4):  # 0, 1, 2, 3 para T1, T2, T3, T4
        inicio_idx = trimestre_num * 3
        fim_idx = inicio_idx + 3
        
        for key in totais_trimestrais.keys():
            if key == 'adicional_ir':
                # CORREÇÃO: Adicional de IR deve ser recalculado com base trimestral
                # Não pode ser soma dos mensais pois o limite é trimestral (R$ 60.000,00)
                base_calculo_total_trim = sum(dados_irpj_trimestral['base_calculo_total'][inicio_idx:fim_idx])
                limite_trimestral = Decimal('60000.00')  # R$ 60.000,00/trimestre
                excedente_trim = max(Decimal('0'), base_calculo_total_trim - limite_trimestral)
                adicional_trim = excedente_trim * Decimal('0.10')  # 10%
                totais_trimestrais[key].append(adicional_trim)
            elif key == 'total_imposto_devido':
                # CORREÇÃO: Total imposto devido deve ser recalculado considerando o adicional correto
                imposto_devido_15_trim = sum(dados_irpj_trimestral['imposto_devido_15'][inicio_idx:fim_idx])
                # Obter o adicional recalculado (último valor adicionado)
                adicional_recalculado = totais_trimestrais['adicional_ir'][-1] if totais_trimestrais['adicional_ir'] else Decimal('0')
                total_imposto_trim = imposto_devido_15_trim + adicional_recalculado
                totais_trimestrais[key].append(total_imposto_trim)
            elif key == 'imposto_a_pagar':
                # CORREÇÃO: Imposto a pagar deve ser recalculado considerando o total correto
                # Obter o total imposto devido recalculado (último valor adicionado)
                total_imposto_recalculado = totais_trimestrais['total_imposto_devido'][-1] if totais_trimestrais['total_imposto_devido'] else Decimal('0')
                imposto_retido_trim = sum(dados_irpj_trimestral['imposto_retido_nf'][inicio_idx:fim_idx])
                retencao_aplicacao_trim = sum(dados_irpj_trimestral['retencao_aplicacao'][inicio_idx:fim_idx])
                imposto_a_pagar_trim = total_imposto_recalculado - imposto_retido_trim - retencao_aplicacao_trim
                totais_trimestrais[key].append(imposto_a_pagar_trim)
            else:
                total_trim = sum(dados_irpj_trimestral[key][inicio_idx:fim_idx])
                totais_trimestrais[key].append(total_trim)

    # Dados Apuração Trimestral CSLL (baseado nos MESMOS dados do IRPJ com alíquota diferente)
    dados_csll_trimestral = {
        'receita_consultas': [],
        'receita_outros': [],
        'receita_bruta': [],
        'base_consultas': [],
        'base_outros': [],
        'base_calculo': [],
        'rendimentos_aplicacoes': [],
        'base_calculo_total': [],
        'total_imposto_devido': [],
        'imposto_retido_nf': [],
        'imposto_a_pagar': [],
    }
    
    # Preparar dados mensais CSLL (12 meses) baseados nos MESMOS dados do IRPJ
    for mes in range(1, 13):  # Meses 1-12
        if mes <= len(relatorio_irpj_mensal['linhas']):
            linha_mes = relatorio_irpj_mensal['linhas'][mes - 1]  # USAR IRPJ como source
            
            receita_consultas = linha_mes.get('receita_consultas', 0)
            receita_outros = linha_mes.get('receita_outros', 0)
            base_calculo = linha_mes.get('base_calculo', 0)
            rendimentos_aplicacoes = linha_mes.get('rendimentos_aplicacoes', 0)
            
            # Calcular CSLL baseado nos dados do IRPJ usando alíquotas configuradas
            # CSLL usa alíquota configurada (padrão 9% vs 15% do IRPJ)
            csll_aliquota = aliquotas_empresa.CSLL_ALIQUOTA / Decimal('100')  # Converter % para decimal
            imposto_devido_csll = base_calculo * csll_aliquota
            
            # Buscar retenção CSLL real das notas fiscais (usar o mesmo método da tabela CSLL - Trimestres)
            # CORREÇÃO: Buscar CSLL retido real das notas fiscais do mês para consistência
            from medicos.models import NotaFiscal
            from django.db.models import Sum
            
            # Buscar CSLL retido sempre por data de recebimento (independente do regime)
            notas_recebidas_mes = NotaFiscal.objects.filter(
                empresa_destinataria_id=empresa_id,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False
            ).exclude(status_recebimento='cancelado')  # Excluir notas canceladas
            imposto_retido_nf_csll = notas_recebidas_mes.aggregate(
                total=Sum('val_CSLL')
            )['total'] or Decimal('0')
            
            # Calcular valores derivados usando alíquotas configuradas
            receita_bruta = receita_consultas + receita_outros
            csll_presuncao_consultas = aliquotas_empresa.CSLL_PRESUNCAO_CONSULTA / Decimal('100')
            csll_presuncao_outros = aliquotas_empresa.CSLL_PRESUNCAO_OUTROS / Decimal('100')
            base_consultas = receita_consultas * csll_presuncao_consultas
            base_outros = receita_outros * csll_presuncao_outros
            base_calculo_total = base_calculo + rendimentos_aplicacoes
            total_imposto_devido = imposto_devido_csll  # Só imposto devido, sem adicional
            imposto_a_pagar = total_imposto_devido - imposto_retido_nf_csll
            
            # Adicionar aos arrays
            dados_csll_trimestral['receita_consultas'].append(receita_consultas)
            dados_csll_trimestral['receita_outros'].append(receita_outros)
            dados_csll_trimestral['receita_bruta'].append(receita_bruta)
            dados_csll_trimestral['base_consultas'].append(base_consultas)
            dados_csll_trimestral['base_outros'].append(base_outros)
            dados_csll_trimestral['base_calculo'].append(base_calculo)
            dados_csll_trimestral['rendimentos_aplicacoes'].append(rendimentos_aplicacoes)
            dados_csll_trimestral['base_calculo_total'].append(base_calculo_total)
            dados_csll_trimestral['total_imposto_devido'].append(total_imposto_devido)
            dados_csll_trimestral['imposto_retido_nf'].append(imposto_retido_nf_csll)
            dados_csll_trimestral['imposto_a_pagar'].append(imposto_a_pagar)
        else:
            # Preencher com zeros se não há dados para o mês
            for key in dados_csll_trimestral.keys():
                dados_csll_trimestral[key].append(Decimal('0'))
    
    # Calcular totais trimestrais CSLL
    totais_trimestrais_csll = {
        'receita_consultas': [],
        'receita_outros': [],
        'receita_bruta': [],
        'base_consultas': [],
        'base_outros': [],
        'base_calculo': [],
        'rendimentos_aplicacoes': [],
        'base_calculo_total': [],
        'total_imposto_devido': [],
        'imposto_retido_nf': [],
        'imposto_a_pagar': [],
    }
    
    # Agrupar por trimestres CSLL (T1, T2, T3, T4)
    for trimestre_num in range(4):  # 0, 1, 2, 3 para T1, T2, T3, T4
        inicio_idx = trimestre_num * 3
        fim_idx = inicio_idx + 3
        
        for key in totais_trimestrais_csll.keys():
            total_trim = sum(dados_csll_trimestral[key][inicio_idx:fim_idx])
            totais_trimestrais_csll[key].append(total_trim)
    
    # Calcular dados das notas fiscais recebidas mensalmente  
    def calcular_notas_fiscais_recebidas():
        from medicos.models import NotaFiscal
        from django.db.models import Sum
        
        notas_recebidas = {
            'receita_consultas': [],
            'receita_outros': [],
            'receita_bruta_mensal': [],
            'receita_bruta_trimestral': []
        }
        
        for mes in range(1, 13):
            # Buscar notas fiscais recebidas no mês
            # EXCLUDINDO notas fiscais canceladas da lista de recebidas
            notas_mes = NotaFiscal.objects.filter(
                empresa_destinataria_id=empresa_id,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False
            ).exclude(status_recebimento='cancelado')
            
            # Calcular receitas por tipo de serviço
            receita_consultas = notas_mes.filter(
                tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
            ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
            
            receita_outros = notas_mes.exclude(
                tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
            ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
            
            receita_bruta_mensal = receita_consultas + receita_outros
            
            notas_recebidas['receita_consultas'].append(receita_consultas)
            notas_recebidas['receita_outros'].append(receita_outros)
            notas_recebidas['receita_bruta_mensal'].append(receita_bruta_mensal)
        
        # Calcular totais trimestrais
        trimestres = [(1, [1,2,3]), (2, [4,5,6]), (3, [7,8,9]), (4, [10,11,12])]
        for num_tri, meses in trimestres:
            total_consultas_tri = sum(notas_recebidas['receita_consultas'][mes-1] for mes in meses)
            total_outros_tri = sum(notas_recebidas['receita_outros'][mes-1] for mes in meses)
            total_bruto_tri = total_consultas_tri + total_outros_tri
            notas_recebidas['receita_bruta_trimestral'].append(total_bruto_tri)
        
        return notas_recebidas

    # Calcular dados das notas fiscais recebidas
    notas_fiscais_recebidas = calcular_notas_fiscais_recebidas()

    # Calcular dados das notas fiscais emitidas mensalmente
    def calcular_notas_fiscais_emitidas():
        from medicos.models import NotaFiscal
        from django.db.models import Sum
        
        notas_emitidas = {
            'receita_consultas': [],
            'receita_outros': [],
            'receita_bruta_mensal': [],
            'receita_bruta_trimestral': []
        }
        
        for mes in range(1, 13):
            # Buscar notas fiscais emitidas no mês
            # EXCLUDINDO notas fiscais canceladas da lista de emitidas
            notas_mes = NotaFiscal.objects.filter(
                empresa_destinataria_id=empresa_id,
                dtEmissao__year=ano,
                dtEmissao__month=mes
            ).exclude(status_recebimento='cancelado')
            
            # Calcular receitas por tipo de serviço
            receita_consultas = notas_mes.filter(
                tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
            ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
            
            receita_outros = notas_mes.exclude(
                tipo_servico=NotaFiscal.TIPO_SERVICO_CONSULTAS
            ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
            
            receita_bruta_mensal = receita_consultas + receita_outros
            
            notas_emitidas['receita_consultas'].append(receita_consultas)
            notas_emitidas['receita_outros'].append(receita_outros)
            notas_emitidas['receita_bruta_mensal'].append(receita_bruta_mensal)
        
        # Calcular totais trimestrais
        trimestres = [(1, [1,2,3]), (2, [4,5,6]), (3, [7,8,9]), (4, [10,11,12])]
        for num_tri, meses in trimestres:
            total_consultas_tri = sum(notas_emitidas['receita_consultas'][mes-1] for mes in meses)
            total_outros_tri = sum(notas_emitidas['receita_outros'][mes-1] for mes in meses)
            total_bruto_tri = total_consultas_tri + total_outros_tri
            notas_emitidas['receita_bruta_trimestral'].append(total_bruto_tri)
        
        return notas_emitidas

    # Calcular dados das notas fiscais emitidas
    notas_fiscais_emitidas = calcular_notas_fiscais_emitidas()

    # Calcular impostos retidos mensais por nota fiscal
    def calcular_impostos_retidos_mensais():
        from medicos.models import NotaFiscal
        from django.db.models import Sum
        
        impostos_retidos = {
            'pis': [],
            'cofins': [],
            'irpj': [],
            'csll': [],
            'issqn': [],
            'outros': [],
            'total': []
        }
        
        for mes in range(1, 13):
            # Buscar notas fiscais recebidas no mês
            # EXCLUDINDO notas fiscais canceladas de todos os cálculos
            notas_recebidas = NotaFiscal.objects.filter(
                empresa_destinataria_id=empresa_id,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False
            ).exclude(status_recebimento='cancelado')
            
            # Somar valores retidos por tipo de imposto
            pis_retido = notas_recebidas.aggregate(total=Sum('val_PIS'))['total'] or Decimal('0')
            cofins_retido = notas_recebidas.aggregate(total=Sum('val_COFINS'))['total'] or Decimal('0')
            irpj_retido = notas_recebidas.aggregate(total=Sum('val_IR'))['total'] or Decimal('0')
            csll_retido = notas_recebidas.aggregate(total=Sum('val_CSLL'))['total'] or Decimal('0')
            issqn_retido = notas_recebidas.aggregate(total=Sum('val_ISS'))['total'] or Decimal('0')
            
            # Calcular outros impostos (campos adicionais se houver)
            outros_retido = Decimal('0')  # Pode ser expandido conforme necessário
            
            total_retido = pis_retido + cofins_retido + irpj_retido + csll_retido + issqn_retido + outros_retido
            
            impostos_retidos['pis'].append(pis_retido)
            impostos_retidos['cofins'].append(cofins_retido)
            impostos_retidos['irpj'].append(irpj_retido)
            impostos_retidos['csll'].append(csll_retido)
            impostos_retidos['issqn'].append(issqn_retido)
            impostos_retidos['outros'].append(outros_retido)
            impostos_retidos['total'].append(total_retido)
        
        return impostos_retidos

    # Calcular dados dos impostos retidos
    impostos_retidos = calcular_impostos_retidos_mensais()

    # Calcular impostos retidos especificamente para notas fiscais emitidas
    def calcular_impostos_retidos_emitidas():
        from medicos.models import NotaFiscal
        from django.db.models import Sum
        
        impostos_retidos_emitidas = {
            'pis': [],
            'cofins': [],
            'irpj': [],
            'csll': [],
            'issqn': [],
            'outros': [],
            'total': []
        }
        
        for mes in range(1, 13):
            # Buscar notas fiscais emitidas no mês
            # EXCLUDINDO notas fiscais canceladas de todos os cálculos
            notas_emitidas = NotaFiscal.objects.filter(
                empresa_destinataria_id=empresa_id,
                dtEmissao__year=ano,
                dtEmissao__month=mes
            ).exclude(status_recebimento='cancelado')
            
            # Somar valores retidos por tipo de imposto nas notas emitidas
            pis_retido = notas_emitidas.aggregate(total=Sum('val_PIS'))['total'] or Decimal('0')
            cofins_retido = notas_emitidas.aggregate(total=Sum('val_COFINS'))['total'] or Decimal('0')
            irpj_retido = notas_emitidas.aggregate(total=Sum('val_IR'))['total'] or Decimal('0')
            csll_retido = notas_emitidas.aggregate(total=Sum('val_CSLL'))['total'] or Decimal('0')
            issqn_retido = notas_emitidas.aggregate(total=Sum('val_ISS'))['total'] or Decimal('0')
            
            # Calcular outros impostos (campos adicionais se houver)
            outros_retido = Decimal('0')  # Pode ser expandido conforme necessário
            
            total_retido = pis_retido + cofins_retido + irpj_retido + csll_retido + issqn_retido + outros_retido
            
            impostos_retidos_emitidas['pis'].append(pis_retido)
            impostos_retidos_emitidas['cofins'].append(cofins_retido)
            impostos_retidos_emitidas['irpj'].append(irpj_retido)
            impostos_retidos_emitidas['csll'].append(csll_retido)
            impostos_retidos_emitidas['issqn'].append(issqn_retido)
            impostos_retidos_emitidas['outros'].append(outros_retido)
            impostos_retidos_emitidas['total'].append(total_retido)
        
        return impostos_retidos_emitidas

    # Calcular dados dos impostos retidos para notas emitidas
    impostos_retidos_emitidas = calcular_impostos_retidos_emitidas()

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
        'linhas_irpj': linhas_irpj,
        'linhas_csll': linhas_csll,
        'dados_irpj_trimestral': dados_irpj_trimestral,
        'totais_trimestrais': totais_trimestrais,
        'dados_csll_trimestral': dados_csll_trimestral,
        'totais_trimestrais_csll': totais_trimestrais_csll,
        'espelho_adicional_trimestral': espelho_adicional_trimestral,
        'aliquotas': aliquotas_empresa,
        'notas_fiscais_recebidas': notas_fiscais_recebidas,
        'notas_fiscais_emitidas': notas_fiscais_emitidas,
        'impostos_retidos': impostos_retidos,
        'impostos_retidos_emitidas': impostos_retidos_emitidas,
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
