#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal
from medicos.forms_recebimento_notafiscal import NotaFiscalRecebimentoForm

# Testar o formulário com a nota fiscal ID 24
print("=== TESTE DO FORMULÁRIO ===")
nf = NotaFiscal.objects.get(id=24)
print(f"Nota fiscal: {nf.id} - Empresa: {nf.empresa_destinataria.name}")

# Criar uma instância do formulário
form = NotaFiscalRecebimentoForm(instance=nf)

# Verificar o queryset do campo meio_pagamento
queryset = form.fields['meio_pagamento'].queryset
print(f"\nQueryset do meio_pagamento: {queryset.count()} itens")
for meio in queryset:
    print(f"- ID: {meio.id}, Nome: {meio.nome}, Código: {meio.codigo}")

# Verificar se há outros meios de pagamento no sistema
from medicos.models.financeiro import MeioPagamento
todos_meios = MeioPagamento.objects.all()
print(f"\nTodos os meios de pagamento no sistema: {todos_meios.count()}")
for meio in todos_meios:
    print(f"- ID: {meio.id}, Empresa: {meio.empresa_id}, Nome: {meio.nome}, Código: {meio.codigo}")

# Verificar as escolhas do campo
print(f"\nEscolhas do campo meio_pagamento:")
choices = list(form.fields['meio_pagamento'].widget.choices)
print(f"Total de escolhas: {len(choices)}")
for choice in choices:
    print(f"- {choice}")
