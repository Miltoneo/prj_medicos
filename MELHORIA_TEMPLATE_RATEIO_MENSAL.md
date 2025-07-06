# Melhoria de Nomenclatura: ConfiguracaoRateioMensal → TemplateRateioMensalDespesas

## Análise do Modelo Atual

### 📋 Problema Identificado

O nome atual `ConfiguracaoRateioMensal` é **genérico e ambíguo**, não transmitindo claramente a função específica do modelo no sistema de gestão de despesas.

### 🎯 Função Real do Modelo

Após análise do código, o modelo `ConfiguracaoRateioMensal` funciona como:

1. **Template/Gabarito** para configurar rateios de um mês específico
2. **Controlador de estado** do processo de configuração de rateios  
3. **Versionamento mensal** das configurações de rateio
4. **Auditoria** de quem e quando configurou os rateios

## 🚀 Proposta de Melhoria

### 1. **Renomeação Principal**

```python
# ANTES
ConfiguracaoRateioMensal

# DEPOIS (Decisão Final)
TemplateRateioMensalDespesas  # ⭐ IMPLEMENTADO - Mais específico e claro

# OUTRAS OPÇÕES CONSIDERADAS:
TemplateRateioMensal          # Genérico demais
ControleRateioMensal         # Não indica claramente a função
ConfiguradorRateioMensal     # Ambíguo
```

**Justificativa para `TemplateRateioMensalDespesas`:**
- ✅ **Clareza**: Indica que é um template/gabarito para o mês específico de despesas
- ✅ **Intuitividade**: Qualquer desenvolvedor entende que é um modelo de configuração de despesas
- ✅ **Precisão**: Reflete exatamente o que o modelo faz - ser um template reutilizável para despesas
- ✅ **Diferenciação**: Distingue claramente de outros possíveis templates (receitas, etc.)
- ✅ **Especificidade**: Deixa explícito que se trata de rateio de despesas, não de outros itens
- ✅ **Escalabilidade**: Permite futura criação de `TemplateRateioMensalReceitas` ou similares

### 2. **Melhoria dos Campos**

```python
class TemplateRateioMensalDespesas(models.Model):
    """
    Template de configuração de rateio de despesas para um mês específico
    
    Funciona como um controlador/gabarito que define o estado
    de configuração dos rateios mensais de despesas, permitindo versionamento
    e controle de aplicação das configurações de rateio.
    """
    
    class Meta:
        db_table = 'template_rateio_mensal'
        unique_together = ('conta', 'mes_referencia')
        verbose_name = "Template de Rateio Mensal"
        verbose_name_plural = "Templates de Rateio Mensais"
        indexes = [
            models.Index(fields=['conta', 'mes_referencia']),
            models.Index(fields=['status']),
        ]

    # === IDENTIFICAÇÃO ===
    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='templates_rateio_mensal'
    )
    
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Primeiro dia do mês (YYYY-MM-01)"
    )
    
    # === CONTROLE DE ESTADO MELHORADO ===
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('em_edicao', 'Em Edição'),            # Mais claro que "em_configuracao"
        ('validado', 'Validado'),               # Estado intermediário
        ('ativo', 'Ativo e Aplicável'),        # Mais claro que "finalizada"
        ('aplicado', 'Aplicado às Despesas'),   # Mantido igual
        ('arquivado', 'Arquivado'),             # Para templates antigos
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho',
        verbose_name="Status do Template"
    )
    
    # === NOVOS CAMPOS ESSENCIAIS ===
    nome_template = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nome do Template",
        help_text="Nome descritivo opcional (ex: 'Rateio Padrão 2025')"
    )
    
    total_itens_configurados = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Itens Configurados",
        help_text="Contador automático de itens com rateio definido"
    )
    
    total_medicos_participantes = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Médicos Participantes", 
        help_text="Contador automático de médicos com percentuais"
    )
    
    # === RELACIONAMENTO COM DESPESAS (NOVO) ===
    despesas_aplicadas = models.ManyToManyField(
        'Despesa',
        blank=True,
        related_name='templates_rateio_utilizados',
        verbose_name="Despesas que Utilizaram este Template",
        help_text="Controle de quais despesas foram rateadas usando este template"
    )
    
    # === CONTROLE DE AUDITORIA MELHORADO ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    data_validacao = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Data de Validação"
    )
    data_ativacao = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Data de Ativação"
    )
    data_primeira_aplicacao = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Data da Primeira Aplicação"
    )
    
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='templates_rateio_criados'
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='templates_rateio_validados'
    )
    ativado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='templates_rateio_ativados'
    )
    
    # === CAMPOS OPCIONAIS ÚTEIS ===
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações do Template"
    )
    
    template_origem = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='templates_derivados',
        verbose_name="Template Origem",
        help_text="Se foi copiado de outro template"
    )
    
    eh_template_padrao = models.BooleanField(
        default=False,
        verbose_name="É Template Padrão",
        help_text="Se deve ser usado como base para novos meses"
    )
```

