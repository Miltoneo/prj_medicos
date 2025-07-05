#!/usr/bin/env python
"""
Script para iniciar o servidor Django com todas as configurações corretas
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Função principal para iniciar o servidor"""
    
    # Configurar o ambiente
    project_path = r'f:\Projects\Django\prj_medicos'
    os.chdir(project_path)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
    
    print("🚀 Iniciando servidor Django SaaS Multi-Tenant...")
    print(f"📁 Diretório: {project_path}")
    print("🌐 Acesse: http://127.0.0.1:8000/medicos/auth/login/")
    print("📊 Admin: http://127.0.0.1:8000/admin/")
    print("=" * 50)
    
    try:
        # Inicializar Django
        django.setup()
        
        # Executar o servidor
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
        
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
