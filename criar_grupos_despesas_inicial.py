#!/usr/bin/env python
"""
Script para criar grupos e itens de despesas iniciais
"""
import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

from medicos.models import Conta, Despesa_Grupo, Despesa_Item

def criar_grupos_despesas_inicial():
    """Cria os grupos e itens iniciais de despesas para todas as contas"""
    
    # Dados dos grupos iniciais
    grupos_dados = [
        {
            'codigo': 'FOLHA',
            'nome': 'Despesas de Folha de Pagamento',
            'descricao': 'Despesas relacionadas à folha de pagamento dos funcionários',
            'tipo_rateio': 1,  # COM_RATEIO
            'cor_grupo': '#28a745',  # Verde
            'icone': 'fas fa-users',
            'ordem_exibicao': 1,
            'itens': [
                {'codigo': 'SAL', 'nome': 'Salários', 'conta_contabil': '3.1.1.01'},
                {'codigo': 'ENC', 'nome': 'Encargos Sociais', 'conta_contabil': '3.1.1.02'},
                {'codigo': 'FER', 'nome': 'Férias', 'conta_contabil': '3.1.1.03'},
                {'codigo': '13º', 'nome': '13º Salário', 'conta_contabil': '3.1.1.04'},
                {'codigo': 'FGTS', 'nome': 'FGTS', 'conta_contabil': '3.1.1.05'},
                {'codigo': 'INSS', 'nome': 'INSS', 'conta_contabil': '3.1.1.06'},
                {'codigo': 'VT', 'nome': 'Vale Transporte', 'conta_contabil': '3.1.1.07'},
                {'codigo': 'VR', 'nome': 'Vale Refeição', 'conta_contabil': '3.1.1.08'},
                {'codigo': 'PLAN', 'nome': 'Plano de Saúde', 'conta_contabil': '3.1.1.09'},
                {'codigo': 'OUT', 'nome': 'Outros Benefícios', 'conta_contabil': '3.1.1.99'},
            ]
        },
        {
            'codigo': 'GERAL',
            'nome': 'Despesas Gerais da Associação',
            'descricao': 'Despesas operacionais gerais da associação médica',
            'tipo_rateio': 1,  # COM_RATEIO
            'cor_grupo': '#007bff',  # Azul
            'icone': 'fas fa-building',
            'ordem_exibicao': 2,
            'itens': [
                {'codigo': 'ALU', 'nome': 'Aluguel', 'conta_contabil': '3.1.2.01'},
                {'codigo': 'ENE', 'nome': 'Energia Elétrica', 'conta_contabil': '3.1.2.02'},
                {'codigo': 'TEL', 'nome': 'Telefone/Internet', 'conta_contabil': '3.1.2.03'},
                {'codigo': 'MAT', 'nome': 'Material de Escritório', 'conta_contabil': '3.1.2.04'},
                {'codigo': 'LIM', 'nome': 'Limpeza e Conservação', 'conta_contabil': '3.1.2.05'},
                {'codigo': 'SEG', 'nome': 'Segurança', 'conta_contabil': '3.1.2.06'},
                {'codigo': 'MAN', 'nome': 'Manutenção', 'conta_contabil': '3.1.2.07'},
                {'codigo': 'CON', 'nome': 'Contabilidade', 'conta_contabil': '3.1.2.08'},
                {'codigo': 'JUR', 'nome': 'Honorários Jurídicos', 'conta_contabil': '3.1.2.09'},
                {'codigo': 'TAX', 'nome': 'Taxas e Impostos', 'conta_contabil': '3.1.2.10'},
                {'codigo': 'SEG_EMP', 'nome': 'Seguros', 'conta_contabil': '3.1.2.11'},
                {'codigo': 'OUT', 'nome': 'Outras Despesas Gerais', 'conta_contabil': '3.1.2.99'},
            ]
        },
        {
            'codigo': 'SOCIO',
            'nome': 'Despesas de Sócio',
            'descricao': 'Despesas específicas de cada sócio/médico',
            'tipo_rateio': 2,  # SEM_RATEIO
            'cor_grupo': '#fd7e14',  # Laranja
            'icone': 'fas fa-user-md',
            'ordem_exibicao': 3,
            'itens': [
                {'codigo': 'PRO', 'nome': 'Pró-labore', 'conta_contabil': '3.1.3.01'},
                {'codigo': 'RET', 'nome': 'Retirada de Sócio', 'conta_contabil': '3.1.3.02'},
                {'codigo': 'REE', 'nome': 'Reembolso', 'conta_contabil': '3.1.3.03'},
                {'codigo': 'ADA', 'nome': 'Adiantamento', 'conta_contabil': '3.1.3.04'},
                {'codigo': 'EQP', 'nome': 'Equipamento Pessoal', 'conta_contabil': '3.1.3.05'},
                {'codigo': 'VIA', 'nome': 'Viagem e Hospedagem', 'conta_contabil': '3.1.3.06'},
                {'codigo': 'CUR', 'nome': 'Curso/Capacitação', 'conta_contabil': '3.1.3.07'},
                {'codigo': 'COMB', 'nome': 'Combustível', 'conta_contabil': '3.1.3.08'},
                {'codigo': 'VEST', 'nome': 'Vestuário', 'conta_contabil': '3.1.3.09'},
                {'codigo': 'OUT', 'nome': 'Outras Despesas Pessoais', 'conta_contabil': '3.1.3.99'},
            ]
        }
    ]
    
    print("=== CRIANDO GRUPOS E ITENS DE DESPESAS ===")
    
    # Buscar todas as contas ativas
    contas = Conta.objects.all()
    print(f"\nEncontradas {contas.count()} contas")
    
    for conta in contas:
        print(f"\n--- Processando conta: {conta.name} ---")
        
        for grupo_data in grupos_dados:
            # Extrair itens
            itens_data = grupo_data.pop('itens', [])
            
            # Criar ou atualizar grupo
            grupo, created = Despesa_Grupo.objects.get_or_create(
                conta=conta,
                codigo=grupo_data['codigo'],
                defaults=grupo_data
            )
            
            if created:
                print(f"  ✓ Grupo criado: {grupo.codigo} - {grupo.nome}")
            else:
                # Atualizar campos se necessário
                updated = False
                for field, value in grupo_data.items():
                    if getattr(grupo, field) != value:
                        setattr(grupo, field, value)
                        updated = True
                
                if updated:
                    grupo.save()
                    print(f"  ↻ Grupo atualizado: {grupo.codigo} - {grupo.nome}")
                else:
                    print(f"  - Grupo já existe: {grupo.codigo} - {grupo.nome}")
            
            # Criar itens do grupo
            for ordem, item_data in enumerate(itens_data, 1):
                item, item_created = Despesa_Item.objects.get_or_create(
                    conta=conta,
                    grupo=grupo,
                    codigo=item_data['codigo'],
                    defaults={
                        'nome': item_data['nome'],
                        'descricao': item_data['nome'],
                        'conta_contabil': item_data.get('conta_contabil', ''),
                        'ordem_exibicao': ordem,
                    }
                )
                
                if item_created:
                    print(f"    ✓ Item criado: {item.codigo_completo} - {item.nome}")
                else:
                    print(f"    - Item já existe: {item.codigo_completo} - {item.nome}")
            
            # Recolocar itens para próxima conta
            grupo_data['itens'] = itens_data
    
    print("\n=== GRUPOS E ITENS CRIADOS COM SUCESSO ===")
    
    # Resumo final
    print(f"\nResumo por conta:")
    for conta in contas:
        grupos_count = Despesa_Grupo.objects.filter(conta=conta).count()
        itens_count = Despesa_Item.objects.filter(conta=conta).count()
        print(f"  {conta.name}: {grupos_count} grupos, {itens_count} itens")

def main():
    try:
        criar_grupos_despesas_inicial()
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
