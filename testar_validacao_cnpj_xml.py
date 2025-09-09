#!/usr/bin/env python
"""
Script para testar a validação de CNPJ no import de XML
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prj_medicos.settings')
django.setup()

import xml.etree.ElementTree as ET
from medicos.models import Empresa
from medicos.contexto import empresa_context

def limpar_cnpj(cnpj):
    """Remove pontuação e espaços do CNPJ"""
    if not cnpj:
        return ''
    return ''.join(filter(str.isdigit, cnpj))

def testar_validacao_cnpj():
    """Testa a lógica de validação do CNPJ"""
    
    # XML de exemplo com prestador diferente
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<CompNfse xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Nfse versao="2.02">
    <InfNfse Id="NfseId">
      <Numero>123456</Numero>
      <CodigoVerificacao>ABC123</CodigoVerificacao>
      <DataEmissao>2023-12-01</DataEmissao>
      <DeclaracaoPrestacaoServico>
        <InfDeclaracaoPrestacaoServico>
          <Prestador>
            <CpfCnpj>
              <Cnpj>12345678000191</Cnpj>
            </CpfCnpj>
          </Prestador>
          <Tomador>
            <CpfCnpj>
              <Cnpj>98765432000111</Cnpj>
            </CpfCnpj>
          </Tomador>
          <Servico>
            <Valores>
              <ValorServicos>1000.00</ValorServicos>
            </Valores>
          </Servico>
        </InfDeclaracaoPrestacaoServico>
      </DeclaracaoPrestacaoServico>
    </InfNfse>
  </Nfse>
</CompNfse>'''

    # Parse do XML
    try:
        root = ET.fromstring(xml_content)
        
        # Namespaces ABRASF
        namespaces = {'n': 'http://www.abrasf.org.br/nfse.xsd'}
        
        # Extrair CNPJ do prestador
        prestador_cnpj_element = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:Prestador/n:CpfCnpj/n:Cnpj', namespaces)
        prestador_cnpj = prestador_cnpj_element.text if prestador_cnpj_element is not None else None
        
        # Extrair CNPJ do tomador
        tomador_cnpj_element = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:Tomador/n:CpfCnpj/n:Cnpj', namespaces)
        tomador_cnpj = tomador_cnpj_element.text if tomador_cnpj_element is not None else None
        
        print(f"CNPJ Prestador encontrado: {prestador_cnpj}")
        print(f"CNPJ Tomador encontrado: {tomador_cnpj}")
        
        # Simular empresa selecionada (98765432000111)
        empresa_cnpj = "98.765.432/0001-11"
        
        # Limpar CNPJs
        prestador_cnpj_limpo = limpar_cnpj(prestador_cnpj)
        empresa_cnpj_limpo = limpar_cnpj(empresa_cnpj)
        
        print(f"CNPJ Prestador limpo: {prestador_cnpj_limpo}")
        print(f"CNPJ Empresa limpo: {empresa_cnpj_limpo}")
        
        # Testar validação
        if prestador_cnpj_limpo == empresa_cnpj_limpo:
            print("✅ VALIDAÇÃO: CNPJ válido - prestador é a própria empresa")
        else:
            print("❌ VALIDAÇÃO: CNPJ inválido - prestador não é a empresa selecionada")
            
        return prestador_cnpj_limpo != empresa_cnpj_limpo
            
    except ET.ParseError as e:
        print(f"Erro ao fazer parse do XML: {e}")
        return False

if __name__ == "__main__":
    print("=== Teste de Validação CNPJ XML ===")
    erro_detectado = testar_validacao_cnpj()
    
    if erro_detectado:
        print("\n✅ Teste bem-sucedido: Validação detectou CNPJ incorreto")
    else:
        print("\n❌ Teste falhou: Validação não detectou o problema")
