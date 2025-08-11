#!/usr/bin/env python
import os
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal
from medicos.models.base import Socio, Empresa

def testar_calculo_receita_bruta_recebida():
    print("=== TESTE DO CÁLCULO DE RECEITA BRUTA RECEBIDA (VALOR TOTAL DAS NOTAS) ===")
    
    try:
        # Pegar uma empresa e sócio para teste
        empresa = Empresa.objects.first()
        socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
        
        if not empresa or not socio:
            print("❌ Nenhuma empresa ou sócio encontrado")
            return
            
        print(f"Testando com:")
        print(f"  Empresa: {empresa.name}")
        print(f"  Sócio: {socio.pessoa.name}")
        
        # Testar para diferentes meses
        for mes_teste in [10, 11, 12]:  # Outubro, Novembro, Dezembro 2024
            competencia = datetime(2024, mes_teste, 1)
            print(f"\n📅 Competência: {competencia.strftime('%m/%Y')}")
            
            # Query para notas recebidas (data de recebimento)
            notas_fiscais_qs = NotaFiscal.objects.filter(
                rateios_medicos__medico=socio,
                empresa_destinataria=empresa,
                dtRecebimento__year=competencia.year,
                dtRecebimento__month=competencia.month,
                dtRecebimento__isnull=False  # Apenas notas que foram recebidas
            )
            
            print(f"  Notas recebidas: {notas_fiscais_qs.count()}")
            
            # Cálculo da receita bruta recebida (valor total bruto das notas)
            receita_bruta_recebida_total = sum(float(nf.val_bruto or 0) for nf in notas_fiscais_qs)
            
            # Cálculo dos faturamentos por tipo (valor total bruto das notas)
            faturamento_consultas = 0
            faturamento_plantao = 0
            faturamento_outros = 0
            
            # Para comparação: soma apenas da parte do sócio
            receita_bruta_socio_parte = 0
            
            for nf in notas_fiscais_qs:
                valor_bruto_total = float(nf.val_bruto or 0)
                
                # Classificar por tipo de serviço (valor total da nota)
                if nf.tipo_servico == NotaFiscal.TIPO_SERVICO_CONSULTAS:
                    faturamento_consultas += valor_bruto_total
                elif 'plantão' in nf.descricao_servicos.lower() or 'plantao' in nf.descricao_servicos.lower():
                    faturamento_plantao += valor_bruto_total
                else:
                    faturamento_outros += valor_bruto_total
                
                # Para comparação: parte do sócio
                rateio = nf.rateios_medicos.filter(medico=socio).first()
                if rateio:
                    receita_bruta_socio_parte += float(rateio.valor_bruto_medico)
                
                print(f"    - Nota {nf.id}: R$ {valor_bruto_total:.2f} total (Sócio: R$ {float(rateio.valor_bruto_medico):.2f if rateio else 0:.2f})")
            
            print(f"  💰 RECEITA BRUTA RECEBIDA (TOTAL): R$ {receita_bruta_recebida_total:.2f}")
            print(f"    • Faturamento consultas: R$ {faturamento_consultas:.2f}")
            print(f"    • Faturamento plantão: R$ {faturamento_plantao:.2f}")
            print(f"    • Faturamento outros: R$ {faturamento_outros:.2f}")
            print(f"  🔍 Apenas parte do sócio: R$ {receita_bruta_socio_parte:.2f}")
            
            # Verificação 1: soma dos faturamentos deve ser igual à receita bruta recebida total
            soma_faturamentos = faturamento_consultas + faturamento_plantao + faturamento_outros
            if abs(receita_bruta_recebida_total - soma_faturamentos) < 0.01:  # Margem para arredondamento
                print(f"  ✅ CONSISTÊNCIA OK: Soma dos faturamentos = Receita bruta recebida (total)")
            else:
                print(f"  ❌ INCONSISTÊNCIA: Receita bruta total R$ {receita_bruta_recebida_total:.2f} vs Soma faturamentos R$ {soma_faturamentos:.2f}")
            
            # Verificação 2: Valor total deve ser maior ou igual à parte do sócio
            if receita_bruta_recebida_total >= receita_bruta_socio_parte:
                print(f"  ✅ CORRETO: Total notas (R$ {receita_bruta_recebida_total:.2f}) ≥ Parte sócio (R$ {receita_bruta_socio_parte:.2f})")
            else:
                print(f"  ❌ ERRO: Total das notas menor que parte do sócio!")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_calculo_receita_bruta_recebida()
