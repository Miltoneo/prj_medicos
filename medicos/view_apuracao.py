from django.shortcuts import render, get_object_or_404
from medicos.models.base import Empresa
from medicos.models.relatorios_apuracao_issqn import ApuracaoISSQN
from medicos.relatorios.builders_apuracao_issqn import calcular_e_salvar_apuracao_issqn

def relatorio_apuracao_issqn(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    competencia = request.GET.get('competencia') or request.session.get('mes_ano')
    aliquota_iss = getattr(empresa, 'aliquota_iss', 5.0)  # ajuste conforme campo real
    calcular_e_salvar_apuracao_issqn(empresa, competencia, aliquota_iss)
    apuracoes = ApuracaoISSQN.objects.filter(empresa=empresa, competencia=competencia)
    linhas = [
        {'descricao': 'Base cálculo', 'valores': [a.base_calculo for a in apuracoes]},
        {'descricao': 'Imposto devido', 'valores': [a.imposto_devido for a in apuracoes]},
        {'descricao': 'Imposto retido NF', 'valores': [a.imposto_retido_nf for a in apuracoes]},
        {'descricao': 'Imposto a pagar', 'valores': [a.imposto_a_pagar for a in apuracoes]},
    ]
    context = {
        'empresa': empresa,
        'competencia': competencia,
        'linhas': linhas,
        'apuracoes': apuracoes,
    }
    return render(request, 'relatorios/relatorio_apuracao_issqn.html', context)
