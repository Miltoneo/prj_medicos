#!/usr/bin/env python3
"""
Script wrapper para copiar despesas apropriadas de TODAS as empresas.
Executa o script de cópia para cada empresa ativa automaticamente.
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa
import subprocess

def main():
    """Executa script de cópia para todas as empresas."""
    print("🏢 COPIANDO DESPESAS APROPRIADAS - TODAS AS EMPRESAS")
    print("="*60)
    print(f"📅 Data/Hora: {datetime.now()}")
    
    try:
        # Buscar todas as empresas ativas
        empresas = Empresa.objects.filter(ativo=True).order_by('id')
        
        if not empresas.exists():
            print("❌ Nenhuma empresa ativa encontrada")
            return
        
        print(f"🏢 Empresas ativas encontradas: {empresas.count()}")
        for empresa in empresas:
            print(f"   → {empresa.id}: {empresa.name}")
        
        print(f"\n🔄 Iniciando processamento...")
        
        total_empresas = empresas.count()
        sucesso = 0
        falhas = 0
        
        for i, empresa in enumerate(empresas, 1):
            print(f"\n{'='*60}")
            print(f"📊 PROCESSANDO EMPRESA {i}/{total_empresas}")
            print(f"🏢 ID: {empresa.id} | Nome: {empresa.name}")
            print(f"{'='*60}")
            
            try:
                # Executar script para esta empresa (agosto 2025)
                cmd = [
                    sys.executable, 
                    "script_copiar_despesas_apropriadas.py",
                    "--empresa_id", str(empresa.id),
                    "--competencia", "2025-08"
                ]
                
                print(f"🔧 Comando: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                if result.returncode == 0:
                    print(f"✅ SUCESSO - Empresa {empresa.id}")
                    print("📋 Saída:")
                    print(result.stdout)
                    sucesso += 1
                else:
                    print(f"❌ ERRO - Empresa {empresa.id}")
                    print("📋 Erro:")
                    print(result.stderr)
                    print("📋 Saída:")
                    print(result.stdout)
                    falhas += 1
                    
            except Exception as e:
                print(f"❌ EXCEÇÃO - Empresa {empresa.id}: {e}")
                falhas += 1
        
        # Resultado final
        print(f"\n{'='*60}")
        print("RESULTADO FINAL")
        print(f"{'='*60}")
        print(f"📊 Total de empresas: {total_empresas}")
        print(f"✅ Sucessos: {sucesso}")
        print(f"❌ Falhas: {falhas}")
        
        if falhas == 0:
            print("\n🎉 TODAS AS EMPRESAS PROCESSADAS COM SUCESSO!")
        else:
            print(f"\n⚠️ {falhas} empresas falharam - verifique os logs acima")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
