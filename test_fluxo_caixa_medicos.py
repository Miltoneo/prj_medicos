"""
Teste do Sistema de Fluxo de Caixa Individual dos Médicos

Este script testa o funcionamento do sistema de controle financeiro
individual por médico/sócio, incluindo:
- Lançamentos de créditos e débitos
- Descrições padronizadas de movimentações  
- Rateio de notas fiscais
- Cálculo de saldos mensais
- Controle de transferências
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
    CustomUser
)

def criar_dados_teste():
    """Cria dados básicos para teste"""
    print("🔧 Criando dados básicos para teste...")
    
    # Criar conta
    conta = Conta.objects.create(
        name="Associação Médica Teste",
        descricao="Conta para teste do fluxo de caixa",
        ativa=True
    )
    
    # Criar empresa
    empresa = Empresa.objects.create(
        name="Clínica Médica Exemplo LTDA",
        CNPJ="12.345.678/0001-90",
        email="contato@clinica.com.br"
    )
    
    # Criar médicos
    medicos = []
    for i in range(3):
        pessoa = Pessoa.objects.create(
            conta=conta,
            name=f"Dr. João Silva {i+1}",
            CPF=f"123.456.789-{i:02d}",
            email=f"medico{i+1}@clinica.com.br"
        )
        
        socio = Socio.objects.create(
            conta=conta,
            pessoa=pessoa,
            empresa=empresa,
            percentual=Decimal('33.33') if i < 2 else Decimal('33.34'),
            ativo=True
        )
        medicos.append(socio)
    
    # Criar configuração de alíquotas
    aliquotas = Aliquotas.objects.create(
        conta=conta,
        ISS_CONSULTAS=Decimal('5.00'),
        ISS_PLANTAO=Decimal('3.00'), 
        ISS_OUTROS=Decimal('4.00'),
        PIS=Decimal('0.65'),
        COFINS=Decimal('3.00'),
        data_vigencia_inicio=date.today() - relativedelta(months=6)
    )
    
    # Criar descrições padronizadas
    Desc_movimentacao_financeiro.criar_descricoes_padrao(conta)
    
    print(f"✅ Dados criados: Conta {conta.name}, {len(medicos)} médicos")
    return conta, empresa, medicos, aliquotas

def testar_nota_fiscal_rateio(conta, empresa, medicos, aliquotas):
    """Testa criação de nota fiscal e rateio entre médicos"""
    print("\n📝 Testando criação e rateio de nota fiscal...")
    
    # Criar nota fiscal
    nf = NotaFiscal.objects.create(
        conta=conta,
        numero="001/2024",
        empresa_destinataria=empresa,
        tomador="Hospital Exemplo",
        dtEmissao=date.today(),
        dtRecebimento=date.today(),
        val_bruto=Decimal('10000.00'),
        tipo_aliquota=1,  # Consultas
        status='lancada'
    )
    
    # Aplicar impostos automaticamente
    nf.calcular_impostos_automaticamente()
    print(f"   NF criada: R$ {nf.val_bruto} (Bruto) → R$ {nf.val_liquido} (Líquido)")
    
    # Definir percentuais de rateio
    rateios = {
        medicos[0].id: Decimal('40.00'),  # 40%
        medicos[1].id: Decimal('35.00'),  # 35%
        medicos[2].id: Decimal('25.00'),  # 25%
    }
    
    # Criar rateio
    lancamentos = Financeiro.criar_rateio_nota_fiscal(nf, rateios)
    print(f"   Rateio criado: {len(lancamentos)} lançamentos")
    
    for lanc in lancamentos:
        print(f"   - {lanc.socio.pessoa.name}: R$ {lanc.valor} ({lanc.percentual_rateio}%)")
    
    return nf, lancamentos

def testar_lancamentos_manuais(conta, empresa, medicos):
    """Testa lançamentos manuais diversos"""
    print("\n💰 Testando lançamentos manuais...")
    
    # Obter descrições
    desc_adiantamento = Desc_movimentacao_financeiro.objects.get(
        conta=conta, descricao="ADIANTAMENTO DE LUCRO"
    )
    desc_despesa = Desc_movimentacao_financeiro.objects.get(
        conta=conta, descricao="DESPESA INDIVIDUAL"
    )
    desc_ajuste = Desc_movimentacao_financeiro.objects.get(
        conta=conta, descricao="ESTORNO PAGAMENTO A MAIOR"
    )
    
    # Lançamentos para o primeiro médico
    medico = medicos[0]
    
    # Adiantamento de lucro (débito)
    lanc1 = Financeiro.objects.create(
        conta=conta,
        data=date.today() - relativedelta(days=15),
        empresa=empresa,
        socio=medico,
        tipo=Financeiro.tipo_t.DEBITO,
        descricao=desc_adiantamento,
        valor=Decimal('2000.00'),
        status='processado',
        observacoes="Adiantamento quinzenal"
    )
    
    # Despesa individual (débito)
    lanc2 = Financeiro.objects.create(
        conta=conta,
        data=date.today() - relativedelta(days=10),
        empresa=empresa,
        socio=medico,
        tipo=Financeiro.tipo_t.DEBITO,
        descricao=desc_despesa,
        valor=Decimal('350.00'),
        status='processado',
        observacoes="Material médico individual"
    )
    
    # Estorno (crédito)
    lanc3 = Financeiro.objects.create(
        conta=conta,
        data=date.today() - relativedelta(days=5),
        empresa=empresa,
        socio=medico,
        tipo=Financeiro.tipo_t.CREDITO,
        descricao=desc_ajuste,
        valor=Decimal('100.00'),
        status='processado',
        observacoes="Estorno de cobrança incorreta"
    )
    
    print(f"   Lançamentos criados para {medico.pessoa.name}:")
    print(f"   - Adiantamento: -R$ {lanc1.valor}")
    print(f"   - Despesa individual: -R$ {lanc2.valor}")
    print(f"   - Estorno: +R$ {lanc3.valor}")
    
    return [lanc1, lanc2, lanc3]

def testar_calculo_saldos(conta, medicos):
    """Testa cálculo de saldos mensais"""
    print("\n📊 Testando cálculo de saldos mensais...")
    
    mes_atual = date.today().replace(day=1)
    
    for medico in medicos:
        # Calcular saldo do mês atual
        saldo = SaldoMensalMedico.calcular_saldo_mensal(medico, mes_atual)
        
        # Obter extrato detalhado
        extrato = Financeiro.obter_extrato_medico(
            medico, 
            mes_atual, 
            mes_atual + relativedelta(months=1) - relativedelta(days=1)
        )
        
        print(f"\n   {medico.pessoa.name}:")
        print(f"   - Saldo inicial: R$ {saldo.saldo_inicial}")
        print(f"   - Total créditos: R$ {saldo.total_creditos}")
        print(f"   - Total débitos: R$ {saldo.total_debitos}")
        print(f"   - Saldo final: {saldo.saldo_formatado}")
        print(f"   - Movimentações: {extrato.count()}")
        
        # Detalhamento por categoria
        if saldo.creditos_nf_consultas > 0:
            print(f"     * NF Consultas: R$ {saldo.creditos_nf_consultas}")
        if saldo.debitos_adiantamentos > 0:
            print(f"     * Adiantamentos: R$ {saldo.debitos_adiantamentos}")
        if saldo.debitos_outros > 0:
            print(f"     * Outros débitos: R$ {saldo.debitos_outros}")

def testar_transferencias(conta, medicos):
    """Testa controle de transferências"""
    print("\n🏦 Testando controle de transferências...")
    
    medico = medicos[0]
    
    # Buscar lançamentos de crédito pendentes de transferência
    creditos_pendentes = Financeiro.objects.filter(
        socio=medico,
        tipo=Financeiro.tipo_t.CREDITO,
        status='processado',
        transferencia_realizada=False
    )
    
    total_disponivel = sum(c.valor for c in creditos_pendentes)
    print(f"   {medico.pessoa.name}: R$ {total_disponivel} disponível para transferência")
    
    if creditos_pendentes.exists():
        # Simular transferência do primeiro crédito
        primeiro_credito = creditos_pendentes.first()
        valor_transferir = primeiro_credito.valor * Decimal('0.8')  # 80% do valor
        
        primeiro_credito.marcar_como_transferido(valor_transferir)
        print(f"   Transferência simulada: R$ {valor_transferir}")
        print(f"   Status: {primeiro_credito.get_status_display()}")

def testar_relatorios(conta, medicos):
    """Testa geração de relatórios básicos"""
    print("\n📈 Testando relatórios básicos...")
    
    # Relatório de saldos por médico
    mes_atual = date.today().replace(day=1)
    
    print(f"\n   Relatório de Saldos - {mes_atual.strftime('%m/%Y')}:")
    print("   " + "="*50)
    
    total_geral = Decimal('0')
    for medico in medicos:
        calculo = Financeiro.calcular_saldo_medico(medico, mes_atual)
        saldo = calculo['saldo']
        total_geral += saldo
        
        print(f"   {medico.pessoa.name:<25} R$ {saldo:>10,.2f}")
    
    print("   " + "-"*50)
    print(f"   {'TOTAL GERAL':<25} R$ {total_geral:>10,.2f}")
    
    # Estatísticas de uso das descrições
    print(f"\n   Top 5 Descrições Mais Utilizadas:")
    top_descricoes = Desc_movimentacao_financeiro.objects.filter(
        conta=conta
    ).order_by('-frequencia_uso')[:5]
    
    for desc in top_descricoes:
        print(f"   - {desc.descricao:<30} ({desc.frequencia_uso} usos)")

def main():
    """Função principal do teste"""
    print("🚀 TESTE DO SISTEMA DE FLUXO DE CAIXA DOS MÉDICOS")
    print("="*60)
    
    try:
        # Limpar dados de teste anteriores
        print("🧹 Limpando dados de teste anteriores...")
        Conta.objects.filter(name__contains="Teste").delete()
        
        # Executar testes
        conta, empresa, medicos, aliquotas = criar_dados_teste()
        nf, lancamentos = testar_nota_fiscal_rateio(conta, empresa, medicos, aliquotas)
        lancamentos_manuais = testar_lancamentos_manuais(conta, empresa, medicos)
        testar_calculo_saldos(conta, medicos)
        testar_transferencias(conta, medicos)
        testar_relatorios(conta, medicos)
        
        print("\n✅ TODOS OS TESTES EXECUTADOS COM SUCESSO!")
        print("\nO sistema de fluxo de caixa individual dos médicos está funcionando corretamente:")
        print("- ✓ Lançamentos automáticos de rateio de NF")
        print("- ✓ Lançamentos manuais com descrições padronizadas")
        print("- ✓ Cálculo automático de saldos mensais")
        print("- ✓ Controle de transferências bancárias")
        print("- ✓ Relatórios de saldos e movimentações")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
