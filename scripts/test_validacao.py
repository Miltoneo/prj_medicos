import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal
from decimal import Decimal

# Teste da validação do valor líquido
print("Testando validação do valor líquido com val_outros...")

# Simular uma nota fiscal com valores
nf = NotaFiscal()
nf.val_bruto = Decimal('2000.00')
nf.val_ISS = Decimal('40.00')  # 2%
nf.val_PIS = Decimal('13.00')  # 0.65%
nf.val_COFINS = Decimal('60.00') # 3%
nf.val_IR = Decimal('30.00')   # 1.5%
nf.val_CSLL = Decimal('20.00') # 1%
nf.val_outros = Decimal('186.00') # Outros valores

total_impostos = nf.val_ISS + nf.val_PIS + nf.val_COFINS + nf.val_IR + nf.val_CSLL
print(f"Total impostos: R$ {total_impostos}")

valor_liquido_esperado = nf.val_bruto - total_impostos - nf.val_outros
print(f"Valor líquido esperado: R$ {valor_liquido_esperado}")

# Teste 1: Valor líquido correto
nf.val_liquido = valor_liquido_esperado
print(f"Teste 1 - Valor líquido correto: R$ {nf.val_liquido}")

try:
    nf.clean()
    print("✓ Validação passou - valor líquido correto")
except Exception as e:
    print(f"✗ Erro inesperado: {e}")

# Teste 2: Valor líquido incorreto
nf.val_liquido = Decimal('1651.00')  # Valor do erro relatado
print(f"Teste 2 - Valor líquido incorreto: R$ {nf.val_liquido}")

try:
    nf.clean()
    print("✗ Validação deveria ter falhado")
except Exception as e:
    print(f"✓ Erro esperado: {e}")

print("\nTeste concluído!")