### 3. **Melhorias nos Métodos**

```python
    # === MÉTODOS MELHORADOS ===
    
    def save(self, *args, **kwargs):
        # Normalizar data para primeiro dia do mês
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        
        # Auto-gerar nome se não fornecido
        if not self.nome_template:
            self.nome_template = f"Template {self.mes_referencia.strftime('%m/%Y')}"
        
        super().save(*args, **kwargs)
        
        # Atualizar contadores após save
        self.atualizar_contadores()
    
    def atualizar_contadores(self):
        """Atualiza os contadores automáticos"""
        # Contar itens configurados
        itens_count = ItemDespesaRateioMensal.objects.filter(
            conta=self.conta,
            mes_referencia=self.mes_referencia,
            ativo=True
        ).values('item_despesa').distinct().count()
        
        # Contar médicos participantes
        medicos_count = ItemDespesaRateioMensal.objects.filter(
            conta=self.conta,
            mes_referencia=self.mes_referencia,
            ativo=True
        ).values('socio').distinct().count()
        
        # Atualizar sem trigger de save recursivo
        TemplateRateioMensalDespesas.objects.filter(pk=self.pk).update(
            total_itens_configurados=itens_count,
            total_medicos_participantes=medicos_count
        )
    
    def validar_template(self):
        """Valida se o template está consistente"""
        erros = []
        
        # Verificar se há itens configurados
        if self.total_itens_configurados == 0:
            erros.append("Template não possui itens configurados")
        
        # Verificar se há médicos participantes  
        if self.total_medicos_participantes == 0:
            erros.append("Template não possui médicos participantes")
        
        # Verificar percentuais por item
        from django.db.models import Sum
        
        itens_problematicos = []
        for item in ItemDespesaRateioMensal.objects.filter(
            conta=self.conta,
            mes_referencia=self.mes_referencia,
            ativo=True
        ).values('item_despesa').distinct():
            
            total_percentual = ItemDespesaRateioMensal.objects.filter(
                conta=self.conta,
                mes_referencia=self.mes_referencia,
                item_despesa=item['item_despesa'],
                tipo_rateio='percentual',
                ativo=True
            ).aggregate(total=Sum('percentual_rateio'))['total'] or 0
            
            if abs(total_percentual - 100) > 0.01:
                item_obj = ItemDespesa.objects.get(pk=item['item_despesa'])
                itens_problematicos.append(
                    f"{item_obj.descricao}: {total_percentual:.2f}%"
                )
        
        if itens_problematicos:
            erros.append(f"Itens com percentuais incorretos: {', '.join(itens_problematicos)}")
        
        return erros
    
    def ativar_template(self, usuario=None):
        """Ativa o template após validação"""
        erros = self.validar_template()
        if erros:
            raise ValidationError(f"Não é possível ativar o template: {'; '.join(erros)}")
        
        self.status = 'ativo'
        self.data_ativacao = timezone.now()
        self.ativado_por = usuario
        self.save()
    
    def aplicar_a_despesa(self, despesa, usuario=None):
        """Aplica este template para ratear uma despesa específica"""
        if self.status != 'ativo':
            raise ValidationError("Apenas templates ativos podem ser aplicados")
        
        # Verificar se a despesa é do mesmo mês
        if despesa.data.replace(day=1) != self.mes_referencia:
            raise ValidationError("Despesa e template devem ser do mesmo mês")
        
        # Aplicar o rateio usando o método existente da despesa
        rateios = despesa.criar_rateio_automatico(usuario)
        
        # Registrar que este template foi usado nesta despesa
        self.despesas_aplicadas.add(despesa)
        
        # Atualizar data primeira aplicação se necessário
        if not self.data_primeira_aplicacao:
            self.data_primeira_aplicacao = timezone.now()
            self.save()
        
        return rateios
    
    def copiar_de_template(self, template_origem, usuario=None):
        """Copia configurações de outro template"""
        if template_origem.conta != self.conta:
            raise ValidationError("Templates devem ser da mesma conta")
        
        # Copiar rateios do template origem
        rateios_origem = ItemDespesaRateioMensal.objects.filter(
            conta=template_origem.conta,
            mes_referencia=template_origem.mes_referencia,
            ativo=True
        )
        
        rateios_criados = []
        for rateio_origem in rateios_origem:
            rateio_novo = ItemDespesaRateioMensal(
                conta=self.conta,
                item_despesa=rateio_origem.item_despesa,
                socio=rateio_origem.socio,
                mes_referencia=self.mes_referencia,
                percentual_rateio=rateio_origem.percentual_rateio,
                valor_fixo_rateio=rateio_origem.valor_fixo_rateio,
                tipo_rateio=rateio_origem.tipo_rateio,
                created_by=usuario,
                observacoes=f"Copiado do template {template_origem.nome_template}"
            )
            rateio_novo.save()
            rateios_criados.append(rateio_novo)
        
        # Registrar origem
        self.template_origem = template_origem
        self.save()
        
        return rateios_criados
    
    @property
    def percentual_completude(self):
        """Retorna percentual de completude do template"""
        total_itens_sistema = ItemDespesa.objects.filter(
            conta=self.conta,
            grupo__tipo_rateio=GRUPO_ITEM_COM_RATEIO
        ).count()
        
        if total_itens_sistema == 0:
            return 100
        
        return (self.total_itens_configurados / total_itens_sistema) * 100
    
    @property
    def status_validacao(self):
        """Status de validação simplificado"""
        erros = self.validar_template()
        return "✅ Válido" if not erros else f"❌ {len(erros)} erro(s)"
    
    def __str__(self):
        return f"{self.nome_template} ({self.mes_referencia.strftime('%m/%Y')}) - {self.get_status_display()}"
```

