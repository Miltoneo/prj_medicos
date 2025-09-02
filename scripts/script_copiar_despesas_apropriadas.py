#!/usr/bin/env python3
"""
Script para copiar despesas apropriadas dos sócios para o extrato de movimentação da conta corrente.

Este script replica a lógica exata da tela "Despesas Apropriadas dos Sócios" e inclui:
1. Despesas individuais de sócio (DespesaSocio)
2. Despesas rateadas com valor apropriado para cada sócio (DespesaRateada com rateio)

Características:
- Evita duplicações verificando se já existe lançamento
- Descrição: "Débito " + descrição da despesa
- Considera apenas valores apropriados > 0
- Permite filtrar por empresa, sócio e competência

Uso:
python script_copiar_despesas_apropriadas.py --empresa_id 5 --socio_id 10 --competencia 2025-08
python script_copiar_despesas_apropriadas.py --empresa_id 5 --competencia 2025-08  # todos os sócios
"""

import os
import sys
import django
import argparse
from decimal import Decimal
from datetime import datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import (
    DespesaSocio, 
    DespesaRateada,
    ItemDespesaRateioMensal,
    MovimentacaoContaCorrente, 
    DescricaoMovimentacaoFinanceira,
    MeioPagamento,
    Socio,
    Empresa
)
from django.db import transaction


class DespesaApropriada:
    """Classe para representar uma despesa apropriada (individual ou rateada)"""
    def __init__(self, data, socio, descricao, grupo, valor_total, taxa_rateio, valor_apropriado, origem_id=None, origem_tipo=None):
        self.data = data
        self.socio = socio
        self.descricao = descricao
        self.grupo = grupo
        self.valor_total = valor_total
        self.taxa_rateio = taxa_rateio
        self.valor_apropriado = valor_apropriado
        self.origem_id = origem_id  # ID da DespesaSocio ou DespesaRateada
        self.origem_tipo = origem_tipo  # 'socio' ou 'rateada'
    
    def __str__(self):
        socio_nome = getattr(getattr(self.socio, 'pessoa', None), 'name', str(self.socio))
        return f"{self.data} | {socio_nome} | {self.descricao} | R$ {self.valor_apropriado:,.2f}"


def obter_ou_criar_descricao_especifica(empresa, descricao_despesa):
    """Obtém ou cria descrição específica para cada tipo de despesa"""
    descricao_formatada = f"Débito {descricao_despesa}"
    
    descricao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
        empresa=empresa,
        descricao=descricao_formatada,
        defaults={
            'empresa': empresa,
            'descricao': descricao_formatada,
            'codigo_contabil': '3.1.1.00.00',
            'observacoes': f'Lançamento automático de despesa: {descricao_despesa}'
        }
    )
    
    return descricao


def obter_meio_pagamento_padrao(empresa):
    """Obtém o meio de pagamento padrão"""
    meio_pagamento = MeioPagamento.objects.filter(empresa=empresa, ativo=True).first()
    if not meio_pagamento:
        meio_pagamento = MeioPagamento.objects.create(
            empresa=empresa,
            codigo="DEBITO_APROPRIADO",
            nome="Débito Apropriado",
            observacoes="Meio de pagamento para despesas apropriadas aos sócios",
            ativo=True
        )
        print(f"✓ Criado meio de pagamento: {meio_pagamento.nome}")
    
    return meio_pagamento


