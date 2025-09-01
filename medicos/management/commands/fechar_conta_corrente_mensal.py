from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from medicos.relatorios.builders import processar_fechamento_mensal_conta_corrente, fechar_periodo_conta_corrente
from medicos.models.base import Empresa
from datetime import date
import calendar


class Command(BaseCommand):
    """
    Management command para processar fechamento mensal da conta corrente.
    
    Implementa padrão bancário de fechamento com persistência de saldos
    e propagação correta entre competências.
    
    Uso:
        python manage.py fechar_conta_corrente_mensal --empresa_id 5 --competencia 2025-08
        python manage.py fechar_conta_corrente_mensal --empresa_id 5 --competencia 2025-08 --fechar
    
    Fonte: Práticas bancárias e padrões do projeto
    """
    
    help = 'Processa fechamento mensal da conta corrente por empresa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa_id',
            type=int,
            required=True,
            help='ID da empresa para processamento'
        )
        
        parser.add_argument(
            '--competencia',
            type=str,
            required=True,
            help='Competência no formato YYYY-MM (ex: 2025-08)'
        )
        
        parser.add_argument(
            '--fechar',
            action='store_true',
            help='Marca o período como oficialmente fechado após processamento'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força reprocessamento mesmo se já processado'
        )

    def handle(self, *args, **options):
        empresa_id = options['empresa_id']
        competencia_str = options['competencia']
        fechar_oficial = options['fechar']
        force = options['force']
        
        # Validar formato da competência
        try:
            ano, mes = map(int, competencia_str.split('-'))
            if not (1 <= mes <= 12):
                raise ValueError("Mês deve estar entre 1 e 12")
            competencia = date(ano, mes, 1)
        except ValueError as e:
            raise CommandError(f'Formato de competência inválido: {e}')
        
        # Validar empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            raise CommandError(f'Empresa {empresa_id} não encontrada')
        
        self.stdout.write(
            self.style.HTTP_INFO(
                f'Iniciando fechamento mensal para {empresa.nome_fantasia} - {competencia_str}'
            )
        )
        
        # Verificar se já foi processado
        if not force:
            from medicos.models.conta_corrente import SaldoMensalContaCorrente
            saldos_existentes = SaldoMensalContaCorrente.objects.filter(
                empresa_id=empresa_id,
                competencia=competencia
            )
            
            if saldos_existentes.exists():
                fechados = saldos_existentes.filter(fechado=True).count()
                if fechados > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Período já possui {fechados} saldos fechados. Use --force para reprocessar.'
                        )
                    )
                    return
        
        # Processar fechamento mensal
        try:
            resultado = processar_fechamento_mensal_conta_corrente(empresa_id, competencia)
            
            if resultado['sucesso']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Processamento concluído com sucesso!'
                    )
                )
                self.stdout.write(f'   Sócios processados: {resultado["socios_processados"]}')
                
                if resultado['erros']:
                    self.stdout.write(
                        self.style.WARNING('⚠️  Avisos durante processamento:')
                    )
                    for erro in resultado['erros']:
                        self.stdout.write(f'   - {erro}')
                
                # Fechamento oficial se solicitado
                if fechar_oficial:
                    self.stdout.write('\nIniciando fechamento oficial...')
                    resultado_fechamento = fechar_periodo_conta_corrente(
                        empresa_id, 
                        competencia,
                        usuario=f'Command {self.__class__.__name__}'
                    )
                    
                    if resultado_fechamento['sucesso']:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Período oficialmente fechado!'
                            )
                        )
                        self.stdout.write(f'   Saldos fechados: {resultado_fechamento["saldos_fechados"]}')
                    else:
                        self.stdout.write(
                            self.style.ERROR('❌ Erro no fechamento oficial:')
                        )
                        for erro in resultado_fechamento['erros']:
                            self.stdout.write(f'   - {erro}')
                
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Erro no processamento:')
                )
                for erro in resultado['erros']:
                    self.stdout.write(f'   - {erro}')
                raise CommandError('Falha no processamento do fechamento mensal')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado: {str(e)}')
            )
            raise CommandError(f'Falha inesperada: {str(e)}')
        
        # Resumo final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'RESUMO DO FECHAMENTO MENSAL')
        self.stdout.write(f'Empresa: {empresa.nome_fantasia} (ID: {empresa_id})')
        self.stdout.write(f'Competência: {competencia_str}')
        self.stdout.write(f'Status: {"Fechado oficialmente" if fechar_oficial else "Processado (não fechado)"}')
        self.stdout.write('='*50)