## 🔄 Relacionamento com Despesa

### **Novo Campo ManyToMany**

```python
# No modelo TemplateRateioMensalDespesas
despesas_aplicadas = models.ManyToManyField(
    'Despesa',
    blank=True,
    related_name='templates_rateio_utilizados',
    verbose_name="Despesas que Utilizaram este Template"
)

# No modelo Despesa (adicionar campos opcionais)
template_rateio_utilizado = models.ForeignKey(
    'TemplateRateioMensalDespesas',
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name='despesas_rateadas_por_template',
    verbose_name="Template de Rateio Utilizado"
)
```

### **Benefícios do Relacionamento**

1. **Rastreabilidade**: Saber qual template foi usado para ratear cada despesa
2. **Auditoria**: Histórico completo de aplicação dos templates
3. **Relatórios**: Análise de uso e eficácia dos templates
4. **Reversão**: Possibilidade de reverter rateios baseados em templates específicos

## 📊 Comparação de Melhorias

| Aspecto | Antes (ConfiguracaoRateioMensal) | Depois (TemplateRateioMensalDespesas) |
|---------|--------------------------------|-------------------------------|
| **Nome** | Genérico e ambíguo | Específico e claro |
| **Campos** | 9 campos básicos | 16 campos informativos |
| **Controle** | Status simples | Estados de workflow completo |
| **Auditoria** | Básica (criação/finalização) | Completa (criação/validação/ativação) |
| **Relacionamentos** | Apenas saída para rateios | Bidirecional com despesas |
| **Métodos** | 2 métodos simples | 8 métodos funcionais |
| **Validação** | Manual/externa | Automática integrada |
| **Usabilidade** | Baixa | Alta |

## 🛠️ Migração Proposta

