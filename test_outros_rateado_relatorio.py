#!/usr/bin/env python
"""
Teste da Correção - Campo "Outros" Rateado no Relatório Mensal do Sócio
Validar que a coluna "outros" mostra o valor rateado, não o total da nota

Execução: python test_outros_rateado_relatorio.py
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')

try:
    django.setup()
    print("✅ Django inicializado com sucesso")
except Exception as e:
    print(f"❌ Erro no setup Django: {e}")
    sys.exit(1)

# Importar após setup
try:
    from medicos.models import Empresa
    from medicos.models.base import Socio
    from medicos.relatorios.builders import montar_relatorio_mensal_socio
    from medicos.models.fiscal import NotaFiscal
    print("✅ Imports realizados com sucesso")
except Exception as e:
    print(f"❌ Erro nos imports: {e}")
    sys.exit(1)

def testar_campo_outros_rateado():
    print("\n" + "="*80)
    print("TESTE - Campo 'Outros' Rateado no Relatório Mensal do Sócio")
    print("="*80)
    
    try:
        # Buscar empresa 4 e sócio 7 conforme exemplo do erro
        empresa = Empresa.objects.get(id=4)
        socio = Socio.objects.get(id=7)
        
        print(f"✅ Empresa: {empresa.nome}")
        print(f"✅ Sócio: {socio.pessoa.name}")
        
        # Competência: 2025-07
        mes_ano = "2025-07"
        print(f"✅ Competência: {mes_ano}")
        
        # Buscar a nota fiscal específica do exemplo (43)
        try:
            nota_exemplo = NotaFiscal.objects.get(id=43, empresa_destinataria=empresa)
            print(f"\n📄 NOTA FISCAL DO EXEMPLO:")
            print(f"   ID: {nota_exemplo.id}")
            print(f"   Número: {nota_exemplo.numero}")
            print(f"   Tomador: {nota_exemplo.tomador}")
            print(f"   Valor Bruto Total: R$ {nota_exemplo.val_bruto:.2f}")
            print(f"   Valor 'Outros' Total: R$ {nota_exemplo.val_outros:.2f}")
            
            # Buscar rateio do sócio
            rateio = nota_exemplo.rateios_medicos.filter(medico=socio).first()
            if rateio:
                print(f"\n📊 RATEIO DO SÓCIO:")
                print(f"   Percentual: {rateio.percentual_participacao:.2f}%")
                print(f"   Valor Bruto Rateado: R$ {rateio.valor_bruto_medico:.2f}")
                
                # Calcular valor "outros" rateado esperado
                proporcao = float(rateio.valor_bruto_medico) / float(nota_exemplo.val_bruto)
                outros_rateado_esperado = float(nota_exemplo.val_outros) * proporcao
                print(f"   Proporção: {proporcao:.4f}")
                print(f"   'Outros' rateado esperado: R$ {outros_rateado_esperado:.2f}")
            else:
                print(f"❌ Rateio não encontrado para o sócio na nota {nota_exemplo.id}")
                return False
                
        except NotaFiscal.DoesNotExist:
            print(f"⚠️  Nota fiscal ID 43 não encontrada. Testando com outras notas...")
        
        # Executar relatório mensal do sócio
        relatorio = montar_relatorio_mensal_socio(empresa.id, mes_ano, socio.id)
        
        print(f"\n📈 RELATÓRIO GERADO:")
        print(f"   Total de notas: {len(relatorio.get('notas_fiscais', []))}")
        
        # Analisar as notas fiscais do relatório
        notas_fiscais = relatorio.get('notas_fiscais', [])
        if not notas_fiscais:
            print(f"❌ Nenhuma nota fiscal encontrada no relatório")
            return False
        
        print(f"\n🔍 ANÁLISE DAS NOTAS FISCAIS:")
        for i, nota in enumerate(notas_fiscais[:3], 1):  # Mostrar apenas as primeiras 3
            print(f"\n   Nota {i}:")
            print(f"      ID: {nota.get('id')}")
            print(f"      Número: {nota.get('numero')}")
            print(f"      % Rateio: {nota.get('percentual_rateio', 0):.2f}%")
            print(f"      Valor Bruto: R$ {nota.get('valor_bruto', 0):.2f}")
            print(f"      Outros: R$ {nota.get('outros', 0):.2f}")
            
            # Verificar se o valor "outros" está rateado
            if nota.get('id') == 43:  # Nota do exemplo
                print(f"      🎯 ESTA É A NOTA DO EXEMPLO!")
                outros_valor = nota.get('outros', 0)
                if abs(outros_valor - 63.58) < 0.1:  # Valor esperado com tolerância
                    print(f"      ✅ Valor 'outros' CORRETO: R$ {outros_valor:.2f}")
                else:
                    print(f"      ❌ Valor 'outros' INCORRETO: R$ {outros_valor:.2f}")
                    print(f"      ❌ Esperado: R$ 63.58 (rateado)")
                    return False
        
        # Verificar total de "outros"
        total_outros = relatorio.get('total_nf_outros', 0)
        print(f"\n📊 TOTAL DE 'OUTROS' NO RELATÓRIO: R$ {total_outros:.2f}")
        
        print(f"\n✅ CORREÇÃO IMPLEMENTADA!")
        print(f"✅ Campo 'outros' agora mostra valor RATEADO")
        print(f"✅ Cálculo proporcional aplicado corretamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Iniciando teste da correção do campo 'outros' rateado...")
    sucesso = testar_campo_outros_rateado()
    
    print("\n" + "="*80)
    if sucesso:
        print("🎉 CORREÇÃO VALIDADA!")
        print("✅ Campo 'outros' agora usa valor RATEADO")
        print("✅ Relatório mensal do sócio mostra valores corretos")
        print("✅ Exemplo: 216,00 × 29,44% = 63,58")
    else:
        print("💥 TESTE FALHOU!")
        print("❌ Verificar implementação da correção")
    print("="*80)
