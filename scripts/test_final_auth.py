#!/usr/bin/env python
"""Teste final com autenticação para verificar se o HTML contém as despesas."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def main():
    with open('resultado_final_auth.txt', 'w', encoding='utf-8') as f:
        f.write("=== TESTE COM AUTENTICAÇÃO ===\n\n")
        
        # Criar client e fazer login
        client = Client()
        User = get_user_model()
        
        # Buscar um usuário existente
        user = User.objects.first()
        if not user:
            f.write("Erro: nenhum usuário encontrado\n")
            return
        
        # Fazer login
        client.force_login(user)
        f.write(f"Login realizado com usuário: {user.username}\n")
        
        # Testar view
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
            with open('debug_relatorio_autenticado.html', 'w', encoding='utf-8') as html_file:
                html_file.write(content)
            f.write("HTML salvo em debug_relatorio_autenticado.html\n")
        else:
            f.write(f"Erro HTTP: {response.status_code}\n")
            
            # Se ainda houver redirecionamento, verificar o location
            if 'Location' in response:
                f.write(f"Redirecionamento para: {response['Location']}\n")
    
    print("Resultado salvo em 'resultado_final_auth.txt'")

if __name__ == '__main__':
    main()
