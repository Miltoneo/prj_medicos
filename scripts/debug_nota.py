#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal
from medicos.models.financeiro import MeioPagamento

# Verificar nota fiscal ID 24
nf = NotaFiscal.objects.get(id=24)
print(f"Nota fiscal ID: {nf.id}")
print(f"Empresa: {nf.empresa_destinataria.name}")
print(f"Empresa ID: {nf.empresa_destinataria.id}")

# Verificar meios de pagamento da empresa
meios_empresa = MeioPagamento.objects.filter(empresa_id=nf.empresa_destinataria.id, ativo=True)
print(f"\nMeios de pagamento da empresa (ID {nf.empresa_destinataria.id}): {meios_empresa.count()}")
for meio in meios_empresa:
    print(f"- ID: {meio.id}, Código: {meio.codigo}, Nome: {meio.nome}")

# Verificar todos os meios de pagamento
print(f"\nTodos os meios de pagamento:")
todos_meios = MeioPagamento.objects.all()
for meio in todos_meios:
    print(f"- ID: {meio.id}, Empresa ID: {meio.empresa_id}, Código: {meio.codigo}, Nome: {meio.nome}")

# Simular o filtro do formulário
print(f"\nSimulando filtro do formulário:")
if nf and nf.empresa_destinataria:
    queryset = MeioPagamento.objects.filter(
        empresa=nf.empresa_destinataria,
        ativo=True
    ).order_by('nome')
    print(f"Queryset filtrado: {queryset.count()} itens")
    for meio in queryset:
        print(f"- {meio.nome} ({meio.codigo})")
else:
    print("Não há empresa_destinataria")
