from django.core.management.base import BaseCommand
from medicos.relatorios.builders import montar_relatorio_mensal_socio
from medicos.models.base import Empresa, Socio

class Command(BaseCommand):
    help = 'Regenera relatório mensal específico'

    def add_arguments(self, parser):
        parser.add_argument('empresa_id', type=int)
        parser.add_argument('socio_id', type=int)  
        parser.add_argument('mes_ano', type=str)

    def handle(self, *args, **options):
        empresa_id = options['empresa_id']
        socio_id = options['socio_id']
        mes_ano = options['mes_ano']
        
        self.stdout.write(f"Regenerando relatório:")
        self.stdout.write(f"Empresa ID: {empresa_id}")
        self.stdout.write(f"Sócio ID: {socio_id}")
        self.stdout.write(f"Competência: {mes_ano}")
        
        try:
            resultado = montar_relatorio_mensal_socio(empresa_id, mes_ano, socio_id)
            relatorio = resultado['relatorio']
            
            self.stdout.write(f"✅ Sucesso!")
            self.stdout.write(f"Imposto provisionado mês anterior: {relatorio.imposto_provisionado_mes_anterior}")
            
        except Exception as e:
            self.stdout.write(f"❌ Erro: {e}")
