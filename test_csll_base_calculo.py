#!/usr/bin/env python
"""
Teste para verificar se o cálculo da base do CSLL está funcionando corretamente
"""
import os
import sys
import django

# Adicionar o projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.apuracao_csll import calcular_csll
from medicos.models.fiscal import Empresa, Aliquotas
from decimal import Decimal

def test_base_calculo_csll():
    """Teste da função calcular_csll"""
    try:
        # Buscar uma empresa de teste
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada no banco")
            return
            
        print(f"✅ Testando com empresa: {empresa.nome}")
        
        # Buscar alíquotas
        aliquotas = Aliquotas.objects.filter(empresa=empresa).first()
        if not aliquotas:
            print("❌ Nenhuma alíquota encontrada para a empresa")
            return
            
        print(f"✅ Alíquotas encontradas:")
        print(f"   - CSLL Presunção Consulta: {aliquotas.CSLL_PRESUNCAO_CONSULTA}%")
        print(f"   - CSLL Presunção Outros: {aliquotas.CSLL_PRESUNCAO_OUTROS}%")
        
        # Testar cálculo para 2024
        ano = 2024
        resultado = calcular_csll(empresa.id, str(ano))
        
        print(f"✅ Teste concluído para ano {ano}")
        print(f"   - Linhas calculadas: {len(resultado)}")
        
        if resultado:
            primeiro_trimestre = resultado[0]
            print(f"   - Exemplo T1:")
            print(f"     * Receita consultas: {primeiro_trimestre.get('receita_consultas', 0)}")
            print(f"     * Receita outros: {primeiro_trimestre.get('receita_outros', 0)}")
            print(f"     * Base consultas: {primeiro_trimestre.get('base_calculo_consultas', 0)}")
            print(f"     * Base outros: {primeiro_trimestre.get('base_calculo_outros', 0)}")
            print(f"     * Base total: {primeiro_trimestre.get('base_calculo', 0)}")
        
        print("✅ Teste de base de cálculo CSLL concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_base_calculo_csll()
