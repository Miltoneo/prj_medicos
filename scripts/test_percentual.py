from django.core.management.base import BaseCommand
from datetime import datetime
from medicos.models import Empresa, Socio
from medicos.relatorios.builders import montar_relatorio_mensal_socio

class Command(BaseCommand):
    help = 'Testa o cálculo do percentual no relatório mensal do sócio'

    def handle(self, *args, **options):
        try:
            # Parâmetros de teste
            empresa = Empresa.objects.get(id=4)
            socio = Socio.objects.get(id=7)
            competencia = datetime(2025, 7, 1)
            
            self.stdout.write(f"Testando relatório para:")
            self.stdout.write(f"  Empresa: {empresa}")
            self.stdout.write(f"  Sócio: {socio}")
            self.stdout.write(f"  Competência: {competencia.strftime('%m/%Y')}")
            
            # Chamar o builder
            relatorio_data = montar_relatorio_mensal_socio(empresa, socio, competencia)
            
            # Extrair dados relevantes
            contexto = relatorio_data
            receita_bruta_socio = contexto.get('receita_bruta_socio')
            total_notas_bruto = contexto['relatorio'].total_notas_bruto
            participacao_socio = contexto.get('participacao_socio')
            participacao_socio_percentual = contexto.get('participacao_socio_percentual')
            
            self.stdout.write("\n=== DADOS DO CÁLCULO ===")
            self.stdout.write(f"receita_bruta_socio: {receita_bruta_socio}")
            self.stdout.write(f"total_notas_bruto: {total_notas_bruto}")
            self.stdout.write(f"participacao_socio: {participacao_socio}")
            self.stdout.write(f"participacao_socio_percentual: {participacao_socio_percentual}")
            
            if total_notas_bruto and total_notas_bruto > 0:
                calculo_manual = float(receita_bruta_socio) / float(total_notas_bruto) * 100
                self.stdout.write(f"Cálculo manual: {receita_bruta_socio} ÷ {total_notas_bruto} × 100 = {calculo_manual:.2f}%")
                
                # Teste de comparação
                if float(receita_bruta_socio) == float(total_notas_bruto):
                    self.stdout.write("✓ Os valores são IGUAIS - deveria mostrar 100,00%")
                else:
                    self.stdout.write("✗ Os valores são DIFERENTES")
            
            self.stdout.write(self.style.SUCCESS('\nTeste concluído com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante o teste: {str(e)}'))
            import traceback
            traceback.print_exc()
