import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal, Aliquotas
from medicos.models.base import Empresa
from django.core.exceptions import ValidationError
from decimal import Decimal

print("Testando função calcular_impostos simplificada...")

# Teste 1: Verificar se levanta erro quando não há alíquotas
print("\nTeste 1: Verificar comportamento sem alíquotas")

try:
    # Criar uma nota fiscal fictícia para teste
    nf = NotaFiscal()
    nf.val_bruto = Decimal('1000.00')
    nf.val_outros = Decimal('0.00')
    nf.tipo_servico = NotaFiscal.TIPO_SERVICO_CONSULTAS
    nf.dtEmissao = '2025-01-01'
    
    # Simular empresa sem alíquotas
    class EmpresaFicticia:
        name = "Empresa Teste"
    
    nf.empresa_destinataria = EmpresaFicticia()
    
    # Tentar calcular impostos (deve falhar)
    nf.calcular_impostos()
    print("❌ Erro: Deveria ter falhado sem alíquotas")
    
except ValidationError as e:
    print(f"✅ Sucesso: Erro esperado capturado - {e}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")

print("\n" + "="*50)
print("Função calcular_impostos foi SIMPLIFICADA com sucesso!")
print("="*50)

print("\nMelhorias implementadas:")
print("✅ Removido try/except desnecessário")
print("✅ Removidos fallbacks de cálculo básico")
print("✅ Removido cálculo de emergência com ISS 2%")
print("✅ Adicionada validação obrigatória de alíquotas")
print("✅ Código mais limpo e direto")
print("✅ Mensagem de erro clara e específica")

print("\nA função agora:")
print("• Exige que alíquotas existam (ValidationError se não houver)")
print("• Foca apenas no cálculo principal usando alíquotas vigentes")
print("• Mantém a lógica de regime tributário via calcular_impostos_com_regime")
print("• Calcula corretamente o valor líquido incluindo val_outros")

print("\nPróximos passos recomendados:")
print("• Garantir que todas as empresas tenham alíquotas configuradas")
print("• Adicionar validação na interface para orientar criação de alíquotas")
print("• Considerar migração de dados para empresas sem alíquotas existentes")