### **Fase 1: Renomeação do Modelo**

```python
# Migration 001: Renomear tabela
class Migration(migrations.Migration):
    operations = [
        migrations.RenameModel(
            old_name='ConfiguracaoRateioMensal',
            new_name='TemplateRateioMensalDespesas',
        ),
        migrations.AlterModelOptions(
            name='templateratiomensal',
            options={
                'verbose_name': 'Template de Rateio Mensal',
                'verbose_name_plural': 'Templates de Rateio Mensais'
            },
        ),
    ]
```

### **Fase 2: Adicionar Novos Campos**

```python
# Migration 002: Adicionar campos melhorados
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='templateratiomensal',
            name='nome_template',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='templateratiomensal',
            name='total_itens_configurados',
            field=models.PositiveIntegerField(default=0),
        ),
        # ... outros campos
        migrations.AddField(
            model_name='templateratiomensal',
            name='despesas_aplicadas',
            field=models.ManyToManyField(
                to='medicos.Despesa',
                blank=True,
                related_name='templates_rateio_utilizados'
            ),
        ),
    ]
```

### **Fase 3: Migração de Dados**

```python
# Migration 003: Migrar dados existentes
def migrar_dados_templates(apps, schema_editor):
    TemplateRateioMensalDespesas = apps.get_model('medicos', 'TemplateRateioMensalDespesas')
    
    for template in TemplateRateioMensalDespesas.objects.all():
        # Gerar nome automático se não existe
        if not template.nome_template:
            template.nome_template = f"Template {template.mes_referencia.strftime('%m/%Y')}"
        
        # Migrar status antigo para novo
        if template.status == 'finalizada':
            template.status = 'ativo'
        elif template.status == 'em_configuracao':
            template.status = 'em_edicao'
        
        template.save()
```

## 🎯 Conclusão

### **Benefícios da Mudança:**

1. ✅ **Nomenclatura Clara**: `TemplateRateioMensalDespesas` é autoexplicativo e específico
2. ✅ **Funcionalidade Expandida**: Controles de estado e validação
3. ✅ **Relacionamento Bidirecional**: Rastreamento completo com despesas
4. ✅ **Auditoria Completa**: Histórico detalhado de modificações
5. ✅ **Usabilidade**: Métodos úteis para operações comuns
6. ✅ **Manutenibilidade**: Código mais organizado e documentado

### **Impacto no Sistema:**

- **Compatibilidade**: Mantida através de migrations bem estruturadas
- **Performance**: Melhorada com indexação adequada e contadores automáticos  
- **Usabilidade**: Significativamente aprimorada para usuários finais
- **Desenvolvimento**: Mais fácil de entender e manter

### **Recomendação:**

✅ **APROVAÇÃO IMEDIATA** para implementação da melhoria proposta.

---

**📅 Documento gerado em:** Julho 2025  
**🎯 Status:** Proposta para aprovação e implementação  
**⏱️ Tempo estimado:** 2-3 semanas para implementação completa

---

### **Evolução da Nomenclatura:**

A nomenclatura do modelo passou por uma evolução lógica para maior precisão:

1. **Estado Inicial**: `ConfiguracaoRateioMensal` 
   - ❌ Problema: Nome genérico e ambíguo
   - ❌ Não indicava claramente a função de template
   
2. **Primeira Melhoria**: `TemplateRateioMensal`
   - ✅ Melhoria: Indicava claramente que é um template
   - ⚠️ Limitação: Ainda genérico, poderia ser qualquer tipo de rateio
   
3. **Versão Final**: `TemplateRateioMensalDespesas` ⭐
   - ✅ **Específico**: Deixa claro que é para rateio de despesas
   - ✅ **Escalável**: Permite futuras expansões (receitas, outros itens)
   - ✅ **Autodocumentado**: O nome explica completamente a função
   - ✅ **Domínio Claro**: Alinhado com o vocabulário do negócio

**Justificativa para a Especificidade:**
- Sistema pode expandir para outros tipos de rateio no futuro
- Elimina ambiguidade sobre o escopo do template
- Facilita manutenção e compreensão do código
- Segue boas práticas de nomenclatura em Domain-Driven Design (DDD)
