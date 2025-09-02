"""
Teste simples para verificar importações do serviço
"""
import os
import sys
import django

# Configurar Django
sys.path.append('f:/Projects/Django/prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

try:
    print("✅ Importando modelos...")
    from medicos.models.base import Empresa, Socio
    from medicos.models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento
    from medicos.models.conta_corrente import MovimentacaoContaCorrente
    print("✅ Modelos importados com sucesso!")
    
    print("✅ Importando serviço...")
    from medicos.services.lancamento_impostos import LancamentoImpostosService
    print("✅ Serviço importado com sucesso!")
    
    print("✅ Criando instância do serviço...")
    service = LancamentoImpostosService()
    print("✅ Serviço instanciado com sucesso!")
    
    print("✅ Verificando empresas disponíveis...")
    empresas = Empresa.objects.all()
    print(f"✅ {empresas.count()} empresas encontradas")
    
    if empresas.exists():
        empresa = empresas.first()
        print(f"✅ Primeira empresa: {empresa.razao_social}")
        
        print("✅ Verificando sócios...")
        socios = Socio.objects.filter(empresa=empresa, ativo=True)
        print(f"✅ {socios.count()} sócios ativos encontrados")
        
        if socios.exists():
            socio = socios.first()
            print(f"✅ Primeiro sócio: {socio.pessoa.name}")
            
            print("✅ Testando criação de instrumentos bancários...")
            instrumentos = service._obter_instrumentos_bancarios(empresa)
            print(f"✅ Instrumentos criados: {list(instrumentos.keys())}")
            
            print("✅ Testando criação de descrições...")
            descricoes = service._obter_descricoes_movimentacao(empresa)
            print(f"✅ Descrições criadas: {list(descricoes.keys())}")
            
            print("✅ Teste de cálculo de data...")
            data = service._calcular_data_lancamento(7, 2025)
            print(f"✅ Data calculada: {data}")
            
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro: {str(e)}")
    import traceback
    traceback.print_exc()
