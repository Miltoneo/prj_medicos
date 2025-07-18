from django.views.generic import CreateView, UpdateView
from django_tables2.views import SingleTableMixin
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from .models.financeiro import AplicacaoFinanceira
from .forms_aplicacoes_financeiras import AplicacaoFinanceiraForm
from .tables_aplicacoes_financeiras import AplicacaoFinanceiraTable

class AplicacaoFinanceiraListView(LoginRequiredMixin, SingleTableMixin, ListView):
    model = AplicacaoFinanceira
    table_class = AplicacaoFinanceiraTable
    template_name = 'financeiro/aplicacoes_financeiras_list.html'
    paginate_by = 20

    def get_table_data(self):
        from medicos.models.base import Empresa
        ano = self.request.GET.get('ano')
        try:
            ano_str = str(ano).replace('.', '').replace(',', '').strip()
            ano_int = int(ano_str)
        except (TypeError, ValueError):
            ano_int = timezone.now().year
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return AplicacaoFinanceira.objects.none()
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return AplicacaoFinanceira.objects.none()
        return AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano_int
        ).order_by('-data_referencia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ano_param = self.request.GET.get('ano')
        try:
            ano_str = str(ano_param).replace('.', '').replace(',', '').strip()
            ano = int(ano_str)
        except (TypeError, ValueError):
            ano = timezone.now().year
        context['ano'] = ano
        context['anos'] = list(range(timezone.now().year - 5, timezone.now().year + 2))
        return context

class AplicacaoFinanceiraCreateView(LoginRequiredMixin, CreateView):
    model = AplicacaoFinanceira
    form_class = AplicacaoFinanceiraForm
    template_name = 'financeiro/aplicacoes_financeiras_form.html'
    success_url = reverse_lazy('medicos:aplicacoes_financeiras')

    def form_valid(self, form):
        empresa_id = self.request.session.get('empresa_id')
        from medicos.models.base import Empresa
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                form.instance.empresa = empresa
            except Empresa.DoesNotExist:
                pass
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AplicacaoFinanceiraUpdateView(LoginRequiredMixin, UpdateView):
    model = AplicacaoFinanceira
    form_class = AplicacaoFinanceiraForm
    template_name = 'financeiro/aplicacoes_financeiras_form.html'
    success_url = reverse_lazy('medicos:aplicacoes_financeiras')

    def get_queryset(self):
        from medicos.models.base import Empresa
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return AplicacaoFinanceira.objects.none()
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return AplicacaoFinanceira.objects.none()
        return AplicacaoFinanceira.objects.filter(empresa=empresa)