def obter_despesas_apropriadas(empresa_id, socio_id=None, competencia=None):
    """
    Obtém todas as despesas apropriadas para um sócio ou empresa.
    Replica exatamente a lógica da view ListaDespesasSocioView.
    """
    print(f"🔍 Buscando despesas apropriadas...")
    print(f"   Empresa ID: {empresa_id}")
    print(f"   Sócio ID: {socio_id or 'Todos'}")
    print(f"   Competência: {competencia or 'Todas'}")
    
    despesas_apropriadas = []
    
    # Filtrar sócios
    if socio_id:
        socios = [Socio.objects.get(id=socio_id, empresa_id=empresa_id, ativo=True)]
    else:
        socios = Socio.objects.filter(empresa_id=empresa_id, ativo=True).order_by('pessoa__name')
    
    for socio in socios:
        print(f"\n👤 Processando sócio: {getattr(getattr(socio, 'pessoa', None), 'name', str(socio))}")
        
        # 1. DESPESAS INDIVIDUAIS DO SÓCIO (DespesaSocio)
        despesas_individuais = DespesaSocio.objects.filter(
            socio=socio,
            socio__empresa_id=empresa_id
        )
        
        if competencia:
            try:
                ano, mes = competencia.split('-')
                despesas_individuais = despesas_individuais.filter(data__year=ano, data__month=mes)
            except Exception:
                pass
        
        despesas_individuais = despesas_individuais.select_related('socio', 'item_despesa', 'item_despesa__grupo_despesa')
        
        for d in despesas_individuais:
            if d.valor > 0:  # Apenas valores positivos
                despesa_apropriada = DespesaApropriada(
                    data=d.data,
                    socio=d.socio,
                    descricao=getattr(d.item_despesa, 'descricao', '-'),
                    grupo=getattr(getattr(d.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                    valor_total=d.valor,
                    taxa_rateio='-',
                    valor_apropriado=d.valor,
                    origem_id=d.id,
                    origem_tipo='socio'
                )
                despesas_apropriadas.append(despesa_apropriada)
        
        # 2. DESPESAS RATEADAS COM APROPRIAÇÃO PARA O SÓCIO (DespesaRateada)
        if competencia:
            try:
                ano, mes = competencia.split('-')
                
                # Buscar todas as despesas rateadas da empresa no mês
                rateadas_qs = DespesaRateada.objects.filter(
                    item_despesa__grupo_despesa__empresa_id=empresa_id,
                    data__year=ano, data__month=mes
                ).select_related('item_despesa', 'item_despesa__grupo_despesa')
                
                for despesa in rateadas_qs:
                    # Para cada despesa rateada, buscar configuração de rateio do sócio
                    try:
                        rateio = ItemDespesaRateioMensal.obter_rateio_para_despesa(
                            despesa.item_despesa, socio, despesa.data
                        )
                        
                        if rateio is not None and rateio.percentual_rateio > 0:
                            valor_apropriado = despesa.valor * (rateio.percentual_rateio / 100)
                            
                            despesa_apropriada = DespesaApropriada(
                                data=despesa.data,
                                socio=socio,
                                descricao=getattr(despesa.item_despesa, 'descricao', '-'),
                                grupo=getattr(getattr(despesa.item_despesa, 'grupo_despesa', None), 'descricao', '-'),
                                valor_total=despesa.valor,
                                taxa_rateio=rateio.percentual_rateio,
                                valor_apropriado=valor_apropriado,
                                origem_id=despesa.id,
                                origem_tipo='rateada'
                            )
                            despesas_apropriadas.append(despesa_apropriada)
                    
                    except Exception as e:
                        print(f"   ⚠️  Erro ao processar rateio para despesa ID {despesa.id}: {e}")
            
            except Exception as e:
                print(f"   ⚠️  Erro ao processar competência {competencia}: {e}")
        
        print(f"   📊 Despesas encontradas para este sócio: {len([d for d in despesas_apropriadas if d.socio == socio])}")
    
    return despesas_apropriadas


def verificar_lancamento_existe(despesa_apropriada):
    """Verifica se já existe lançamento para esta despesa apropriada"""
    # Criar identificador único baseado na origem
    if despesa_apropriada.origem_tipo == 'socio':
        identificador = f"DespesaSocio ID: {despesa_apropriada.origem_id}"
    else:
        identificador = f"DespesaRateada ID: {despesa_apropriada.origem_id} - Sócio ID: {despesa_apropriada.socio.id}"
    
    existe = MovimentacaoContaCorrente.objects.filter(
        socio=despesa_apropriada.socio,
        historico_complementar__icontains=identificador
    ).exists()
    
    return existe, identificador


def criar_lancamento_conta_corrente(despesa_apropriada, empresa, meio_pagamento):
    """Cria um lançamento na conta corrente para a despesa apropriada"""
    try:
        # Verificar se já existe
        ja_existe, identificador = verificar_lancamento_existe(despesa_apropriada)
        if ja_existe:
            return False, f"Lançamento já existe: {identificador}"
        
        # Obter descrição específica para esta despesa
        descricao_movimentacao = obter_ou_criar_descricao_especifica(empresa, despesa_apropriada.descricao)
        
        # Criar histórico complementar detalhado  
        historico = identificador
        if despesa_apropriada.origem_tipo == 'rateada':
            historico += f" - Taxa: {despesa_apropriada.taxa_rateio}%"
        
        # Criar o lançamento
        movimentacao = MovimentacaoContaCorrente.objects.create(
            descricao_movimentacao=descricao_movimentacao,
            instrumento_bancario=meio_pagamento,
            socio=despesa_apropriada.socio,
            data_movimentacao=despesa_apropriada.data,
            valor=-abs(despesa_apropriada.valor_apropriado),  # Negativo = débito = saída da conta
            numero_documento_bancario="",
            historico_complementar=historico,
            conciliado=False,
            data_conciliacao=None
        )
        
        return True, f"Lançamento criado: ID {movimentacao.id}, Valor: R$ {despesa_apropriada.valor_apropriado:,.2f}"
        
    except Exception as e:
        return False, f"Erro ao criar lançamento: {str(e)}"


def processar_despesas_apropriadas(empresa_id, socio_id=None, competencia=None):
    """Processa todas as despesas apropriadas e cria lançamentos na conta corrente"""
    print("=" * 80)
    print("SCRIPT: Copiar Despesas Apropriadas para Conta Corrente")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Validar empresa
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        print(f"🏢 Empresa: {empresa.nome_fantasia or f'ID {empresa.id}'}")
    except Empresa.DoesNotExist:
        print(f"❌ Empresa ID {empresa_id} não encontrada")
        return
    
    # Obter meio de pagamento padrão
    meio_pagamento = obter_meio_pagamento_padrao(empresa)
    
    # Obter despesas apropriadas
    despesas_apropriadas = obter_despesas_apropriadas(empresa_id, socio_id, competencia)
    
    if not despesas_apropriadas:
        print("⚠️  Nenhuma despesa apropriada encontrada")
        return
    
    print(f"\n📊 Total de despesas apropriadas encontradas: {len(despesas_apropriadas)}")
    
    # Processar cada despesa apropriada
    sucessos = 0
    ja_existentes = 0
    erros = 0
    
    print("\n🔄 Processando despesas apropriadas...")
    print("-" * 80)
    
    with transaction.atomic():
        for i, despesa in enumerate(despesas_apropriadas, 1):
            # Apenas processar se valor apropriado > 0
            if despesa.valor_apropriado <= 0:
                continue
                
            sucesso, mensagem = criar_lancamento_conta_corrente(despesa, empresa, meio_pagamento)
            
            if sucesso:
                sucessos += 1
                status = "✅"
            elif "já existe" in mensagem:
                ja_existentes += 1
                status = "⚠️ "
            else:
                erros += 1
                status = "❌"
            
            # Formatar taxa de rateio
            taxa_str = f"{despesa.taxa_rateio}%" if despesa.taxa_rateio != '-' else despesa.taxa_rateio
            
            print(f"{status} [{i:3d}/{len(despesas_apropriadas)}] {despesa.data} | {getattr(getattr(despesa.socio, 'pessoa', None), 'name', str(despesa.socio))} | R$ {despesa.valor_apropriado:,.2f} | {despesa.descricao}")
            
            # Mostrar detalhes dos erros
            if not sucesso and "já existe" not in mensagem:
                print(f"      └─ {mensagem}")
    
    # Resumo final
    print("-" * 80)
    print("📊 RESUMO FINAL:")
    print(f"✅ Lançamentos criados: {sucessos}")
    print(f"⚠️  Já existiam: {ja_existentes}")
    print(f"❌ Erros: {erros}")
    print(f"📈 Total processado: {sucessos + ja_existentes + erros}")
    
    if sucessos > 0:
        total_valor = sum(d.valor_apropriado for d in despesas_apropriadas if d.valor_apropriado > 0)
        print(f"💰 Valor total dos lançamentos: R$ {total_valor:,.2f}")
    
    print(f"📅 Data/Hora de conclusão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)


def main():
    """Função principal com argumentos de linha de comando"""
    parser = argparse.ArgumentParser(description="Copiar despesas apropriadas para conta corrente")
    parser.add_argument('--empresa_id', type=int, required=True, help='ID da empresa')
    parser.add_argument('--socio_id', type=int, help='ID do sócio (opcional, se não informado processa todos)')
    parser.add_argument('--competencia', type=str, help='Competência no formato YYYY-MM (ex: 2025-08)')
    
    args = parser.parse_args()
    
    try:
        processar_despesas_apropriadas(args.empresa_id, args.socio_id, args.competencia)
    except Exception as e:
        print(f"❌ Erro crítico: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
