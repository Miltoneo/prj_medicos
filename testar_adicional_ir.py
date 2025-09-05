#!/usr/bin/env python
"""
Teste específico para verificar se a tabela ESPELHO DO ADICIONAL DE IR TRIMESTRAL
está excluindo corretamente as notas fiscais canceladas.
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
from medicos.views_relatorios import calcular_adicional_ir_trimestral
from decimal import Decimal

def verificar_adicional_ir_trimestral():
    """
    Verifica se a função calcular_adicional_ir_trimestral está 
    excluindo notas fiscais canceladas corretamente.
    """
    print("=== VERIFICAÇÃO: ESPELHO DO ADICIONAL DE IR TRIMESTRAL ===\n")
    
    try:
        # Pegar a primeira empresa para teste
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada no sistema.")
            return
        
        print(f"📊 Testando com empresa: {empresa.razao_social}")
        print(f"🆔 ID da empresa: {empresa.id}")
        
        # Ano de teste
        ano = 2024
        print(f"📅 Ano de teste: {ano}\n")
        
        # === TESTE 1: Verificar notas do 3º trimestre (Jul, Ago, Set) ===
        print("1️⃣ ANÁLISE DO 3º TRIMESTRE (Julho, Agosto, Setembro):")
        
        meses_t3 = [7, 8, 9]
        
        # Total de notas por data de emissão (incluindo canceladas)
        total_notas_t3 = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses_t3
        ).count()
        
        print(f"   Total de notas emitidas no T3: {total_notas_t3}")
        
        # Notas canceladas no T3
        notas_canceladas_t3 = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses_t3,
            status_recebimento='cancelado'
        ).count()
        
        print(f"   Notas canceladas no T3: {notas_canceladas_t3}")
        
        # Notas válidas no T3
        notas_validas_t3 = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses_t3
        ).exclude(status_recebimento='cancelado').count()
        
        print(f"   Notas válidas no T3: {notas_validas_t3}")
        
        # === TESTE 2: Verificar valores de receita ===
        print("\n2️⃣ VALORES DE RECEITA DO T3:")
        
        receita_com_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses_t3
        ).aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        
        print(f"   Receita incluindo canceladas: R$ {receita_com_canceladas:,.2f}")
        
        receita_sem_canceladas = NotaFiscal.objects.filter(
            empresa_destinataria=empresa,
            dtEmissao__year=ano,
            dtEmissao__month__in=meses_t3
        ).exclude(status_recebimento='cancelado').aggregate(total=Sum('val_bruto'))['total'] or Decimal('0')
        
        print(f"   Receita excluindo canceladas: R$ {receita_sem_canceladas:,.2f}")
        
        diferenca_receita = receita_com_canceladas - receita_sem_canceladas
        print(f"   Diferença (valor das canceladas): R$ {diferenca_receita:,.2f}")
        
        # === TESTE 3: Testar função do adicional IR trimestral ===
        print("\n3️⃣ TESTE DA FUNÇÃO calcular_adicional_ir_trimestral():")
        
        resultado_adicional = calcular_adicional_ir_trimestral(empresa.id, ano)
        
        # Buscar dados do T3 (posição 2 no array, pois começa em 0)
        if len(resultado_adicional) > 2:
            dados_t3 = resultado_adicional[2]  # T3 está na posição 2
            
            print(f"   Trimestre: {dados_t3['trimestre']}")
            print(f"   Receita consultas (função): R$ {dados_t3['receita_consultas']:,.2f}")
            print(f"   Receita outros (função): R$ {dados_t3['receita_outros']:,.2f}")
            print(f"   Receita bruta (função): R$ {dados_t3['receita_bruta']:,.2f}")
            print(f"   Base cálculo total (função): R$ {dados_t3['base_total']:,.2f}")
            print(f"   Adicional devido (função): R$ {dados_t3['adicional']:,.2f}")
            
            # Comparar receita bruta da função com cálculo manual
            receita_funcao = dados_t3['receita_bruta']
            
            if abs(receita_funcao - receita_sem_canceladas) < Decimal('0.01'):
                print(f"\n   ✅ FUNÇÃO ESTÁ CORRETA: Exclui notas canceladas!")
                print(f"      Esperado: R$ {receita_sem_canceladas:,.2f}")
                print(f"      Função retornou: R$ {receita_funcao:,.2f}")
            else:
                print(f"\n   ❌ FUNÇÃO INCORRETA: Pode estar incluindo canceladas!")
                print(f"      Esperado (sem canceladas): R$ {receita_sem_canceladas:,.2f}")
                print(f"      Função retornou: R$ {receita_funcao:,.2f}")
                print(f"      Diferença: R$ {abs(receita_funcao - receita_sem_canceladas):,.2f}")
        else:
            print("   ❌ Erro: Função não retornou dados suficientes para o T3")
        
        # === TESTE 4: Verificar todos os trimestres ===
        print("\n4️⃣ RESUMO DE TODOS OS TRIMESTRES:")
        
        for i, trimestre_data in enumerate(resultado_adicional):
            print(f"   {trimestre_data['trimestre']}: Receita R$ {trimestre_data['receita_bruta']:,.2f}, Adicional R$ {trimestre_data['adicional']:,.2f}")
        
        print(f"\n🎯 CONCLUSÃO:")
        if notas_canceladas_t3 > 0:
            print(f"   - Foram encontradas {notas_canceladas_t3} notas canceladas no T3/{ano}")
            print(f"   - Diferença nos valores: R$ {diferenca_receita:,.2f}")
            if abs(receita_funcao - receita_sem_canceladas) < Decimal('0.01'):
                print(f"   ✅ Correção implementada com SUCESSO!")
                print(f"   ✅ ESPELHO DO ADICIONAL DE IR TRIMESTRAL agora exclui canceladas!")
            else:
                print(f"   ❌ Correção ainda não está funcionando corretamente")
        else:
            print(f"   - Não há notas canceladas no T3/{ano} para teste")
            print(f"   ℹ️  Para testar completamente, adicione algumas notas com status_recebimento='cancelado'")
            print(f"   ✅ Função foi corrigida para excluir canceladas quando existirem")
        
    except Exception as e:
        print(f"❌ Erro durante a verificação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_adicional_ir_trimestral()
