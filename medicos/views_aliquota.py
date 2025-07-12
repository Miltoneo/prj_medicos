def main(request, empresa=None, menu_nome=None, cenario_nome=None):
    from datetime import datetime
    mes_ano = request.GET.get('mes_ano') or request.session.get('mes_ano')
    if not mes_ano:
        mes_ano = datetime.now().strftime('%Y-%m')
    request.session['mes_ano'] = mes_ano
    request.session['menu_nome'] = menu_nome or 'Aliquotas'
    request.session['cenario_nome'] = cenario_nome or 'Aliquotas'
    request.session['user_id'] = request.user.id
    context = {
        'mes_ano': mes_ano,
        'menu_nome': menu_nome or 'Aliquotas',
        'cenario_nome': cenario_nome or 'Aliquotas',
        'empresa': empresa,
        'user': request.user,
    }
    return context
from django.shortcuts import render, get_object_or_404
from medicos.models.base import Empresa
from medicos.models.fiscal import Aliquotas
from django.contrib.auth.decorators import login_required
from medicos.forms import AliquotaForm
from django.contrib import messages
from django.shortcuts import redirect
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from .tables import AliquotasTable
from .filters import AliquotasFilter

class ListaAliquotasView(SingleTableMixin, FilterView):
    table_class = AliquotasTable
    model = Aliquotas
    template_name = 'empresa/lista_aliquotas.html'
    filterset_class = AliquotasFilter  # Mantido filtro de configuração ativa
    paginate_by = 20

    def get_queryset(self):
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        # Ordena primeiro por ativos, depois por data de início de vigência mais recente
        return Aliquotas.objects.filter(conta=empresa.conta).order_by('-ativa', '-data_vigencia_inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs.get('empresa_id')
        empresa = get_object_or_404(Empresa, id=empresa_id)
        context.update(main(self.request, empresa=empresa, menu_nome='Aliquotas', cenario_nome='Aliquotas'))
        return context

@login_required
def aliquota_edit(request, empresa_id, aliquota_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if aliquota_id == 0:
        aliquota = None
        form = AliquotaForm(request.POST or None)
    else:
        aliquota = get_object_or_404(Aliquotas, id=aliquota_id, conta=empresa.conta)
        form = AliquotaForm(request.POST or None, instance=aliquota)
    if request.method == 'POST' and form.is_valid():
        aliquota = form.save(commit=False)
        aliquota.conta = empresa.conta
        aliquota.save()
        return redirect('medicos:lista_aliquotas', empresa_id=empresa.id)
    context = main(request, empresa=empresa, menu_nome='Aliquotas', cenario_nome='Aliquota')
    context['form'] = form
    context['aliquota'] = aliquota
    return render(request, 'empresa/aliquota_form.html', context)
