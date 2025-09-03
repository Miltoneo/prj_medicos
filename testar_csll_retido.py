#!/usr/bin/env python
import os
import sys
import django

# Adicionar o diretório do projeto ao Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from decimal import Decimal
from medicos.models.base import Empresa
from medicos.relatorios.apuracao_csll import montar_relatorio_csll_persistente
from medicos.views_relatorios import ApuracaoImpostosView
from medicos.models import NotaFiscal
from django.db.models import Sum

def verificar_csll_retido():
    """Comparar valores de CSLL retido entre as duas tabelas"""
    
    print("🔍 Verificando consistência do CSLL retido entre tabelas...")
    
    try:
        # Usar empresa padrão (ajustar conforme necessário)
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada")
            return
            
        ano = 2024  # Ajustar conforme necessário
        print(f"📊 Empresa: {empresa.nome} | Ano: {ano}")
        
        # 1. Buscar dados da tabela "CSLL - Trimestres"
        relatorio_csll = montar_relatorio_csll_persistente(empresa.id, ano)
        
        print("\n📋 Tabela 'CSLL - Trimestres' (relatorio_csll):")
        for linha in relatorio_csll['linhas']:
            competencia = linha['competencia']
            imposto_retido = linha['imposto_retido_nf']
            print(f"   {competencia}: R$ {imposto_retido}")
        
        # 2. Calcular valores mensais como na tabela "Apuração Trimestral - CSLL"
        print("\n📋 Cálculo mensal direto (como Apuração Trimestral - CSLL):")
        
        for mes in range(1, 13):
            # Buscar CSLL retido do mês por data de recebimento
            notas_recebidas_mes = NotaFiscal.objects.filter(
                empresa_destinataria=empresa,
                dtRecebimento__year=ano,
                dtRecebimento__month=mes,
                dtRecebimento__isnull=False
            )
            
            csll_retido_mes = notas_recebidas_mes.aggregate(
                total=Sum('val_CSLL')
            )['total'] or Decimal('0')
            
            print(f"   Mês {mes:02d}: R$ {csll_retido_mes}")
        
        # 3. Verificar totais trimestrais
        print("\n📋 Comparação por trimestre:")
        trimestres = [(1, [1,2,3]), (2, [4,5,6]), (3, [7,8,9]), (4, [10,11,12])]
        
        for num_tri, meses in trimestres:
            # Total do trimestre pela soma mensal
            total_trimestral_mensal = Decimal('0')
            for mes in meses:
                notas_recebidas_mes = NotaFiscal.objects.filter(
                    empresa_destinataria=empresa,
                    dtRecebimento__year=ano,
                    dtRecebimento__month=mes,
                    dtRecebimento__isnull=False
                )
                csll_retido_mes = notas_recebidas_mes.aggregate(
                    total=Sum('val_CSLL')
                )['total'] or Decimal('0')
                total_trimestral_mensal += csll_retido_mes
            
            # Total do trimestre pela tabela CSLL
            linha_trimestre = None
            for linha in relatorio_csll['linhas']:
                if linha['competencia'] == f"T{num_tri}/{ano}":
                    linha_trimestre = linha
                    break
            
            total_trimestral_csll = linha_trimestre['imposto_retido_nf'] if linha_trimestre else Decimal('0')
            
            diferenca = total_trimestral_mensal - total_trimestral_csll
            status = "✅" if diferenca == 0 else "❌"
            
            print(f"   T{num_tri}: Mensal=R${total_trimestral_mensal} | CSLL=R${total_trimestral_csll} | Diff=R${diferenca} {status}")
        
        print("\n✅ Verificação concluída!")
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_csll_retido()
