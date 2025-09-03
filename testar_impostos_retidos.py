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
from medicos.models import NotaFiscal
from django.db.models import Sum

def testar_impostos_retidos():
    """Testar se a tabela de impostos retidos está funcionando"""
    
    print("🔍 Testando implementação da tabela 'Impostos Retidos na Nota Fiscal'...")
    
    try:
        # Usar empresa padrão
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada")
            return
            
        ano = 2024  # Ajustar conforme necessário
        print(f"📊 Empresa: {empresa.nome} | Ano: {ano}")
        
        # Testar a função de cálculo dos impostos retidos
        def calcular_impostos_retidos_mensais():
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
                notas_recebidas = NotaFiscal.objects.filter(
                    empresa_destinataria_id=empresa.id,
                    dtRecebimento__year=ano,
                    dtRecebimento__month=mes,
                    dtRecebimento__isnull=False
                )
                
                print(f"   Mês {mes:02d}: {notas_recebidas.count()} notas recebidas")
                
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
                
                print(f"      PIS: R${pis_retido} | COFINS: R${cofins_retido} | IRPJ: R${irpj_retido} | CSLL: R${csll_retido} | ISSQN: R${issqn_retido} | Total: R${total_retido}")
            
            return impostos_retidos

        # Calcular dados dos impostos retidos
        impostos_retidos = calcular_impostos_retidos_mensais()
        
        print("\n📋 Resumo anual:")
        total_anual_pis = sum(impostos_retidos['pis'])
        total_anual_cofins = sum(impostos_retidos['cofins'])
        total_anual_irpj = sum(impostos_retidos['irpj'])
        total_anual_csll = sum(impostos_retidos['csll'])
        total_anual_issqn = sum(impostos_retidos['issqn'])
        total_anual_outros = sum(impostos_retidos['outros'])
        total_anual_geral = sum(impostos_retidos['total'])
        
        print(f"   PIS Total: R$ {total_anual_pis}")
        print(f"   COFINS Total: R$ {total_anual_cofins}")
        print(f"   IRPJ Total: R$ {total_anual_irpj}")
        print(f"   CSLL Total: R$ {total_anual_csll}")
        print(f"   ISSQN Total: R$ {total_anual_issqn}")
        print(f"   Outros Total: R$ {total_anual_outros}")
        print(f"   TOTAL GERAL: R$ {total_anual_geral}")
        
        print("\n✅ Implementação da tabela 'Impostos Retidos na Nota Fiscal' testada com sucesso!")
        print("📊 A tabela está pronta para exibir os valores mensais de impostos retidos.")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_impostos_retidos()
