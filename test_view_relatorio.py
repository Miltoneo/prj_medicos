#!/usr/bin/env python
"""Testa se a view do relatório mensal do sócio exibe as despesas corretamente."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.test import RequestFactory
from medicos.views_relatorios import relatorio_mensal_socio
from django.contrib.auth import get_user_model
from medicos.models.base import Empresa, Socio

def main():
    # Configurar request simulado
    factory = RequestFactory()
    User = get_user_model()
    
    # Criar um usuário temporário para o teste
    user = User.objects.first()
    if not user:
        print("Erro: nenhum usuário encontrado")
        return
    
    # Simular request GET
    request = factory.get('/medicos/relatorio-mensal-socio/5/?mes_ano=2025-08&socio_id=10')
    request.user = user
    request.session = {'mes_ano': '2025-08'}
    
    print("=== TESTE VIEW RELATÓRIO MENSAL SÓCIO ===")
    print("URL: /medicos/relatorio-mensal-socio/5/?mes_ano=2025-08&socio_id=10")
    
    try:
        response = relatorio_mensal_socio(request, empresa_id=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar contexto
            context = response.context_data if hasattr(response, 'context_data') else {}
            relatorio = context.get('relatorio', {})
            
            despesas_sem_rateio = relatorio.get('despesas_sem_rateio', [])
            print(f"Despesas sem rateio no contexto: {len(despesas_sem_rateio)}")
            
            for desp in despesas_sem_rateio:
                print(f"  - {desp.get('data')}: {desp.get('descricao')} = R$ {desp.get('valor_total', 0):.2f}")
            
            # Verificar se o HTML contém as despesas
            content = response.content.decode('utf-8')
            if '123.00' in content and '333.00' in content:
                print("✅ HTML contém os valores esperados (123.00 e 333.00)")
            else:
                print("❌ HTML não contém os valores esperados")
                
            if 'Nenhuma despesa sem rateio encontrada' in content:
                print("❌ HTML ainda mostra mensagem de 'nenhuma despesa encontrada'")
            else:
                print("✅ HTML não mostra mensagem de 'nenhuma despesa encontrada'")
        
    except Exception as e:
        print(f"Erro na view: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
