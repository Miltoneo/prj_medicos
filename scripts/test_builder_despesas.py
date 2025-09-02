#!/usr/bin/env python
"""Script simples para testar se o builder retorna despesas sem rateio após correção."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio

def main():
    # Testar builder
    print("=== TESTE BUILDER ===")
    resultado = montar_relatorio_mensal_socio(empresa_id=5, mes_ano='2025-08', socio_id=10)
    
    relatorio = resultado.get('relatorio')
    if relatorio:
        lista_despesas = resultado.get('lista_despesas_sem_rateio', [])
        print(f"Builder retornou {len(lista_despesas)} despesas sem rateio:")
        for desp in lista_despesas:
            print(f"  - ID {desp.get('id')}: {desp.get('descricao')} = R$ {desp.get('valor_total', 0):.2f}")
    else:
        print("Erro: builder não retornou relatório válido")

if __name__ == '__main__':
    main()
