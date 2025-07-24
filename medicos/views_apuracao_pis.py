from django.shortcuts import render, get_object_or_404
from medicos.models.base import Empresa
from medicos.models.relatorios_apuracao_pis import ApuracaoPIS
from medicos.relatorios.builders_apuracao_pis import calcular_e_salvar_apuracao_pis

def relatorio_apuracao_pis(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    ano = request.GET.get('ano') or (request.session.get('mes_ano') or '01/2025')[3:]
    competencias = [f'{mes:02d}/{ano}' for mes in range(1, 13)]
    aliquota_pis = getattr(empresa, 'aliquota_pis', None)
    if aliquota_pis is None:
        aliquota_pis = 0
    apuracoes = []
    for competencia in competencias:
        apuracao = calcular_e_salvar_apuracao_pis(empresa, competencia, aliquota_pis)
        apuracoes.append(apuracao)
    linhas = [
        {'descricao': 'Base cálculo', 'valores': [a.base_calculo for a in apuracoes]},
        {'descricao': 'Imposto devido', 'valores': [a.imposto_devido for a in apuracoes]},
        {'descricao': 'Imposto retido NF', 'valores': [a.imposto_retido_nf for a in apuracoes]},
        {'descricao': 'Imposto a pagar', 'valores': [a.imposto_a_pagar for a in apuracoes]},
        {'descricao': 'Crédito mês anterior', 'valores': [a.credito_mes_anterior for a in apuracoes]},
        {'descricao': 'Crédito mês seguinte', 'valores': [a.credito_mes_seguinte for a in apuracoes]},
    ]
    context = {
        'empresa': empresa,
        'ano': ano,
        'competencias': competencias,
        'linhas': linhas,
        'apuracoes': apuracoes,
    }
    return render(request, 'relatorios/relatorio_apuracao_pis.html', context)
