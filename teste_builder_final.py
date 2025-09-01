#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.relatorios.builders import montar_relatorio_mensal_socio

print('=== TESTE BUILDER ATUALIZADO ===')

# Parâmetros da tela do relatório
empresa_id = 5
mes_ano = '2025-08'
socio_id = 10

print(f'Parametros: empresa_id={empresa_id}, mes_ano={mes_ano}, socio_id={socio_id}')

try:
    # Executar o builder
    dados = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id=socio_id)
    
    print(f'\nBuilder executado com sucesso!')
    print(f'Chaves retornadas: {list(dados.keys())}')
    
    # Verificar despesas_sem_rateio via property do relatorio
    if 'relatorio' in dados and hasattr(dados['relatorio'], 'despesas_sem_rateio'):
        despesas = dados['relatorio'].despesas_sem_rateio
        print(f'\n[ENCONTRADO] relatorio.despesas_sem_rateio: {len(despesas)} registros')
        total = 0
        for despesa in despesas:
            print(f'  Data: {despesa.data} - R$ {despesa.valor} - {despesa.descricao}')
            total += float(despesa.valor)
        print(f'  Total: R$ {total}')
    else:
        print('[ERRO] relatorio.despesas_sem_rateio NAO acessivel')
    
    # Verificar lista_despesas_sem_rateio
    if 'lista_despesas_sem_rateio' in dados:
        lista = dados['lista_despesas_sem_rateio']
        print(f'\n[ENCONTRADO] lista_despesas_sem_rateio: {len(lista)} registros')
    else:
        print('[ERRO] lista_despesas_sem_rateio NAO encontrada no contexto')
        
    print(f'\n[RESULTADO] Builder retorna {len(dados.get("relatorio").despesas_sem_rateio if "relatorio" in dados else [])} despesas sem rateio via property')
    print('[CONCLUSAO] Se o property retorna as despesas, o template deve funcionar')

except Exception as e:
    print(f'[ERRO BUILDER]: {e}')
    import traceback
    traceback.print_exc()
