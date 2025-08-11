#!/usr/bin/env python
import os
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.fiscal import NotaFiscal
from medicos.models.base import Socio, Empresa

# Testar o filtro das notas fiscais
print("=== TESTE DO FILTRO DE NOTAS FISCAIS ===")

# Pegar uma empresa e sócio para teste
try:
    empresa = Empresa.objects.first()
    socio = Socio.objects.filter(empresa=empresa, ativo=True).first()
    
    if empresa and socio:
        print(f"Testando com Empresa: {empresa.name}")
        print(f"Testando com Sócio: {socio.pessoa.name}")
        
        # Testar para o mês 11/2024 (exemplo)
        competencia = datetime(2024, 11, 1)
        
        # Query por data de emissão (para adicional IR)
        notas_emissao = NotaFiscal.objects.filter(
            rateios_medicos__medico=socio,
            empresa_destinataria=empresa,
            dtEmissao__year=competencia.year,
            dtEmissao__month=competencia.month
        )
        
        # Query por data de recebimento (para tabela)
        notas_recebimento = NotaFiscal.objects.filter(
            rateios_medicos__medico=socio,
            empresa_destinataria=empresa,
            dtRecebimento__year=competencia.year,
            dtRecebimento__month=competencia.month,
            dtRecebimento__isnull=False
        )
        
        print(f"\nMês de competência: {competencia.strftime('%m/%Y')}")
        print(f"Notas por DATA DE EMISSÃO: {notas_emissao.count()}")
        for nf in notas_emissao[:3]:  # Primeiras 3
            print(f"  - ID {nf.id}: Emissão {nf.dtEmissao.strftime('%d/%m/%Y')}, Recebimento: {nf.dtRecebimento.strftime('%d/%m/%Y') if nf.dtRecebimento else 'Não recebida'}")
        
        print(f"\nNotas por DATA DE RECEBIMENTO: {notas_recebimento.count()}")
        for nf in notas_recebimento[:3]:  # Primeiras 3
            print(f"  - ID {nf.id}: Emissão {nf.dtEmissao.strftime('%d/%m/%Y')}, Recebimento: {nf.dtRecebimento.strftime('%d/%m/%Y')}")
        
        # Verificar se há diferença
        if notas_emissao.count() != notas_recebimento.count():
            print(f"\n✅ DIFERENÇA ENCONTRADA! Emissão: {notas_emissao.count()}, Recebimento: {notas_recebimento.count()}")
        else:
            print(f"\n⚠️  Mesma quantidade de notas por emissão e recebimento")
            
    else:
        print("Nenhuma empresa ou sócio encontrado para teste")
        
except Exception as e:
    print(f"Erro no teste: {e}")
    import traceback
    traceback.print_exc()
