from django.http import JsonResponse
from django.views import View
from medicos.models.despesas import ItemDespesa, GrupoDespesa

class ItemDespesaSelect2Ajax(View):
    def get(self, request, *args, **kwargs):
        empresa_id = request.GET.get('empresa_id')
        term = request.GET.get('term', '')
        results = []
        if empresa_id:
            qs = ItemDespesa.objects.filter(
                grupo_despesa__empresa_id=empresa_id,
                grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO,
                descricao__icontains=term
            )[:20]
            for item in qs:
                results.append({
                    'id': item.pk,
                    'text': f"{item.descricao} ({item.grupo_despesa.descricao})"
                })
        return JsonResponse({'results': results})
