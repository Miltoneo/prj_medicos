"""
Views para lançamento automático de impostos na conta corrente
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction

from medicos.models.base import Empresa, Socio
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento
from medicos.relatorios.builders import montar_relatorio_mensal_socio
from core.context_processors import empresa_context


@login_required
@require_http_methods(["POST"])
def lancar_impostos_conta_corrente(request, empresa_id, socio_id, mes, ano):
    """
    Cria lançamentos automáticos dos impostos na conta corrente do mês seguinte
    baseado no relatório mensal do sócio.
    """
    print(f"DEBUG: Iniciando lançamento de impostos - empresa_id={empresa_id}, socio_id={socio_id}, mes={mes}, ano={ano}")
    
    try:
        # Validações básicas
        print(f"DEBUG: Buscando empresa {empresa_id}")
        empresa = get_object_or_404(Empresa, id=empresa_id)
        print(f"DEBUG: Empresa encontrada: {empresa.razao_social}")
        
        print(f"DEBUG: Buscando sócio {socio_id}")
        socio = get_object_or_404(Socio, id=socio_id, empresa=empresa)
        print(f"DEBUG: Sócio encontrado: {socio.nome}")
        
        # Validar se o usuário tem acesso à empresa (verificação simplificada)
        print(f"DEBUG: Verificando acesso do usuário à empresa")
        user_has_access = empresa.conta.contamembership_set.filter(
            usuario=request.user,
            ativo=True
        ).exists()
        
        if not user_has_access:
            print(f"DEBUG: Usuário sem acesso à empresa")
            return JsonResponse({
                'success': False,
                'message': 'Acesso negado à empresa.'
            })
        
        print(f"DEBUG: Usuário tem acesso, continuando...")
        
        # Gerar o relatório do mês para obter os valores dos impostos
        print(f"DEBUG: Gerando relatório mensal do sócio")
        try:
            mes_ano = f"{ano}-{mes:02d}"
            print(f"DEBUG: Chamando montar_relatorio_mensal_socio com: empresa_id={empresa_id}, mes_ano={mes_ano}, socio_id={socio_id}")
            relatorio_dict = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)
            relatorio = relatorio_dict.get('relatorio')
            
            if not relatorio:
                print(f"DEBUG: Relatório não encontrado")
                return JsonResponse({
                    'success': False,
                    'message': 'Não foi possível gerar o relatório mensal do sócio.'
                })
            print(f"DEBUG: Relatório gerado com sucesso")
        except Exception as e:
            print(f"DEBUG: Erro ao gerar relatório: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Erro ao gerar relatório: {str(e)}'
            })
        
        # Definir data do lançamento (próximo mês)
        try:
            # Primeiro dia do mês seguinte
            if mes == 12:
                mes_lancamento = 1
                ano_lancamento = ano + 1
            else:
                mes_lancamento = mes + 1
                ano_lancamento = ano
            
            data_lancamento = date(ano_lancamento, mes_lancamento, 15)  # Dia 15 do mês seguinte
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Data de lançamento inválida.'
            })
        
        # Buscar ou criar descrições de movimentação para cada imposto
        descricoes_impostos = {}
        impostos_config = [
            ('PIS', 'Pagamento PIS'),
            ('COFINS', 'Pagamento COFINS'),
            ('IRPJ', 'Pagamento IRPJ'),
            ('CSLL', 'Pagamento CSLL'),
            ('ISSQN', 'Pagamento ISSQN')
        ]
        
        for codigo, descricao in impostos_config:
            desc_obj, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
                empresa=empresa,
                codigo_contabil=f"IMPOSTO_{codigo}",
                defaults={
                    'descricao': descricao,
                    'observacoes': f'Lançamento automático de {descricao.lower()}'
                }
            )
            descricoes_impostos[codigo] = desc_obj
        
        # Buscar ou criar instrumento bancário DARF
        darf, created = MeioPagamento.objects.get_or_create(
            empresa=empresa,
            nome="DARF",
            defaults={
                'descricao': 'Documento de Arrecadação de Receitas Federais'
            }
        )
        
        # Buscar ou criar instrumento bancário para ISSQN
        iss_instrumento, created = MeioPagamento.objects.get_or_create(
            empresa=empresa,
            nome="Guia Municipal",
            defaults={
                'descricao': 'Guia de pagamento municipal (ISSQN)'
            }
        )
        
        # Preparar lançamentos dos impostos
        lancamentos_criados = []
        competencia_str = f"{mes:02d}/{ano}"
        
        impostos_valores = [
            ('PIS', relatorio.total_pis, darf),
            ('COFINS', relatorio.total_cofins, darf),
            ('IRPJ', relatorio.total_irpj, darf),
            ('CSLL', relatorio.total_csll, darf),
            ('ISSQN', relatorio.total_iss, iss_instrumento)
        ]
        
        # Usar transação para garantir consistência
        with transaction.atomic():
            for imposto_nome, valor_a_pagar, instrumento in impostos_valores:
                # Só criar lançamento se há valor a pagar
                if valor_a_pagar and valor_a_pagar > 0:
                    # Verificar se já existe lançamento para este imposto neste período
                    lancamento_existente = MovimentacaoContaCorrente.objects.filter(
                        descricao_movimentacao=descricoes_impostos[imposto_nome],
                        socio=socio,
                        data_movimentacao__year=ano_lancamento,
                        data_movimentacao__month=mes_lancamento,
                        historico_complementar__icontains=competencia_str
                    ).first()
                    
                    if lancamento_existente:
                        continue  # Pula se já existe
                    
                    # Criar o lançamento
                    lancamento = MovimentacaoContaCorrente.objects.create(
                        data_movimentacao=data_lancamento,
                        descricao_movimentacao=descricoes_impostos[imposto_nome],
                        socio=socio,
                        valor=-valor_a_pagar,  # Valor negativo = saída de dinheiro (crédito bancário)
                        historico_complementar=f"Pagamento {imposto_nome} - Competência {competencia_str}",
                        instrumento_bancario=instrumento,
                        conciliado=False
                    )
                    
                    lancamentos_criados.append({
                        'imposto': imposto_nome,
                        'valor': float(valor_a_pagar),
                        'data': data_lancamento.strftime('%d/%m/%Y'),
                        'id': lancamento.id
                    })
        
        if lancamentos_criados:
            return JsonResponse({
                'success': True,
                'message': f'Foram criados {len(lancamentos_criados)} lançamentos de impostos na conta corrente.',
                'lancamentos': lancamentos_criados,
                'total_lancado': sum(l['valor'] for l in lancamentos_criados)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum lançamento foi criado. Verifique se já existem lançamentos para este período ou se há valores a pagar.'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar lançamentos: {str(e)}'
        })


@login_required
def preview_lancamentos_impostos(request, empresa_id, socio_id, mes, ano):
    """
    Visualiza os impostos que serão lançados na conta corrente
    sem efetuar os lançamentos.
    """
    print(f"DEBUG PREVIEW: Iniciando preview - empresa_id={empresa_id}, socio_id={socio_id}, mes={mes}, ano={ano}")
    
    try:
        # Validações básicas
        print(f"DEBUG PREVIEW: Buscando empresa {empresa_id}")
        empresa = get_object_or_404(Empresa, id=empresa_id)
        print(f"DEBUG PREVIEW: Empresa encontrada: {empresa.razao_social}")
        
        print(f"DEBUG PREVIEW: Buscando sócio {socio_id}")
        socio = get_object_or_404(Socio, id=socio_id, empresa=empresa)
        print(f"DEBUG PREVIEW: Sócio encontrado: {socio.nome}")
        
        # Gerar o relatório do mês para obter os valores dos impostos
        print(f"DEBUG PREVIEW: Gerando relatório mensal do sócio")
        try:
            mes_ano = f"{ano}-{mes:02d}"
            print(f"DEBUG PREVIEW: Chamando montar_relatorio_mensal_socio com: empresa_id={empresa_id}, mes_ano={mes_ano}, socio_id={socio_id}")
            relatorio_dict = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)
            relatorio = relatorio_dict.get('relatorio')
            
            if not relatorio:
                print(f"DEBUG PREVIEW: Relatório não encontrado")
                return JsonResponse({
                    'success': False,
                    'message': 'Não foi possível gerar o relatório mensal do sócio.'
                })
            print(f"DEBUG PREVIEW: Relatório gerado com sucesso")
        except Exception as e:
            print(f"DEBUG PREVIEW: Erro ao gerar relatório: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Erro ao gerar relatório: {str(e)}'
            })
        
        # Calcular data do lançamento (próximo mês)
        if mes == 12:
            mes_lancamento = 1
            ano_lancamento = ano + 1
        else:
            mes_lancamento = mes + 1
            ano_lancamento = ano
        
        data_lancamento = date(ano_lancamento, mes_lancamento, 15)
        competencia_str = f"{mes:02d}/{ano}"
        
        # Preparar preview dos lançamentos
        impostos_preview = []
        impostos_valores = [
            ('PIS', relatorio.total_pis),
            ('COFINS', relatorio.total_cofins),
            ('IRPJ', relatorio.total_irpj),
            ('CSLL', relatorio.total_csll),
            ('ISSQN', relatorio.total_iss)
        ]
        
        total_geral = Decimal('0')
        
        for imposto_nome, valor_a_pagar in impostos_valores:
            if valor_a_pagar and valor_a_pagar > 0:
                # Verificar se já existe lançamento
                try:
                    desc_obj = DescricaoMovimentacaoFinanceira.objects.get(
                        empresa=empresa,
                        codigo_contabil=f"IMPOSTO_{imposto_nome}"
                    )
                    ja_existe = MovimentacaoContaCorrente.objects.filter(
                        descricao_movimentacao=desc_obj,
                        socio=socio,
                        data_movimentacao__year=ano_lancamento,
                        data_movimentacao__month=mes_lancamento,
                        historico_complementar__icontains=competencia_str
                    ).exists()
                except DescricaoMovimentacaoFinanceira.DoesNotExist:
                    ja_existe = False
                
                impostos_preview.append({
                    'imposto': imposto_nome,
                    'valor': float(valor_a_pagar),
                    'data_lancamento': data_lancamento.strftime('%d/%m/%Y'),
                    'competencia': competencia_str,
                    'descricao': f"Pagamento {imposto_nome} - Competência {competencia_str}",
                    'instrumento': 'DARF' if imposto_nome != 'ISSQN' else 'Guia Municipal',
                    'ja_existe': ja_existe
                })
                
                if not ja_existe:
                    total_geral += valor_a_pagar
        
        return JsonResponse({
            'success': True,
            'impostos': impostos_preview,
            'total_geral': float(total_geral),
            'socio_nome': socio.pessoa.name,
            'competencia': competencia_str,
            'mes_lancamento': f"{mes_lancamento:02d}/{ano_lancamento}"
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao gerar preview: {str(e)}'
        })
