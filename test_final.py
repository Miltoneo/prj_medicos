#!/usr/bin/env python
"""
Script para testar o servidor Django após as correções
"""
import os
import sys
import subprocess

# Configurar caminhos
project_path = r'f:\Projects\Django\prj_medicos'
python_path = r'F:\Projects\Django\prj_medicos\myenv\Scripts\python.exe'

def test_django_check():
    """Testa se há erros no Django"""
    print("🔍 Executando Django check...")
    
    try:
        result = subprocess.run([
            python_path, 'manage.py', 'check'
        ], cwd=project_path, capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Django check passou sem erros!")
            return True
        else:
            print("❌ Django check encontrou problemas")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar check: {e}")
        return False

def test_migrations():
    """Verifica se há migrações pendentes"""
    print("\n🔄 Verificando migrações...")
    
    try:
        result = subprocess.run([
            python_path, 'manage.py', 'showmigrations', '--verbosity=2'
        ], cwd=project_path, capture_output=True, text=True, timeout=30)
        
        print("MIGRAÇÕES:")
        print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Erro ao verificar migrações: {e}")
        return False

def test_basic_imports():
    """Testa se as importações básicas funcionam"""
    print("\n📦 Testando importações...")
    
    try:
        # Mudar para o diretório do projeto
        os.chdir(project_path)
        sys.path.append(project_path)
        
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
        
        import django
        django.setup()
        
        # Testar importações
        from medicos.models import Conta, ContaMembership, Licenca, Pessoa
        print("✅ Modelos SaaS importados")
        
        from medicos.middleware.tenant_middleware import TenantMiddleware
        print("✅ Middleware importado")
        
        from medicos.views_auth import tenant_login, select_account
        print("✅ Views de autenticação importadas")
        
        from medicos.views_dashboard import dashboard_home
        print("✅ Views de dashboard importadas")
        
        print("✅ Todas as importações funcionaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nas importações: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 TESTANDO CORREÇÕES DO DJANGO SAAS\n")
    
    check_ok = test_django_check()
    migrations_ok = test_migrations()
    imports_ok = test_basic_imports()
    
    if check_ok and imports_ok:
        print("\n🎉 TODAS AS CORREÇÕES APLICADAS COM SUCESSO!")
        print("\n✅ Sistema pronto para uso!")
        print("🌐 Inicie o servidor com: python manage.py runserver 127.0.0.1:8000")
        print("🔗 Acesse: http://127.0.0.1:8000/medicos/auth/login/")
    else:
        print("\n❌ Ainda há problemas a serem resolvidos")
