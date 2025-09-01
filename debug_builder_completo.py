#!/usr/bin/env python
"""Debug específico do builder para identificar o problema."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa, Socio
from medicos.models.despesas import DespesaSocio
from datetime import datetime

def main():
    with open('debug_builder.txt', 'w', encoding='utf-8') as f:
        f.write("=== DEBUG BUILDER ===\n\n")
        
        empresa_id = 5
        mes_ano = '2025-08'
        socio_id = 10
        
        # 1. Verificar empresa
        f.write(f"1. EMPRESA {empresa_id}:\n")
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            f.write(f"  Encontrada: {empresa.name}\n")
        except Exception as e:
            f.write(f"  Erro: {e}\n")
            return
        
        # 2. Verificar competência
        f.write(f"\n2. COMPETÊNCIA {mes_ano}:\n")
        competencia = datetime.strptime(mes_ano, "%Y-%m")
        f.write(f"  Ano: {competencia.year}, Mês: {competencia.month}\n")
        
        # 3. Verificar sócios da empresa
        f.write(f"\n3. SÓCIOS DA EMPRESA:\n")
        socios = list(Socio.objects.filter(empresa=empresa, ativo=True).order_by('pessoa__name'))
        f.write(f"  Total sócios ativos: {len(socios)}\n")
        for socio in socios:
            f.write(f"    ID {socio.id}: {socio.pessoa.name} (ativo: {socio.ativo})\n")
        
        # 4. Verificar sócio específico
        f.write(f"\n4. SÓCIO ESPECÍFICO {socio_id}:\n")
        socio_selecionado = None
        if socio_id:
            socio_selecionado = next((s for s in socios if s.id == int(socio_id)), None)
        
        if socio_selecionado:
            f.write(f"  Encontrado: {socio_selecionado.pessoa.name}\n")
            f.write(f"  Empresa do sócio: {socio_selecionado.empresa_id}\n")
        else:
            f.write(f"  NÃO ENCONTRADO! Sócio {socio_id} não está na lista de sócios ativos da empresa {empresa_id}\n")
            
            # Verificar se o sócio existe em outras empresas
            socio_outras = Socio.objects.filter(id=socio_id).first()
            if socio_outras:
                f.write(f"  Sócio {socio_id} existe mas está na empresa {socio_outras.empresa_id}\n")
            else:
                f.write(f"  Sócio {socio_id} não existe no sistema\n")
            return
        
        # 5. Verificar despesas do sócio
        f.write(f"\n5. DESPESAS DO SÓCIO:\n")
        despesas_sem_rateio = DespesaSocio.objects.filter(
            socio=socio_selecionado,
            item_despesa__grupo_despesa__empresa=empresa,
            data__year=competencia.year,
            data__month=competencia.month
        ).select_related('item_despesa__grupo_despesa')
        
        f.write(f"  Filtro aplicado: socio={socio_selecionado.id}, empresa={empresa.id}, ano={competencia.year}, mês={competencia.month}\n")
        f.write(f"  Despesas encontradas: {despesas_sem_rateio.count()}\n")
        
        for despesa in despesas_sem_rateio:
            f.write(f"    ID {despesa.id}: {despesa.valor} - {despesa.item_despesa.descricao}\n")
            f.write(f"      Grupo: {despesa.item_despesa.grupo_despesa.descricao} (empresa {despesa.item_despesa.grupo_despesa.empresa_id})\n")
    
    print("Debug salvo em 'debug_builder.txt'")

if __name__ == '__main__':
    main()
