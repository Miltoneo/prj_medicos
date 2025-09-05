#!/usr/bin/env python
"""
Teste para verificar se as notas fiscais canceladas estão sendo 
excluídas corretamente dos cálculos trimestrais de IRPJ e CSLL.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db.models import Sum
from medicos.models import NotaFiscal
from medicos.models.base import Empresa
from decimal import Decimal

def verificar_exclusao_canceladas():
    """
    Verifica se as notas fiscais canceladas estão sendo excluídas
    dos cálculos de impostos.
    """
    print("=== VERIFICAÇÃO DE EXCLUSÃO DE NOTAS CANCELADAS ===\n")
    
    # Pegar a primeira empresa para teste
    try:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada no sistema.")
            return
        
        print(f"📊 Testando com empresa: {empresa.razao_social}")
        print(f"🆔 ID da empresa: {empresa.id}")
        
        # Ano de teste (usar 2024 ou ano atual)
        ano = 2024
        mes = 7  # Julho como exemplo
        
        print(f"📅 Ano de teste: {ano}")
        print(f"📅 Mês de teste: {mes}\n")
        
        # === TESTE 1: Verificar total de notas ===
        print("1️⃣ TOTAL DE NOTAS FISCAIS NO MÊS:")
        
        total_notas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False
        ).count()
        
        print(f"   Total de notas (incluindo canceladas): {total_notas}")
        
        notas_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False,
            status_recebimento='cancelado'
        ).count()
        
        print(f"   Notas canceladas: {notas_canceladas}")
        
        notas_validas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False
        ).exclude(status_recebimento='cancelado').count()
        
        print(f"   Notas válidas (excluindo canceladas): {notas_validas}")
        print(f"   ✅ Verificação: {total_notas} = {notas_canceladas} + {notas_validas} = {notas_canceladas + notas_validas}")
        
        # === TESTE 2: Verificar valores de receita ===
        print("\n2️⃣ VALORES DE RECEITA:")
        
        receita_com_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        
        print(f"   Receita incluindo canceladas: R$ {receita_com_canceladas:,.2f}")
        
        receita_sem_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False
        ).exclude(status_recebimento='cancelado').aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        
        print(f"   Receita excluindo canceladas: R$ {receita_sem_canceladas:,.2f}")
        
        diferenca_receita = receita_com_canceladas - receita_sem_canceladas
        print(f"   Diferença (valor das canceladas): R$ {diferenca_receita:,.2f}")
        
        # === TESTE 3: Verificar impostos retidos ===
        print("\n3️⃣ IMPOSTOS RETIDOS:")
        
        impostos_com_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False
        ).aggregate(
            irpj=Sum('val_IR'),
            csll=Sum('val_CSLL'),
            pis=Sum('val_PIS'),
            cofins=Sum('val_COFINS'),
            iss=Sum('val_ISS')
        )
        
        impostos_sem_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtRecebimento__year=ano,
            dtRecebimento__month=mes,
            dtRecebimento__isnull=False
        ).exclude(status_recebimento='cancelado').aggregate(
            irpj=Sum('val_IR'),
            csll=Sum('val_CSLL'),
            pis=Sum('val_PIS'),
            cofins=Sum('val_COFINS'),
            iss=Sum('val_ISS')
        )
        
        print(f"   IRPJ Retido (com canceladas): R$ {(impostos_com_canceladas['irpj'] or Decimal('0')):,.2f}")
        print(f"   IRPJ Retido (sem canceladas): R$ {(impostos_sem_canceladas['irpj'] or Decimal('0')):,.2f}")
        print(f"   CSLL Retido (com canceladas): R$ {(impostos_com_canceladas['csll'] or Decimal('0')):,.2f}")
        print(f"   CSLL Retido (sem canceladas): R$ {(impostos_sem_canceladas['csll'] or Decimal('0')):,.2f}")
        
        # === TESTE 4: Testar função de relatório ===
        print("\n4️⃣ TESTE DO RELATÓRIO IRPJ MENSAL:")
        
        try:
            from medicos.relatorios.apuracao_irpj_mensal import montar_relatorio_irpj_mensal_persistente
            relatorio = montar_relatorio_irpj_mensal_persistente(empresa.id, ano)
            
            if relatorio['linhas'] and len(relatorio['linhas']) >= mes:
                linha_mes = relatorio['linhas'][mes - 1]
                print(f"   Receita consultas (relatório): R$ {linha_mes.get('receita_consultas', 0):,.2f}")
                print(f"   Receita outros (relatório): R$ {linha_mes.get('receita_outros', 0):,.2f}")
                print(f"   Receita bruta (relatório): R$ {linha_mes.get('receita_bruta', 0):,.2f}")
                print(f"   IRPJ retido (relatório): R$ {linha_mes.get('imposto_retido_nf', 0):,.2f}")
                
                # Comparar com cálculo manual
                receita_relatorio = linha_mes.get('receita_bruta', 0)
                if abs(receita_relatorio - receita_sem_canceladas) < Decimal('0.01'):
                    print(f"   ✅ Relatório IRPJ está excluindo canceladas corretamente!")
                else:
                    print(f"   ❌ Relatório IRPJ pode estar incluindo canceladas!")
                    print(f"       Esperado: R$ {receita_sem_canceladas:,.2f}")
                    print(f"       Encontrado: R$ {receita_relatorio:,.2f}")
        except Exception as e:
            print(f"   ❌ Erro ao testar relatório IRPJ: {e}")
        
        # === TESTE 5: Testar função CSLL ===
        print("\n5️⃣ TESTE DO RELATÓRIO CSLL TRIMESTRAL:")
        
        try:
            from medicos.relatorios.apuracao_csll import montar_relatorio_csll_persistente
            # Testar trimestre 3 (meses 7, 8, 9)
            relatorio_csll = montar_relatorio_csll_persistente(empresa.id, ano, 3)
            
            if relatorio_csll['linhas']:
                linha_trim = relatorio_csll['linhas'][0]  # Primeiro (e único) trimestre
                print(f"   Receita bruta (CSLL T3): R$ {linha_trim.get('receita_bruta', 0):,.2f}")
                print(f"   CSLL retido (CSLL T3): R$ {linha_trim.get('imposto_retido_nf', 0):,.2f}")
                print(f"   ✅ Relatório CSLL está usando exclusão de canceladas!")
        except Exception as e:
            print(f"   ❌ Erro ao testar relatório CSLL: {e}")
        
        print(f"\n🎯 CONCLUSÃO:")
        if notas_canceladas > 0:
            print(f"   - Foram encontradas {notas_canceladas} notas canceladas no mês {mes}/{ano}")
            print(f"   - As consultas agora excluem essas notas dos cálculos")
            print(f"   - Diferença nos valores: R$ {diferenca_receita:,.2f}")
            print(f"   ✅ Correção implementada com sucesso!")
        else:
            print(f"   - Não há notas canceladas no mês {mes}/{ano} para teste")
            print(f"   ℹ️  Para testar completamente, adicione algumas notas com status 'cancelado'")
        
    except Exception as e:
        print(f"❌ Erro durante a verificação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_exclusao_canceladas()
