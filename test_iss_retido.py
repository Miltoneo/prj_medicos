#!/usr/bin/env python
"""
Script de teste para verificar a implementação corrigida da regra IssRetido na importação de XML
"""

import os
import sys
import django

# Configurar Django
sys.path.append('f:/Projects/Django/prj_medicos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

import xml.etree.ElementTree as ET
from decimal import Decimal

def test_xml_parsing_corrected():
    """Testa o parsing corrigido do XML fornecido"""
    
    # XML com IssRetido = 1 (retido)
    xml_content_1 = '''<EnviarLoteRpsSincronoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
<ListaNfse>
<CompNfse>
<Nfse versao='2.04'>
<InfNfse Id="202500000000042">
<DeclaracaoPrestacaoServico>
<InfDeclaracaoPrestacaoServico>
<Servico>
<Valores>
<ValorServicos>3990.00</ValorServicos>
<ValorIss>119.70</ValorIss>
</Valores>
<IssRetido>1</IssRetido>
</Servico>
</InfDeclaracaoPrestacaoServico>
</DeclaracaoPrestacaoServico>
</InfNfse>
</Nfse>
</CompNfse>
</ListaNfse>
</EnviarLoteRpsSincronoResposta>'''
    
    # XML com IssRetido = 2 (não retido)
    xml_content_2 = '''<EnviarLoteRpsSincronoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
<ListaNfse>
<CompNfse>
<Nfse versao='2.04'>
<InfNfse Id="202500000000040">
<DeclaracaoPrestacaoServico>
<InfDeclaracaoPrestacaoServico>
<Servico>
<Valores>
<ValorServicos>3018.30</ValorServicos>
<ValorIss>90.55</ValorIss>
</Valores>
<IssRetido>2</IssRetido>
</Servico>
</InfDeclaracaoPrestacaoServico>
</DeclaracaoPrestacaoServico>
</InfNfse>
</Nfse>
</CompNfse>
</ListaNfse>
</EnviarLoteRpsSincronoResposta>'''
    
    def to_decimal(val):
        try:
            return Decimal(str(val).replace(',', '.'))
        except Exception:
            return Decimal('0.00')
    
    print("📄 Testando parsing corrigido dos XMLs fornecidos\n")
    
    test_cases = [
        {
            'name': 'XML 042 - IssRetido=1 (deve importar)',
            'xml': xml_content_1,
            'expected_iss': Decimal('119.70')
        },
        {
            'name': 'XML 040 - IssRetido=2 (deve zerar)',
            'xml': xml_content_2,
            'expected_iss': Decimal('0.00')
        }
    ]
    
    for case in test_cases:
        print(f"📋 Teste: {case['name']}")
        
        try:
            root = ET.fromstring(case['xml'])
            ns = {'n': 'http://www.abrasf.org.br/nfse.xsd'}
            
            # Parsing corrigido
            valores_servico = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:Servico/n:Valores', ns)
            val_iss_el = valores_servico.find('n:ValorIss', ns) if valores_servico is not None else None
            
            # IssRetido está no nível do Servico, não dentro de Valores
            servico_el = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:Servico', ns)
            iss_retido_el = servico_el.find('n:IssRetido', ns) if servico_el is not None else None
            
            print(f"   ValorIss: {val_iss_el.text if val_iss_el is not None else 'Não encontrado'}")
            print(f"   IssRetido: {iss_retido_el.text if iss_retido_el is not None else 'Não encontrado'}")
            
            # Aplicar lógica da regra
            val_iss = Decimal('0.00')
            if val_iss_el is not None:
                iss_retido = None
                if iss_retido_el is not None:
                    try:
                        iss_retido = int(iss_retido_el.text)
                    except (ValueError, TypeError):
                        iss_retido = None
                
                # Aplicar regra do IssRetido
                if iss_retido == 1:
                    # ISS foi retido - importar o valor
                    val_iss = to_decimal(val_iss_el.text)
                elif iss_retido == 2:
                    # ISS não foi retido - não considerar (valor = 0)
                    val_iss = Decimal('0.00')
                else:
                    # Se IssRetido não está presente ou valor inválido, importar o valor normalmente
                    val_iss = to_decimal(val_iss_el.text)
            
            if val_iss == case['expected_iss']:
                print(f"   ✅ PASSOU: ISS = R$ {val_iss} (esperado R$ {case['expected_iss']})")
            else:
                print(f"   ❌ FALHOU: ISS = R$ {val_iss} (esperado R$ {case['expected_iss']})")
                
        except Exception as e:
            print(f"   ❌ Erro ao fazer parsing do XML: {e}")
        
        print()

if __name__ == '__main__':
    test_xml_parsing_corrected()
    print("🔬 Teste da correção concluído!")
