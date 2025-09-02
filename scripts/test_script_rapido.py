#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste rápido do script
"""

import os
import sys
import django

print("1. Iniciando...")

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

print("2. Configurando Django...")
django.setup()

print("3. Importando modelos...")
from medicos.models.despesas import DespesaSocio
from medicos.models.conta_corrente import MovimentacaoContaCorrente
from medicos.models.financeiro import DescricaoMovimentacaoFinanceira, MeioPagamento
from medicos.models.base import Socio, Empresa

print("4. Buscando sócio ID 5...")
try:
    socio = Socio.objects.get(id=5)
    print(f"✓ Sócio encontrado: {socio.pessoa.name}")
    
    print("5. Buscando despesas...")
    despesas = DespesaSocio.objects.filter(socio=socio)
    print(f"✓ Total de despesas encontradas: {despesas.count()}")
    
    for despesa in despesas:
        print(f"  - ID: {despesa.id}, Data: {despesa.data}, Valor: R$ {despesa.valor}")
        
        # Verificar se já existe no extrato
        existe = MovimentacaoContaCorrente.objects.filter(
            socio=despesa.socio,
            data_movimentacao=despesa.data,
            valor=-abs(despesa.valor),
            historico_complementar__icontains=f"Despesa ID: {despesa.id}"
        ).exists()
        
        print(f"    └─ Já existe no extrato: {existe}")
        
except Exception as e:
    print(f"❌ Erro: {e}")

print("6. Teste finalizado!")
