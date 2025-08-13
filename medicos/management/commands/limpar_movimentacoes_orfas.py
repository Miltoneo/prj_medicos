from django.core.management.base import BaseCommand
from medicos.signals_financeiro import limpar_movimentacoes_orfas


class Command(BaseCommand):
    help = '''
    Remove movimentações financeiras órfãs (que perderam a referência da nota fiscal).
    
    Estas movimentações órfãs são criadas quando uma nota fiscal é excluída 
    mas o sistema anterior usava SET_NULL em vez de remover o registro completo.
    
    Uso: python manage.py limpar_movimentacoes_orfas
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas simula a operação, sem remover os registros',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('Iniciando limpeza de movimentações financeiras órfãs...')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.NOTICE('MODO SIMULAÇÃO - Nenhum registro será removido')
            )
            
            # Contar órfãs sem remover
            from medicos.models.financeiro import Financeiro
            movimentacoes_orfas = Financeiro.objects.filter(
                nota_fiscal__isnull=True,
                descricao_movimentacao_financeira__descricao='Credito de Nota Fiscal'
            )
            count_orfas = movimentacoes_orfas.count()
            
            if count_orfas > 0:
                self.stdout.write(f'Seriam removidas {count_orfas} movimentação(ões) órfã(s):')
                for mov in movimentacoes_orfas:
                    self.stdout.write(
                        f'  - ID: {mov.id}, Sócio: {mov.socio.pessoa.name}, '
                        f'Valor: R$ {mov.valor}, Data: {mov.data_movimentacao}'
                    )
            else:
                self.stdout.write('Nenhuma movimentação órfã encontrada.')
        else:
            # Executar limpeza real
            count_removidas = limpar_movimentacoes_orfas()
            
            if count_removidas > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {count_removidas} movimentação(ões) órfã(s) removida(s) com sucesso!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ Nenhuma movimentação órfã encontrada. Dados já estão limpos!')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Comando concluído.')
        )
