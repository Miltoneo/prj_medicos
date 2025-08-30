import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import transaction
from medicos.models.despesas import DespesaSocio
from medicos.models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from django.contrib.auth import get_user_model

User = get_user_model()

def executar_migracao():
    print("Iniciando migração de despesas para movimentação financeira...")
    
    # Buscar todas as despesas de sócio
    despesas_qs = DespesaSocio.objects.all().select_related(
        'socio', 
        'item_despesa__grupo_despesa__empresa'
    )
    
    total_despesas = despesas_qs.count()
    print(f'Total de despesas encontradas: {total_despesas}')
    
    # Obter usuário admin para as criações
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print('Nenhum superuser encontrado. Criando registros sem usuário.')
    
    contador_criados = 0
    contador_existentes = 0
    contador_erros = 0
    
    for despesa in despesas_qs:
        try:
            empresa = despesa.item_despesa.grupo_despesa.empresa
            socio = despesa.socio
            
            # Verificar se já existe lançamento financeiro para esta despesa
            descricao_texto = f"Débito - {despesa.item_despesa.descricao}"
            
            # Buscar se já existe uma movimentação similar
            movimentacao_existente = Financeiro.objects.filter(
                socio=socio,
                data_movimentacao=despesa.data,
                valor=-despesa.valor,  # Valor negativo para débito
                descricao_movimentacao_financeira__descricao=descricao_texto
            ).exists()
            
            if movimentacao_existente:
                contador_existentes += 1
                print(f'JÁ EXISTE: Despesa ID {despesa.id} - {socio.pessoa.name} - {despesa.data} - R$ {despesa.valor}')
                continue
            
            # Criar ou obter descrição da movimentação financeira
            with transaction.atomic():
                descricao_movimentacao, created = DescricaoMovimentacaoFinanceira.objects.get_or_create(
                    empresa=empresa,
                    descricao=descricao_texto,
                    defaults={
                        'created_by': admin_user,
                    }
                )
                
                # Criar lançamento financeiro
                Financeiro.objects.create(
                    socio=socio,
                    descricao_movimentacao_financeira=descricao_movimentacao,
                    data_movimentacao=despesa.data,
                    valor=-despesa.valor,  # Valor negativo para débito
                    created_by=admin_user,
                )
                
                contador_criados += 1
                print(f'CRIADO: Despesa ID {despesa.id} - {socio.pessoa.name} - {despesa.data} - R$ {despesa.valor} - {descricao_texto}')
                
        except Exception as e:
            contador_erros += 1
            print(f'ERRO: Despesa ID {despesa.id} - {str(e)}')
    
    # Resumo final
    print('\n=== RESUMO DA MIGRAÇÃO ===')
    print(f'Total de despesas processadas: {total_despesas}')
    print(f'Lançamentos criados: {contador_criados}')
    print(f'Já existentes (ignorados): {contador_existentes}')
    print(f'Erros: {contador_erros}')
    print('\nMigração concluída com sucesso!')

if __name__ == '__main__':
    executar_migracao()
