from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from .models.financeiro import AplicacaoFinanceira
from .forms_aplicacoes_financeiras import AplicacaoFinanceiraForm

class AplicacaoFinanceiraListView(LoginRequiredMixin, ListView):
    model = AplicacaoFinanceira
    template_name = 'financeiro/aplicacoes_financeiras_list.html'
    context_object_name = 'aplicacoes'
    paginate_by = 20


    def get_queryset(self):
        from medicos.models.base import Empresa
        ano = self.request.GET.get('ano')
        if not ano:
            ano = timezone.now().year
        empresa_id = self.request.session.get('empresa_id')
        if not empresa_id:
            return AplicacaoFinanceira.objects.none()
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return AplicacaoFinanceira.objects.none()
        return AplicacaoFinanceira.objects.filter(
            empresa=empresa,
            data_referencia__year=ano
        ).order_by('-data_referencia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ano = self.request.GET.get('ano')
        if not ano:
            ano = timezone.now().year
        context['ano'] = int(ano)
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
