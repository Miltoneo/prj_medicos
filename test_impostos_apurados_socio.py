#!/usr/bin/env python
"""
Teste para verificar se o cálculo dos impostos apurados no Relatório Mensal do Sócio está funcionando
"""
import os
import sys
import django

# Adicionar o projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio
from medicos.models.base import Empresa, Socio
from decimal import Decimal

def test_impostos_apurados():
    """Teste do cálculo de impostos apurados no relatório mensal do sócio"""
    try:
        # Buscar uma empresa de teste
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada no banco")
            return
            
        print(f"✅ Testando com empresa: {empresa.nome}")
        
        # Buscar um sócio de teste
        socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
        if not socio:
            print("❌ Nenhum sócio encontrado para a empresa")
            return
            
        print(f"✅ Testando com sócio: {socio.pessoa.name}")
        
        # Testar relatório para julho/2025
        mes_ano = "2025-07"
        resultado = montar_relatorio_mensal_socio(empresa.id, mes_ano, socio.id)
        
        if 'relatorio' in resultado:
            relatorio = resultado['relatorio']
            
            print(f"✅ Relatório gerado com sucesso para {mes_ano}")
            print(f"   - PIS: R$ {relatorio.get('total_pis', 0):.2f}")
            print(f"   - COFINS: R$ {relatorio.get('total_cofins', 0):.2f}")
            print(f"   - IRPJ: R$ {relatorio.get('total_irpj', 0):.2f}")
            print(f"   - CSLL: R$ {relatorio.get('total_csll', 0):.2f}")
            print(f"   - ISSQN: R$ {relatorio.get('total_iss', 0):.2f}")
            print(f"   - Impostos Total: R$ {relatorio.get('impostos_total', 0):.2f}")
            print(f"   - Receita Bruta: R$ {relatorio.get('receita_bruta_recebida', 0):.2f}")
            print(f"   - Receita Líquida: R$ {relatorio.get('receita_liquida', 0):.2f}")
        else:
            print("❌ Estrutura de retorno inesperada")
            print(f"   - Chaves disponíveis: {list(resultado.keys())}")
        
        print("✅ Teste de impostos apurados concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_impostos_apurados()
