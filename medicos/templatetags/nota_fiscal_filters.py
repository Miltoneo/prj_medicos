from django import template
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def filter_context_only(filter_obj):
    """
    Preserva apenas os filtros de contexto relevantes (mes_ano_emissao e status_recebimento),
    excluindo dados específicos de registros (numero, tomador, cnpj_tomador).
    """
    if not filter_obj:
        return ''
    
    # Campos que devem ser preservados (apenas contexto de filtro, não dados do registro)
    context_fields = ['mes_ano_emissao', 'status_recebimento']
    
    # Cria um QueryDict apenas com os campos de contexto
    query_dict = QueryDict(mutable=True)
    for field in context_fields:
        value = filter_obj.form.data.get(field)
        if value:
            query_dict[field] = value
    
    return query_dict.urlencode()
