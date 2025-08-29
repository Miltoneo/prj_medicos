from django.core.management.base import BaseCommand
from django.db import transaction
from medicos.models.despesas import DespesaSocio
from medicos.models.financeiro import Financeiro, DescricaoMovimentacaoFinanceira
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Migra despesas de sócio existentes para a tabela de movimentação financeira'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa para filtrar as despesas (opcional)',
        )
        parser.add_argument(
            '--socio-id',
            type=int,
            help='ID do sócio para filtrar as despesas (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações, apenas mostra o que seria feito',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando migração de despesas para movimentação financeira...'))
        
        # Filtros opcionais
        empresa_id = options.get('empresa_id')
        socio_id = options.get('socio_id')
        dry_run = options.get('dry_run', False)
        
        # Buscar todas as despesas de sócio
        despesas_qs = DespesaSocio.objects.all().select_related(
            'socio', 
            'item_despesa__grupo_despesa__empresa'
        )
        
        if empresa_id:
            despesas_qs = despesas_qs.filter(item_despesa__grupo_despesa__empresa_id=empresa_id)
            self.stdout.write(f'Filtrando por empresa ID: {empresa_id}')
        
        if socio_id:
            despesas_qs = despesas_qs.filter(socio_id=socio_id)
            self.stdout.write(f'Filtrando por sócio ID: {socio_id}')
        
        total_despesas = despesas_qs.count()
        self.stdout.write(f'Total de despesas encontradas: {total_despesas}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita'))
        
        # Obter usuário admin para as criações (primeiro superuser encontrado)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('Nenhum superuser encontrado. Criando registros sem usuário.'))
        
        contador_criados = 0
        contador_existentes = 0
        contador_erros = 0
        
        for despesa in despesas_qs:
            try:
                empresa = despesa.item_despesa.grupo_despesa.empresa
                socio = despesa.socio
                
                # Verificar se já existe lançamento financeiro para esta despesa
                # Critério: mesmo sócio, mesma data, mesmo valor negativo e descrição similar
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
                    self.stdout.write(
                        f'JÁ EXISTE: Despesa ID {despesa.id} - {socio.pessoa.name} - '
                        f'{despesa.data} - R$ {despesa.valor}'
                    )
                    continue
                
                if dry_run:
                    contador_criados += 1
                    self.stdout.write(
                        f'SERIA CRIADO: Despesa ID {despesa.id} - {socio.pessoa.name} - '
                        f'{despesa.data} - R$ {despesa.valor} - {descricao_texto}'
                    )
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
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'CRIADO: Despesa ID {despesa.id} - {socio.pessoa.name} - '
                            f'{despesa.data} - R$ {despesa.valor} - {descricao_texto}'
                        )
                    )
                    
            except Exception as e:
                contador_erros += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'ERRO: Despesa ID {despesa.id} - {str(e)}'
                    )
                )
        
        # Resumo final
        self.stdout.write(self.style.SUCCESS('\n=== RESUMO DA MIGRAÇÃO ==='))
        self.stdout.write(f'Total de despesas processadas: {total_despesas}')
        self.stdout.write(f'Lançamentos criados: {contador_criados}')
        self.stdout.write(f'Já existentes (ignorados): {contador_existentes}')
        self.stdout.write(f'Erros: {contador_erros}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nEste foi um DRY-RUN. Para executar de fato, remova o parâmetro --dry-run'))
        else:
            self.stdout.write(self.style.SUCCESS('\nMigração concluída com sucesso!'))
