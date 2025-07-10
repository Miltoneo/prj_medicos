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
        context['empresa'] = get_object_or_404(Empresa, id=empresa_id)
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
    context = {
        'empresa': empresa,
        'form': form,
        'aliquota': aliquota
    }
    return render(request, 'empresa/aliquota_form.html', context)
