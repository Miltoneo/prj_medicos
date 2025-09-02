#!/usr/bin/env python3
"""
Script simples para verificar empresas e executar cópia direta.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models.base import Empresa

def main():
    print("🔍 VERIFICANDO EMPRESAS NO SISTEMA")
    print("="*50)
    
    # Verificar todas as empresas
    todas_empresas = Empresa.objects.all()
    print(f"📊 Total de empresas: {todas_empresas.count()}")
    
    if todas_empresas.exists():
        print("\n📋 Lista de empresas:")
        for empresa in todas_empresas:
            status = "✅ ATIVA" if empresa.ativo else "❌ INATIVA"
            print(f"   ID {empresa.id}: {empresa.name} - {status}")
    
    # Verificar empresas ativas
    empresas_ativas = Empresa.objects.filter(ativo=True)
    print(f"\n📊 Empresas ativas: {empresas_ativas.count()}")
    
    if empresas_ativas.exists():
        print("\n🎯 Executando cópia para empresas ativas:")
        for empresa in empresas_ativas:
            print(f"\n🏢 Processando Empresa ID {empresa.id}: {empresa.name}")
            
            # Importar e executar função diretamente
            try:
                from script_copiar_despesas_apropriadas import processar_despesas_apropriadas
                
                print(f"🔄 Copiando despesas apropriadas (agosto/2025)...")
                result = processar_despesas_apropriadas(
                    empresa_id=empresa.id,
                    socio_id=None,  # Todos os sócios
                    competencia="2025-08"
                )
                print(f"✅ Empresa {empresa.id} processada com sucesso!")
                
            except Exception as e:
                print(f"❌ Erro ao processar empresa {empresa.id}: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("\n⚠️ Nenhuma empresa ativa para processar")
        print("💡 Sugestão: Ativar empresas ou verificar dados do sistema")

if __name__ == "__main__":
    main()
