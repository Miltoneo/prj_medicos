#!/usr/bin/env python
"""
Validação das Notas de Rodapé - Adicional de IR
Verificar se as notas foram adicionadas corretamente no template

Execução: python validacao_notas_rodape.py
"""

import os
import sys

def validar_notas_rodape():
    """
    Verificar se as notas de rodapé foram adicionadas no template
    """
    print("=" * 80)
    print("VALIDAÇÃO - Notas de Rodapé do Adicional de IR")
    print("=" * 80)
    
    template_path = "medicos/templates/relatorios/apuracao_de_impostos.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print(f"✓ Template carregado: {template_path}")
        
        # Verificar presença das notas específicas
        notas_esperadas = [
            "* Adicional de IR: Considera a data de emissão da nota.",
        ]
        
        seções_verificadas = []
        
        # Verificar seção IRPJ Mensal
        if "Apuração IRPJ Mensal" in conteudo:
            print("✓ Seção 'Apuração IRPJ Mensal' encontrada")
            
            # Encontrar o trecho da seção IRPJ Mensal
            inicio_irpj_mensal = conteudo.find("Apuração IRPJ Mensal")
            fim_irpj_mensal = conteudo.find("Apuração Trimestral - IRPJ e CSLL", inicio_irpj_mensal)
            
            if fim_irpj_mensal > inicio_irpj_mensal:
                secao_irpj_mensal = conteudo[inicio_irpj_mensal:fim_irpj_mensal]
                
                if "* Adicional de IR: Considera a data de emissão da nota." in secao_irpj_mensal:
                    print("✅ Nota de rodapé encontrada na seção 'Apuração IRPJ Mensal'")
                    seções_verificadas.append("IRPJ Mensal")
                else:
                    print("❌ Nota de rodapé NÃO encontrada na seção 'Apuração IRPJ Mensal'")
        
        # Verificar seção IRPJ e CSLL Trimestral
        if "Apuração Trimestral - IRPJ e CSLL" in conteudo:
            print("✓ Seção 'Apuração Trimestral - IRPJ e CSLL' encontrada")
            
            # Encontrar o trecho da seção Trimestral
            inicio_trimestral = conteudo.find("Apuração Trimestral - IRPJ e CSLL")
            fim_trimestral = conteudo.find("ESPELHO DO ADICIONAL DE IR TRIMESTRAL", inicio_trimestral)
            
            if fim_trimestral > inicio_trimestral:
                secao_trimestral = conteudo[inicio_trimestral:fim_trimestral]
                
                if "* Adicional de IR: Considera a data de emissão da nota." in secao_trimestral:
                    print("✅ Nota de rodapé encontrada na seção 'Apuração Trimestral - IRPJ e CSLL'")
                    seções_verificadas.append("IRPJ e CSLL Trimestral")
                else:
                    print("❌ Nota de rodapé NÃO encontrada na seção 'Apuração Trimestral - IRPJ e CSLL'")
        
        # Verificar seção Espelho do Adicional
        if "ESPELHO DO ADICIONAL DE IR TRIMESTRAL" in conteudo:
            print("✓ Seção 'ESPELHO DO ADICIONAL DE IR TRIMESTRAL' encontrada")
            
            # Encontrar o trecho da seção Espelho
            inicio_espelho = conteudo.find("ESPELHO DO ADICIONAL DE IR TRIMESTRAL")
            fim_espelho = conteudo.find("</div>\n  </div>\n</div>\n{% endblock %}", inicio_espelho)
            
            if fim_espelho > inicio_espelho:
                secao_espelho = conteudo[inicio_espelho:fim_espelho]
                
                if "* Adicional de IR: Considera a data de emissão da nota." in secao_espelho:
                    print("✅ Nota de rodapé encontrada na seção 'ESPELHO DO ADICIONAL DE IR TRIMESTRAL'")
                    seções_verificadas.append("Espelho do Adicional")
                else:
                    print("❌ Nota de rodapé NÃO encontrada na seção 'ESPELHO DO ADICIONAL DE IR TRIMESTRAL'")
        
        print(f"\n📊 RESULTADO DA VALIDAÇÃO:")
        print(f"   Seções com nota de rodapé: {len(seções_verificadas)}/3")
        print(f"   Seções verificadas: {', '.join(seções_verificadas)}")
        
        if len(seções_verificadas) == 3:
            print(f"\n🎉 SUCESSO!")
            print(f"✅ Todas as notas de rodapé foram adicionadas corretamente")
            print(f"✅ Template atualizado: {template_path}")
            print(f"✅ Usuário será informado sobre a regra do adicional de IR")
            return True
        else:
            print(f"\n❌ PROBLEMA!")
            print(f"💥 Algumas notas de rodapé estão faltando")
            return False
    
    except FileNotFoundError:
        print(f"❌ ERRO: Template não encontrado: {template_path}")
        return False
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

def exibir_preview_notas():
    """
    Exibir como as notas aparecerão no template
    """
    print(f"\n" + "=" * 80)
    print("PREVIEW DAS NOTAS DE RODAPÉ")
    print("=" * 80)
    
    print(f"\n📋 SEÇÃO: Apuração IRPJ Mensal")
    print(f"   Nota existente: * IRPJ Mensal: Considera a data de emissão da nota (regime de competência) ou data de recebimento (regime de caixa)")
    print(f"   Nova nota: * Adicional de IR: Considera a data de emissão da nota.")
    
    print(f"\n📋 SEÇÃO: Apuração Trimestral - IRPJ e CSLL")
    print(f"   Nota existente: * IRPJ e CSLL: Considera a data de emissão da nota (regime de competência) ou data de recebimento (regime de caixa)")
    print(f"   Nova nota: * Adicional de IR: Considera a data de emissão da nota.")
    
    print(f"\n📋 SEÇÃO: ESPELHO DO ADICIONAL DE IR TRIMESTRAL")
    print(f"   Nova nota: * Adicional de IR: Considera a data de emissão da nota.")
    
    print(f"\n💡 EXPLICAÇÃO:")
    print(f"   As notas esclarecem que o adicional de IR tem regra específica:")
    print(f"   • IRPJ principal: Segue regime da empresa (competência ou caixa)")
    print(f"   • Adicional de IR: SEMPRE usa data de emissão (Lei 9.249/1995)")

if __name__ == '__main__':
    print("Validando notas de rodapé...")
    
    sucesso = validar_notas_rodape()
    exibir_preview_notas()
    
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 VALIDAÇÃO APROVADA!")
        print("✅ Notas de rodapé adicionadas com sucesso")
        print("✅ Template atualizado corretamente")
        print("✅ Usuários serão informados sobre a regra específica do adicional de IR")
    else:
        print("💥 VALIDAÇÃO REPROVADA!")
        print("❌ Verificar template e adicionar notas faltantes")
    print("=" * 80)
