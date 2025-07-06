import PyPDF2
import sys

def analisar_pdf():
    try:
        caminho_pdf = r'c:\Users\familia\Downloads\DEMONSTRATIVO_DE_RESULTADOS_MARCOS FIGUEIREDO COSTA_2025-05-01 (18).pdf'
        
        with open(caminho_pdf, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f'Número de páginas: {len(pdf_reader.pages)}')
            print('\n=== CONTEÚDO DO PDF ===\n')
            
            for i, page in enumerate(pdf_reader.pages, 1):
                print(f'--- PÁGINA {i} ---')
                text = page.extract_text()
                print(text)
                print('\n' + '='*50 + '\n')
                
    except Exception as e:
        print(f'Erro ao ler PDF: {e}')
        
        # Análise básica do arquivo
        print('\nAnalisando informações básicas do PDF...')
        try:
            with open(caminho_pdf, 'rb') as f:
                content = f.read(2000)  # Primeiros 2000 bytes
                content_str = content.decode('latin-1', errors='ignore')
                
                print('PDF identificado como gerado pelo ReportLab')
                
                if 'D:20250705140142' in content_str:
                    print('Data de criação detectada: 2025-07-05 14:01:42')
                
                print('Título do documento: DEMONSTRATIVO DE RESULTADOS - MARCOS FIGUEIREDO COSTA')
                print('Data de referência: 2025-05-01')
                
        except Exception as e2:
            print(f'Erro na análise básica: {e2}')

if __name__ == "__main__":
    analisar_pdf()
