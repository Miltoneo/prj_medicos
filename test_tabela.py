#!/usr/bin/env python
"""Script para testar se a tabela apuracao_irpj_mensal existe"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from django.db import connection

def testar_tabela():
    with connection.cursor() as cursor:
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'apuracao_irpj_mensal'
            );
        """)
        existe = cursor.fetchone()[0]
        print(f"Tabela 'apuracao_irpj_mensal' existe: {existe}")
        
        if not existe:
            print("Criando tabela manualmente...")
            cursor.execute("""
                CREATE TABLE apuracao_irpj_mensal (
                    id BIGSERIAL PRIMARY KEY,
                    empresa_id BIGINT NOT NULL REFERENCES medicos_empresa(id) ON DELETE CASCADE,
                    competencia VARCHAR(7) NOT NULL,
                    receita_consultas DECIMAL(15,2) DEFAULT 0.00,
                    receita_outros DECIMAL(15,2) DEFAULT 0.00,
                    receita_bruta DECIMAL(15,2) DEFAULT 0.00,
                    base_calculo DECIMAL(15,2) DEFAULT 0.00,
                    rendimentos_aplicacoes DECIMAL(15,2) DEFAULT 0.00,
                    base_calculo_total DECIMAL(15,2) DEFAULT 0.00,
                    imposto_devido DECIMAL(15,2) DEFAULT 0.00,
                    adicional DECIMAL(15,2) DEFAULT 0.00,
                    imposto_retido_nf DECIMAL(15,2) DEFAULT 0.00,
                    retencao_aplicacao_financeira DECIMAL(15,2) DEFAULT 0.00,
                    imposto_a_pagar DECIMAL(15,2) DEFAULT 0.00,
                    data_calculo TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    UNIQUE(empresa_id, competencia)
                );
            """)
            print("Tabela criada com sucesso!")
        else:
            print("Tabela já existe!")

if __name__ == '__main__':
    testar_tabela()
