#!/usr/bin/env python
"""Script final para testar e documentar o resultado da correção."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.despesas import DespesaSocio
from medicos.relatorios.builders import montar_relatorio_mensal_socio
from django.test import Client

def main():
    with open('resultado_final.txt', 'w', encoding='utf-8') as f:
        f.write("=== RESULTADO FINAL DA CORREÇÃO ===\n\n")
        
        # 1. Verificar dados no banco
        f.write("1. DADOS NO BANCO:\n")
        despesas = DespesaSocio.objects.filter(
            socio_id=10,
            data__year=2025,
            data__month=8
        ).select_related('item_despesa__grupo_despesa__empresa')
        
        f.write(f"Total despesas encontradas: {despesas.count()}\n")
        for despesa in despesas:
            empresa_id = despesa.item_despesa.grupo_despesa.empresa_id
            f.write(f"  ID {despesa.id}: valor={despesa.valor}, empresa_grupo={empresa_id}\n")
        
        # 2. Verificar builder
        f.write("\n2. BUILDER:\n")
        try:
            resultado = montar_relatorio_mensal_socio(empresa_id=5, mes_ano='2025-08', socio_id=10)
            lista_despesas = resultado.get('lista_despesas_sem_rateio', [])
            f.write(f"Builder retornou {len(lista_despesas)} despesas sem rateio\n")
            for desp in lista_despesas:
                f.write(f"  - ID {desp.get('id')}: {desp.get('descricao')} = R$ {desp.get('valor_total', 0):.2f}\n")
        except Exception as e:
            f.write(f"Erro no builder: {e}\n")
        
        # 3. Testar view via Client
        f.write("\n3. VIEW VIA CLIENT:\n")
        try:
            client = Client()
            response = client.get('/medicos/relatorio-mensal-socio/5/?mes_ano=2025-08&socio_id=10')
            f.write(f"Status: {response.status_code}\n")
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Verificar se contém os valores
                has_123 = '123.00' in content
                has_333 = '333.00' in content
                has_empty_msg = 'Nenhuma despesa sem rateio encontrada' in content
                
                f.write(f"HTML contém 123.00: {has_123}\n")
                f.write(f"HTML contém 333.00: {has_333}\n")
                f.write(f"HTML contém mensagem vazia: {has_empty_msg}\n")
                
                if has_123 and has_333 and not has_empty_msg:
                    f.write("✅ SUCESSO: As despesas aparecem corretamente no relatório!\n")
                else:
                    f.write("❌ PROBLEMA: As despesas ainda não aparecem corretamente\n")
                    
                # Salvar HTML para inspeção
                with open('debug_relatorio_final.html', 'w', encoding='utf-8') as html_file:
                    html_file.write(content)
                f.write("HTML salvo em debug_relatorio_final.html\n")
            else:
                f.write(f"Erro HTTP: {response.status_code}\n")
                
        except Exception as e:
            f.write(f"Erro na view: {e}\n")
        
        f.write("\n=== FIM ===\n")
    
    print("Resultado salvo em 'resultado_final.txt'")
    print("HTML salvo em 'debug_relatorio_final.html'")

if __name__ == '__main__':
    main()
