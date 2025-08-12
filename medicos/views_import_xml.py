from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from .forms_import_xml import NotaFiscalImportXMLForm
from medicos.models.fiscal import NotaFiscal
from core.context_processors import empresa_context
import xml.etree.ElementTree as ET
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class NotaFiscalImportXMLView(View):
    template_name = 'faturamento/importar_xml_nota_fiscal.html'
    form_class = NotaFiscalImportXMLForm

    def get_success_url(self):
        # Preservar TODOS os filtros originais da busca (vindos da tela de lista)
        params = []
        
        # Preserva todos os parâmetros GET que vieram da tela de lista
        for key, value in self.request.GET.items():
            if value:
                params.append(f'{key}={value}')
        
        url = reverse('medicos:lista_notas_fiscais')
        if params:
            url += '?' + '&'.join(params)
        return url

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'titulo_pagina': 'Importar XML de Nota Fiscal'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        empresa = empresa_context(request).get('empresa')
        if not empresa:
            messages.error(request, 'Nenhuma empresa selecionada.')
            return redirect(self.get_success_url())
        if form.is_valid():
            files = request.FILES.getlist('xml_file')
            total_importadas = 0
            total_erros = 0
            for f in files:
                importado, erro = False, False
                try:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'n': 'http://www.abrasf.org.br/nfse.xsd'}
                    # Busca robusta para NFS-e ABRASF
                    numero_el = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:Numero', ns)
                    tomador_el = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:TomadorServico/n:RazaoSocial', ns)
                    data_emissao_el = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DataEmissao', ns)
                    descr_el = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:Servico/n:Discriminacao', ns)
                    valores_nfse = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:ValoresNfse', ns)
                    val_bruto_el = valores_nfse.find('n:BaseCalculo', ns) if valores_nfse is not None else None
                    val_iss_el = valores_nfse.find('n:ValorIss', ns) if valores_nfse is not None else None
                    val_liquido_el = valores_nfse.find('n:ValorLiquidoNfse', ns) if valores_nfse is not None else None
                    # Valores de impostos detalhados (PIS, COFINS, IR, CSLL) podem estar em outros pontos, buscar também em Servico/Valores
                    valores_servico = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:Servico/n:Valores', ns)
                    val_pis_el = valores_servico.find('n:ValorPis', ns) if valores_servico is not None else None
                    val_cofins_el = valores_servico.find('n:ValorCofins', ns) if valores_servico is not None else None
                    val_ir_el = valores_servico.find('n:ValorIr', ns) if valores_servico is not None else None
                    val_csll_el = valores_servico.find('n:ValorCsll', ns) if valores_servico is not None else None
                    # Campos
                    numero = numero_el.text if numero_el is not None else None
                    tomador = tomador_el.text if tomador_el is not None else None
                    # Buscar CNPJ do tomador
                    cnpj_tomador_el = root.find('.//n:CompNfse/n:Nfse/n:InfNfse/n:DeclaracaoPrestacaoServico/n:InfDeclaracaoPrestacaoServico/n:TomadorServico/n:IdentificacaoTomador/n:CpfCnpj/n:Cnpj', ns)
                    cnpj_tomador = cnpj_tomador_el.text if cnpj_tomador_el is not None else ''
                    dtEmissao = data_emissao_el.text[:10] if data_emissao_el is not None else None
                    descricao_servicos = descr_el.text if descr_el is not None else ''
                    from decimal import Decimal
                    from datetime import datetime
                    def to_decimal(val):
                        try:
                            return Decimal(str(val).replace(',', '.'))
                        except Exception:
                            return Decimal('0.00')
                    val_bruto = to_decimal(val_bruto_el.text) if val_bruto_el is not None else Decimal('0.00')
                    val_iss = to_decimal(val_iss_el.text) if val_iss_el is not None else Decimal('0.00')
                    val_liquido = to_decimal(val_liquido_el.text) if val_liquido_el is not None else Decimal('0.00')
                    val_pis = to_decimal(val_pis_el.text) if val_pis_el is not None else Decimal('0.00')
                    val_cofins = to_decimal(val_cofins_el.text) if val_cofins_el is not None else Decimal('0.00')
                    val_ir = to_decimal(val_ir_el.text) if val_ir_el is not None else Decimal('0.00')
                    val_csll = to_decimal(val_csll_el.text) if val_csll_el is not None else Decimal('0.00')
                    serie = ''
                    # Converter data para datetime.date
                    dtEmissao = None
                    if data_emissao_el is not None and data_emissao_el.text:
                        try:
                            dtEmissao = datetime.strptime(data_emissao_el.text[:10], '%Y-%m-%d').date()
                        except Exception:
                            dtEmissao = None
                    # Buscar aliquota vigente para a empresa e data
                    from medicos.models.fiscal import Aliquotas
                    aliquota = None
                    if empresa and dtEmissao:
                        aliquota = Aliquotas.obter_aliquota_vigente(empresa, dtEmissao)
                    if not aliquota:
                        aliquota = Aliquotas.obter_aliquota_vigente(empresa)
                    if not aliquota:
                        messages.error(request, 'Não foi encontrada alíquota vigente para a empresa e data informada. Cadastre uma alíquota antes de importar a nota fiscal.')
                        total_erros += 1
                        continue
                    if numero and dtEmissao:
                        if not NotaFiscal.objects.filter(numero=numero, serie=serie, empresa_destinataria=empresa).exists():
                            NotaFiscal.objects.create(
                                numero=numero,
                                serie=serie,
                                empresa_destinataria=empresa,
                                tomador=tomador or '',
                                cnpj_tomador=cnpj_tomador or '',
                                dtEmissao=dtEmissao,
                                descricao_servicos=descricao_servicos,
                                val_bruto=val_bruto,
                                val_ISS=val_iss,
                                val_liquido=val_liquido,
                                val_PIS=val_pis,
                                val_COFINS=val_cofins,
                                val_IR=val_ir,
                                val_CSLL=val_csll,
                                aliquotas=aliquota,
                            )
                            importado = True
                            total_importadas += 1
                        else:
                            erro = True
                            total_erros += 1
                    else:
                        erro = True
                        total_erros += 1
                except Exception as e:
                    import traceback
                    print('Erro ao importar nota fiscal XML:', e)
                    traceback.print_exc()
                    erro = True
                    total_erros += 1
            if total_importadas:
                messages.success(request, f'{total_importadas} nota(s) fiscal(is) importada(s) com sucesso!')
            if total_erros:
                messages.warning(request, f'{total_erros} arquivo(s) não pôde/puderam ser importado(s).')
            return redirect(self.get_success_url())
        return render(request, self.template_name, {'form': form, 'titulo_pagina': 'Importar XML de Nota Fiscal'})
