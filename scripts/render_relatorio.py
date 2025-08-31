"""Renderiza a view `relatorio_mensal_socio` e salva o HTML em um arquivo.
Uso:
  python scripts\render_relatorio.py --empresa 5 --mes_ano 2025-08 --socio 10

Gera: debug_relatorio.html no diretório do projeto.
"""
import os
import sys
import argparse

# Ajuste para usar settings do projeto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
import django
from django.test import Client

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--empresa', required=True, help='empresa_id (ex: 5)')
    parser.add_argument('--mes_ano', required=True, help='competencia no formato YYYY-MM (ex: 2025-08)')
    parser.add_argument('--socio', required=True, help='socio_id (ex: 10)')
    args = parser.parse_args()

    django.setup()
    client = Client()

    url = f"/medicos/relatorio-mensal-socio/{args.empresa}/?mes_ano={args.mes_ano}&socio_id={args.socio}"
    print('Requesting:', url)
    response = client.get(url)
    print('Status code:', response.status_code)

    try:
        content = response.content.decode('utf-8')
    except Exception:
        content = response.content.decode('latin-1')

    out_path = os.path.join(os.getcwd(), 'debug_relatorio.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Wrote {out_path} ({len(content)} bytes)')

if __name__ == '__main__':
    main()
