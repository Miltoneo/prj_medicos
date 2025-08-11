#!/usr/bin/env python
import os
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal
from medicos.models.base import Socio, Empresa

def testar_calculo_notas_emitidas():
    print("=== TESTE DO CÁLCULO DE NOTAS EMITIDAS ===")
    
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
            
            # Query atual (como está no código)
            notas_fiscais_emissao_qs = NotaFiscal.objects.filter(
                rateios_medicos__medico=socio,
                empresa_destinataria=empresa,
                dtEmissao__year=competencia.year,
                dtEmissao__month=competencia.month
            )
            
            print(f"  Notas encontradas: {notas_fiscais_emissao_qs.count()}")
            
            # Cálculo atual
            total_notas_emitidas_mes = 0
            for nf in notas_fiscais_emissao_qs:
                rateio = nf.rateios_medicos.filter(medico=socio).first()
                if rateio:
                    valor_rateio = float(rateio.valor_bruto_medico)
                    total_notas_emitidas_mes += valor_rateio
                    print(f"    - Nota {nf.id}: R$ {valor_rateio:.2f}")
                else:
                    print(f"    - Nota {nf.id}: SEM RATEIO para este sócio")
            
            print(f"  💰 Total calculado: R$ {total_notas_emitidas_mes:.2f}")
            
            # Verificação alternativa: somar direto do val_bruto das notas
            total_alternativo = sum(float(nf.val_bruto or 0) for nf in notas_fiscais_emissao_qs)
            print(f"  🔍 Total alternativo (val_bruto): R$ {total_alternativo:.2f}")
            
            if total_notas_emitidas_mes != total_alternativo:
                print(f"  ⚠️  DIVERGÊNCIA! Rateio: R$ {total_notas_emitidas_mes:.2f} vs Bruto: R$ {total_alternativo:.2f}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_calculo_notas_emitidas()
