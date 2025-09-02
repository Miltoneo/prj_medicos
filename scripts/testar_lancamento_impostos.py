"""
Script de teste para o serviço de lançamento automático de impostos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('f:/Projects/Django/prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from decimal import Decimal
from medicos.models.base import Empresa, Socio
from medicos.services.lancamento_impostos import LancamentoImpostosService

def testar_servico():
    print("=== TESTE DO SERVIÇO DE LANÇAMENTO DE IMPOSTOS ===\n")
    
    try:
        # Buscar primeira empresa e sócio para teste
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ Nenhuma empresa encontrada")
            return
        
        socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
        if not socio:
            print("❌ Nenhum sócio ativo encontrado")
            return
        
        print(f"✅ Empresa: {empresa.razao_social}")
        print(f"✅ Sócio: {socio.pessoa.name}")
        print()
        
        # Valores de teste
        valores_impostos = {
            'PIS': Decimal('150.75'),
            'COFINS': Decimal('693.58'),
            'IRPJ': Decimal('1250.00'),
            'CSLL': Decimal('450.00'),
            'ISSQN': Decimal('850.25')
        }
        
        print("💰 Valores de teste:")
        for imposto, valor in valores_impostos.items():
            print(f"   {imposto}: R$ {valor}")
        print()
        
        # Testar serviço
        service = LancamentoImpostosService()
        
        print("🚀 Executando lançamento automático...")
        resultado = service.processar_impostos_automaticamente(
            empresa=empresa,
            socio=socio,
            mes=7,  # Julho
            ano=2025,
            valores_impostos=valores_impostos,
            atualizar_existentes=True
        )
        
        print("\n📊 RESULTADO:")
        print(f"✅ Sucesso: {resultado['success']}")
        
        if resultado['success']:
            print(f"📝 Lançamentos criados: {resultado['lancamentos_criados']}")
            print(f"🔄 Lançamentos atualizados: {resultado['lancamentos_atualizados']}")
            print(f"🗑️ Lançamentos removidos: {resultado['lancamentos_removidos']}")
            print(f"💵 Total lançado: R$ {resultado['total_lancado']}")
            print(f"📅 Data de lançamento: {resultado['data_lancamento']}")
            print(f"📋 Competência: {resultado['competencia']}")
            
            print("\n📋 DETALHES DOS LANÇAMENTOS:")
            for detalhe in resultado['detalhes']:
                acao_icon = {
                    'criado': '➕',
                    'atualizado': '🔄',
                    'removido': '➖',
                    'mantido': '⏸️'
                }.get(detalhe['acao'], '❓')
                
                print(f"   {acao_icon} {detalhe['imposto']}: {detalhe['acao']} - R$ {detalhe['valor']}")
        else:
            print(f"❌ Erro: {resultado['error']}")
        
        print("\n🔍 Testando listagem de lançamentos...")
        lancamentos = service.listar_lancamentos_impostos(socio, 7, 2025)
        print(f"📄 Lançamentos encontrados: {lancamentos.count()}")
        
        for lancamento in lancamentos:
            print(f"   • {lancamento.descricao_movimentacao.descricao}: R$ {abs(lancamento.valor)} em {lancamento.data_movimentacao}")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_servico()
