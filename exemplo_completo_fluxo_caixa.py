"""
Exemplo Prático: Sistema de Fluxo de Caixa Individual dos Médicos

Este exemplo demonstra o uso completo do sistema de controle financeiro
individual por médico, mostrando desde o setup inicial até operações avançadas.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# Configurar Django
sys.path.append('f:/Projects/Django/prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import (
    Conta, Pessoa, Empresa, Socio, NotaFiscal, Aliquotas,
    Desc_movimentacao_financeiro, Financeiro, SaldoMensalMedico,
    Despesa, Despesa_Item, Despesa_Grupo
)

def exemplo_completo_fluxo_caixa():
    """
    Exemplo completo do sistema de fluxo de caixa dos médicos
    """
    print("💰 EXEMPLO PRÁTICO: SISTEMA DE FLUXO DE CAIXA DOS MÉDICOS")
    print("="*70)
    
    # === 1. SETUP INICIAL ===
    print("\n🔧 1. CONFIGURAÇÃO INICIAL")
    print("-" * 40)
    
    # Criar conta (organização/associação)
    conta = Conta.objects.create(
        name="Associação Médica São Paulo",
        descricao="Associação de médicos especialistas",
        ativa=True
    )
    print(f"✓ Conta criada: {conta.name}")
    
    # Criar empresa
    empresa = Empresa.objects.create(
        name="AMSP - Associação Médica São Paulo LTDA",
        CNPJ="12.345.678/0001-90",
        email="contato@amsp.com.br"
    )
    print(f"✓ Empresa criada: {empresa.name}")
    
    # Criar médicos
    medicos_data = [
        ("Dr. João Cardiologista", "123.456.789-01", "joao@amsp.com.br"),
        ("Dra. Maria Neurologista", "123.456.789-02", "maria@amsp.com.br"),
        ("Dr. Carlos Ortopedista", "123.456.789-03", "carlos@amsp.com.br"),
    ]
    
    medicos = []
    for nome, cpf, email in medicos_data:
        pessoa = Pessoa.objects.create(
            conta=conta,
            name=nome,
            CPF=cpf,
            email=email
        )
        
        socio = Socio.objects.create(
            conta=conta,
            pessoa=pessoa,
            empresa=empresa,
            percentual=Decimal('33.33'),
            ativo=True
        )
        medicos.append(socio)
        print(f"✓ Médico criado: {nome}")
    
    # Configurar alíquotas tributárias
    aliquotas = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('5.00'),    # 5% para consultas
        ISS_PLANTAO=Decimal('3.00'),      # 3% para plantão  
        ISS_OUTROS=Decimal('4.00'),       # 4% para outros serviços
        PIS=Decimal('0.65'),
        COFINS=Decimal('3.00'),
        data_vigencia_inicio=date.today() - relativedelta(months=6)
    )
    print(f"✓ Alíquotas configuradas: ISS Consultas {aliquotas.ISS_CONSULTAS}%")
    
    # Criar descrições padronizadas
    descricoes_criadas = Desc_movimentacao_financeiro.criar_descricoes_padrao(conta)
    print(f"✓ {descricoes_criadas} descrições padronizadas criadas")
    
    # === 2. PROCESSAMENTO DE NOTA FISCAL ===
    print("\n📝 2. PROCESSAMENTO DE NOTA FISCAL")
    print("-" * 40)
    
    # Criar nota fiscal de consultas
    nf_consultas = NotaFiscal.objects.create(
        conta=conta,
        numero="NF-001/2024",
        empresa_destinataria=empresa,
        tomador="Hospital São Paulo",
        dtEmissao=date.today(),
        dtRecebimento=date.today(),
        val_bruto=Decimal('15000.00'),
        tipo_aliquota=1,  # Consultas médicas
        descricao_servicos="Consultas médicas especializadas - Janeiro 2024",
        status='lancada'
    )
    
    # Calcular impostos automaticamente
    nf_consultas.calcular_impostos_automaticamente()
    print(f"✓ NF Consultas criada:")
    print(f"  - Valor Bruto: R$ {nf_consultas.val_bruto}")
    print(f"  - ISS (5%): R$ {nf_consultas.val_ISS}")
    print(f"  - Valor Líquido: R$ {nf_consultas.val_liquido}")
    
    # Definir rateio personalizado
    rateio_consultas = {
        medicos[0].id: Decimal('50.00'),  # Dr. João: 50%
        medicos[1].id: Decimal('30.00'),  # Dra. Maria: 30%
        medicos[2].id: Decimal('20.00'),  # Dr. Carlos: 20%
    }
    
    # Executar rateio
    lancamentos_nf = Financeiro.criar_rateio_nota_fiscal(
        nf_consultas, 
        rateio_consultas
    )
    
    print(f"✓ Rateio executado - {len(lancamentos_nf)} lançamentos:")
    for lanc in lancamentos_nf:
        print(f"  - {lanc.socio.pessoa.name}: R$ {lanc.valor} ({lanc.percentual_rateio}%)")
    
    # === 3. NOTA FISCAL DE PLANTÃO ===
    print("\n🏥 3. NOTA FISCAL DE PLANTÃO")
    print("-" * 40)
    
    nf_plantao = NotaFiscal.objects.create(
        conta=conta,
        numero="NF-002/2024",
        empresa_destinataria=empresa,
        tomador="Pronto Socorro Central",
        dtEmissao=date.today() - relativedelta(days=5),
        dtRecebimento=date.today() - relativedelta(days=3),
        val_bruto=Decimal('8000.00'),
        tipo_aliquota=2,  # Plantão médico
        descricao_servicos="Plantão médico de emergência - Final de semana",
        status='lancada'
    )
    
    nf_plantao.calcular_impostos_automaticamente()
    print(f"✓ NF Plantão criada:")
    print(f"  - Valor Bruto: R$ {nf_plantao.val_bruto}")
    print(f"  - ISS (3%): R$ {nf_plantao.val_ISS}")
    print(f"  - Valor Líquido: R$ {nf_plantao.val_liquido}")
    
    # Rateio igualitário para plantão
    rateio_plantao = {
        medicos[0].id: Decimal('33.33'),
        medicos[1].id: Decimal('33.33'),
        medicos[2].id: Decimal('33.34'),
    }
    
    lancamentos_plantao = Financeiro.criar_rateio_nota_fiscal(
        nf_plantao,
        rateio_plantao
    )
    print(f"✓ Rateio plantão executado")
    
    # === 4. LANÇAMENTOS MANUAIS ===
    print("\n✋ 4. LANÇAMENTOS MANUAIS")
    print("-" * 40)
    
    # Obter descrições
    desc_adiantamento = Desc_movimentacao_financeiro.objects.get(
        conta=conta, descricao="ADIANTAMENTO DE LUCRO"
    )
    desc_cartao = Desc_movimentacao_financeiro.objects.get(
        conta=conta, descricao="PAGAMENTO CARTÃO CRÉDITO"
    )
    desc_estorno = Desc_movimentacao_financeiro.objects.get(
        conta=conta, descricao="ESTORNO PAGAMENTO A MAIOR"
    )
    
    # Adiantamentos para todos os médicos
    print("✓ Processando adiantamentos:")
    for medico in medicos:
        adiantamento = Financeiro.objects.create(
            conta=conta,
            data=date.today() - relativedelta(days=10),
            empresa=empresa,
            socio=medico,
            tipo=Financeiro.tipo_t.DEBITO,
            descricao=desc_adiantamento,
            valor=Decimal('3000.00'),
            status='processado',
            observacoes="Adiantamento mensal de lucro"
        )
        print(f"  - {medico.pessoa.name}: R$ {adiantamento.valor}")
    
    # Recebimento por cartão (Dr. João)
    pagamento_cartao = Financeiro.objects.create(
        conta=conta,
        data=date.today() - relativedelta(days=7),
        empresa=empresa,
        socio=medicos[0],
        tipo=Financeiro.tipo_t.CREDITO,
        descricao=desc_cartao,
        valor=Decimal('1500.00'),
        numero_documento="AUTH-123456",
        forma_pagamento="Cartão Crédito",
        status='processado',
        observacoes="Pagamento particular de consulta"
    )
    print(f"✓ Pagamento cartão registrado: R$ {pagamento_cartao.valor}")
    
    # Estorno (Dra. Maria)
    estorno = Financeiro.objects.create(
        conta=conta,
        data=date.today() - relativedelta(days=2),
        empresa=empresa,
        socio=medicos[1],
        tipo=Financeiro.tipo_t.CREDITO,
        descricao=desc_estorno,
        valor=Decimal('250.00'),
        status='processado',
        observacoes="Estorno de cobrança de material médico"
    )
    print(f"✓ Estorno registrado: R$ {estorno.valor}")
    
    # === 5. CÁLCULO DE SALDOS MENSAIS ===
    print("\n📊 5. RELATÓRIO DE SALDOS MENSAIS")
    print("-" * 40)
    
    mes_atual = date.today().replace(day=1)
    total_geral = Decimal('0')
    
    print(f"Período: {mes_atual.strftime('%B/%Y')}")
    print("=" * 60)
    
    for medico in medicos:
        # Calcular saldo mensal consolidado
        saldo_mensal = SaldoMensalMedico.calcular_saldo_mensal(medico, mes_atual)
        total_geral += saldo_mensal.saldo_final
        
        print(f"\n{medico.pessoa.name}:")
        print(f"  Saldo Inicial:     R$ {saldo_mensal.saldo_inicial:>10,.2f}")
        print(f"  Total Créditos:    R$ {saldo_mensal.total_creditos:>10,.2f}")
        print(f"  Total Débitos:     R$ {saldo_mensal.total_debitos:>10,.2f}")
        print(f"  SALDO FINAL:       R$ {saldo_mensal.saldo_final:>10,.2f}")
        
        # Detalhamento
        if saldo_mensal.creditos_nf_consultas > 0:
            print(f"    • NF Consultas:  R$ {saldo_mensal.creditos_nf_consultas:>8,.2f}")
        if saldo_mensal.creditos_nf_plantao > 0:
            print(f"    • NF Plantão:    R$ {saldo_mensal.creditos_nf_plantao:>8,.2f}")
        if saldo_mensal.creditos_outros > 0:
            print(f"    • Outros créd.:  R$ {saldo_mensal.creditos_outros:>8,.2f}")
        if saldo_mensal.debitos_adiantamentos > 0:
            print(f"    • Adiantamentos: R$ {saldo_mensal.debitos_adiantamentos:>8,.2f}")
    
    print("\n" + "="*60)
    print(f"TOTAL GERAL DE SALDOS: R$ {total_geral:>15,.2f}")
    
    # === 6. EXTRATO DETALHADO ===
    print("\n📋 6. EXTRATO DETALHADO - DR. JOÃO")
    print("-" * 40)
    
    medico_exemplo = medicos[0]
    inicio_mes = mes_atual
    fim_mes = mes_atual + relativedelta(months=1) - relativedelta(days=1)
    
    extrato = Financeiro.obter_extrato_medico(medico_exemplo, inicio_mes, fim_mes)
    
    print(f"Extrato: {medico_exemplo.pessoa.name}")
    print(f"Período: {inicio_mes.strftime('%d/%m/%Y')} a {fim_mes.strftime('%d/%m/%Y')}")
    print("-" * 60)
    
    saldo_acumulado = Decimal('0')
    for movimento in extrato:
        saldo_acumulado += movimento.valor_com_sinal
        tipo_simbolo = "+" if movimento.tipo == Financeiro.tipo_t.CREDITO else "-"
        
        print(f"{movimento.data.strftime('%d/%m')} | "
              f"{tipo_simbolo}R$ {movimento.valor:>8,.2f} | "
              f"{movimento.descricao.descricao:<25} | "
              f"R$ {saldo_acumulado:>8,.2f}")
    
    # === 7. CONTROLE DE TRANSFERÊNCIAS ===
    print("\n🏦 7. CONTROLE DE TRANSFERÊNCIAS")
    print("-" * 40)
    
    # Buscar créditos pendentes de transferência
    for medico in medicos:
        creditos_pendentes = Financeiro.objects.filter(
            socio=medico,
            tipo=Financeiro.tipo_t.CREDITO,
            status='processado',
            transferencia_realizada=False
        )
        
        total_disponivel = sum(c.valor for c in creditos_pendentes)
        
        if total_disponivel > 0:
            print(f"{medico.pessoa.name}:")
            print(f"  Disponível para transferência: R$ {total_disponivel:,.2f}")
            print(f"  Lançamentos pendentes: {creditos_pendentes.count()}")
            
            # Simular transferência parcial
            if creditos_pendentes.exists():
                primeiro_credito = creditos_pendentes.first()
                valor_transferir = primeiro_credito.valor * Decimal('0.9')  # 90% do valor
                
                primeiro_credito.marcar_como_transferido(valor_transferir)
                print(f"  ✓ Transferido: R$ {valor_transferir:,.2f}")
    
    # === 8. ESTATÍSTICAS FINAIS ===
    print("\n📈 8. ESTATÍSTICAS DO SISTEMA")
    print("-" * 40)
    
    # Estatísticas gerais
    total_movimentacoes = Financeiro.objects.filter(conta=conta).count()
    total_creditos = Financeiro.objects.filter(
        conta=conta, tipo=Financeiro.tipo_t.CREDITO
    ).count()
    total_debitos = Financeiro.objects.filter(
        conta=conta, tipo=Financeiro.tipo_t.DEBITO
    ).count()
    
    print(f"Total de movimentações: {total_movimentacoes}")
    print(f"  • Créditos: {total_creditos}")
    print(f"  • Débitos: {total_debitos}")
    
    # Top descrições utilizadas
    print("\nTop 5 descrições mais utilizadas:")
    top_descricoes = Desc_movimentacao_financeiro.objects.filter(
        conta=conta
    ).order_by('-frequencia_uso')[:5]
    
    for i, desc in enumerate(top_descricoes, 1):
        print(f"  {i}. {desc.descricao} ({desc.frequencia_uso} usos)")
    
    print("\n✅ EXEMPLO COMPLETO EXECUTADO COM SUCESSO!")
    print("\nO sistema demonstrou:")
    print("- ✓ Processamento automático de notas fiscais com impostos diferenciados")
    print("- ✓ Rateio flexível entre médicos com percentuais personalizados")
    print("- ✓ Lançamentos manuais com descrições padronizadas")
    print("- ✓ Cálculo automático de saldos mensais consolidados")
    print("- ✓ Controle de transferências bancárias")
    print("- ✓ Extratos detalhados e relatórios gerenciais")
    print("- ✓ Auditoria completa com trilha de todas as operações")

def limpar_dados_exemplo():
    """Limpa os dados criados no exemplo"""
    print("\n🧹 Limpando dados do exemplo...")
    Conta.objects.filter(name__contains="Associação Médica São Paulo").delete()
    print("✓ Dados limpos")

if __name__ == "__main__":
    try:
        # Executar exemplo completo
        exemplo_completo_fluxo_caixa()
        
        # Perguntar se quer limpar os dados
        print("\n" + "="*70)
        resposta = input("Deseja limpar os dados criados no exemplo? (s/N): ").strip().lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            limpar_dados_exemplo()
        else:
            print("📝 Dados mantidos para exploração adicional")
            
    except Exception as e:
        print(f"\n❌ ERRO NO EXEMPLO: {str(e)}")
        import traceback
        traceback.print_exc()
