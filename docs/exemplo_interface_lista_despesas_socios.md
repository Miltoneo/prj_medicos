# Exemplo de Interface HTML – Lista de Despesas dos Sócios
# (Controle gerencial, não utilizado para cálculo direto de impostos)

```django-html
{% extends 'layouts/base_cenario_despesas.html' %}
{% block content %}
<div class="container-fluid px-0">
  <div class="row justify-content-center">
    <div class="col-12 col-md-11 col-lg-10 col-xl-9" style="max-width: 1200px;">
      <div class="card shadow-sm border-0 mt-4">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="fw-bold text-primary mb-0">Despesas Apropriadas dos Sócios – {{ mes_ano }}</h5>
            <a href="{% url 'medicos:copiar_despesas_socios' empresa_id=empresa_id %}" class="btn btn-outline-secondary">
              <i class="fas fa-copy me-1"></i>Copiar do mês anterior
            </a>
          </div>
          <div class="table-responsive rounded-3 border">
            <table class="table table-striped align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>Sócio</th>
                  <th>Descrição</th>
                  <th>Grupo</th>
                  <th>Valor Total (R$)</th>
                  <th>Taxa de Rateio (%)</th>
                  <th>Valor Apropriado (R$)</th>
                  <th class="text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {% for despesa in despesas_socios %}
                <tr>
                  <td>{{ despesa.socio_nome }}</td>
                  <td>{{ despesa.descricao }}</td>
                  <td>{{ despesa.grupo }}</td>
                  <td>{{ despesa.valor_total|floatformat:2 }}</td>
                  <td>
                    {% if despesa.taxa_rateio %}
                      {{ despesa.taxa_rateio|floatformat:2 }}
                    {% else %}
                      —
                    {% endif %}
                  </td>
                  <td>{{ despesa.valor_apropriado|floatformat:2 }}</td>
                  <td class="text-center">
                    <a href="{% url 'medicos:editar_despesa_socio' empresa_id=empresa_id pk=despesa.id %}" class="btn btn-sm btn-primary">
                      <i class="fas fa-edit"></i> Editar
                    </a>
                  </td>
                </tr>
                {% empty %}
                <tr>
                  <td colspan="7" class="text-center text-muted">Nenhuma despesa apropriada encontrada para o mês selecionado.</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

> Este exemplo segue o padrão visual e estrutural do projeto, incluindo responsividade, bloco content, botão de cópia do mês anterior e ações de edição.
