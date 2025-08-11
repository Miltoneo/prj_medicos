"""
Teste simples para verificar o funcionamento do IRPJ Mensal
"""

from datetime import datetime
from decimal import Decimal
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas
from medicos.relatorios.apuracao_irpj_mensal import montar_relatorio_irpj_mensal_persistente

def teste_irpj_mensal():
    """Teste básico da funcionalidade IRPJ Mensal"""
    try:
        # Buscar primeira empresa
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada no banco de dados")
            return False
            
        print(f"✅ Testando IRPJ Mensal para empresa: {empresa.name}")
        
        # Verificar se existe alíquota
        aliquota = Aliquotas.objects.filter(empresa=empresa).first()
        if not aliquota:
            print("❌ Nenhuma alíquota encontrada para a empresa")
            return False
            
        print(f"✅ Alíquota encontrada. Limite adicional: R$ {aliquota.IRPJ_VALOR_BASE_INICIAR_CAL_ADICIONAL}")
        
        # Executar cálculo para 2024
        ano = 2024
        resultado = montar_relatorio_irpj_mensal_persistente(empresa.id, ano)
        
        print(f"✅ Cálculo executado com sucesso")
        print(f"   - Linhas processadas: {len(resultado['linhas'])}")
        
        # Exibir resumo dos primeiros meses
        for i, linha in enumerate(resultado['linhas'][:3]):
            print(f"   - {linha['competencia']}: Receita R$ {linha['receita_bruta']}, IRPJ R$ {linha['imposto_a_pagar']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    import django
    import os
    import sys
    
    # Configurar Django
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
    django.setup()
    
    # Executar teste
    print("🧪 Iniciando teste do IRPJ Mensal...")
    sucesso = teste_irpj_mensal()
    
    if sucesso:
        print("✅ Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou!")
