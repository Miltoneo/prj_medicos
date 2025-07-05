#!/usr/bin/env python
"""
Script para iniciar o servidor Django e testar a aplicação
"""
import os
import sys
import subprocess

# Configurar o ambiente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

# Caminho para o Python do ambiente virtual
python_path = r'F:\Projects\Django\prj_medicos\myenv\Scripts\python.exe'
project_path = r'f:\Projects\Django\prj_medicos'

def run_django_check():
    """Executa o check do Django"""
    print("=== EXECUTANDO DJANGO CHECK ===")
    try:
        result = subprocess.run([
            python_path, 'manage.py', 'check', '--verbosity=2'
        ], cwd=project_path, capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout - comando demorou mais de 30 segundos")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar check: {e}")
        return False

def run_migrate():
    """Executa as migrações"""
    print("\n=== EXECUTANDO MIGRAÇÕES ===")
    try:
        result = subprocess.run([
            python_path, 'manage.py', 'migrate', '--verbosity=2'
        ], cwd=project_path, capture_output=True, text=True, timeout=60)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout - comando demorou mais de 60 segundos")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar migrate: {e}")
        return False

def test_urls():
    """Testa as URLs usando o script criado"""
    print("\n=== TESTANDO URLs ===")
    try:
        result = subprocess.run([
            python_path, 'debug_urls.py'
        ], cwd=project_path, capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout - teste de URLs demorou mais de 30 segundos")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar URLs: {e}")
        return False

if __name__ == '__main__':
    print("🚀 INICIANDO TESTES DO PROJETO DJANGO SAAS\n")
    
    # Verificar se o arquivo de configuração existe
    if not os.path.exists(os.path.join(project_path, 'manage.py')):
        print("❌ manage.py não encontrado!")
        sys.exit(1)
        
    # Executar testes
    check_ok = run_django_check()
    
    if check_ok:
        print("\n✅ Django check passou!")
        
        # Executar migrações se o check passou
        migrate_ok = run_migrate()
        
        if migrate_ok:
            print("\n✅ Migrações executadas com sucesso!")
            
            # Testar URLs
            urls_ok = test_urls()
            
            if urls_ok:
                print("\n✅ Testes de URL completados!")
            else:
                print("\n❌ Problemas nos testes de URL")
        else:
            print("\n❌ Erro nas migrações")
    else:
        print("\n❌ Django check falhou!")
    
    print("\n🏁 TESTES CONCLUÍDOS")
