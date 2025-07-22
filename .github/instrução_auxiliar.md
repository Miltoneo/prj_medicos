# instrução_auxiliar.md

## Troubleshooting e Correção de Dropdowns Multi-Tenant (`medicos/forms_despesas.py`)

### 1. Diagnóstico Assertivo de Dropdowns

- Siga o fluxo de troubleshooting conforme `.github/copilot-instructions.md`, seção "Fluxo assertivo para troubleshooting de dropdowns multi-tenant e filtrados".
- Confirme a regra de negócio do filtro consultando `.github/documentacao_especifica_instructions.md` e os modelos envolvidos.
- Valide se existem registros no banco que atendam ao filtro esperado (`ItemDespesa` vinculado a `GrupoDespesa` com `tipo_rateio` e empresa correta).
- Cheque se o parâmetro de contexto (`empresa_id`) está sendo passado corretamente da view para o form/widget.
- Revise o widget: o queryset do campo deve aplicar todos os filtros de negócio necessários, sem sobrescrever o widget após definir o queryset.
- Valide o template: confirme que os assets JS/CSS do widget estão carregados e não há erro de renderização.
- Teste o fluxo completo criando/editando um registro real e validando o comportamento na interface.
- Documente a causa e a solução, citando sempre os arquivos e linhas usados para referência.

### 2. Correção Aplicada em `medicos/forms_despesas.py`

- Problema: O dropdown de `item_despesa` estava vazio no HTML porque o widget era sobrescrito após a definição do queryset, quebrando o padrão do ModelForm.
- Solução: Remover a sobrescrita do widget após definir o queryset, mantendo o padrão do ModelForm. Isso garante que as opções do dropdown sejam renderizadas corretamente no HTML.

#### Exemplo de código corrigido:

```python
class DespesaEmpresaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)
        queryset = ItemDespesa.objects.filter(
            grupo_despesa__empresa_id=empresa_id,
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.COM_RATEIO
        )
        self.fields['item_despesa'].queryset = queryset
        # Não sobrescrever o widget após definir o queryset, mantendo o padrão do ModelForm

    class Meta:
        model = DespesaRateada
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

class DespesaSocioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item_despesa'].queryset = ItemDespesa.objects.filter(
            grupo_despesa__tipo_rateio=GrupoDespesa.Tipo_t.SEM_RATEIO
        )
        self.fields['item_despesa'].required = True
        # Não sobrescrever o widget após definir o queryset, mantendo o padrão do ModelForm

    class Meta:
        model = DespesaSocio
        fields = ['item_despesa', 'data', 'valor']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
```

- Fonte: `medicos/forms_despesas.py`, linhas 1-41 (após patch).
- Referência: `.github/copilot-instructions.md`, seção 3.

### 3. Recomendações

- Nunca sobrescrever widgets após definir o queryset em ModelForms.
- Garantir que o contexto (`empresa_id`) seja passado corretamente via context processor.
- Validar que o dropdown renderiza opções no HTML, não apenas no bloco de debug.
- Citar sempre os arquivos e linhas utilizados para referência.

---

Se precisar adaptar para outro fluxo ou arquivo, utilize este modelo como base.
