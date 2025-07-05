from django.contrib import admin
from django.utils.html import format_html

from .models import *

# Register your models here.

@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpf', 'email')
    search_fields = ('name', 'cpf', 'email')
    list_filter = ('created_at',)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'email', 'created_at')
    search_fields = ('name', 'cnpj', 'email')
    list_filter = ('created_at',)

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'empresa', 'ativo', 'data_entrada')
    search_fields = ('pessoa__name', 'empresa__name')
    list_filter = ('empresa', 'ativo', 'data_entrada')

@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ('numero', 'empresa_destinataria', 'tomador', 'get_tipo_aliquota_display', 'dtEmissao', 'val_bruto', 'val_liquido', 'get_status_recebimento_display', 'get_meio_pagamento_display')
    list_filter = ('tipo_aliquota', 'status_recebimento', 'status', 'dtEmissao', 'empresa_destinataria', 'meio_pagamento')
    search_fields = ('numero', 'tomador', 'empresa_destinataria__name', 'meio_pagamento__nome')
    ordering = ('-dtEmissao', 'numero')
    
    fieldsets = (
        ('📄 NOTA FISCAL', {
            'fields': (),
            'description': 'Gerenciamento de notas fiscais com sistema integrado de meios de pagamento cadastrados'
        }),
        ('Informações Básicas', {
            'fields': ('numero', 'serie', 'empresa_destinataria', 'tomador')
        }),
        ('Tipo de Serviço', {
            'fields': ('tipo_aliquota', 'descricao_servicos'),
            'description': 'Selecione o tipo de serviço médico para aplicação das alíquotas corretas de ISS'
        }),
        ('Datas', {
            'fields': ('dtEmissao', 'dtRecebimento', 'dtVencimento')
        }),
        ('Valores da Nota', {
            'fields': ('val_bruto', 'val_ISS', 'val_PIS', 'val_COFINS', 'val_IR', 'val_CSLL', 'val_liquido'),
            'classes': ('collapse',)
        }),
        ('💳 Recebimento', {
            'fields': ('status_recebimento', 'meio_pagamento', 'valor_recebido', 'numero_documento_recebimento', 'detalhes_recebimento'),
            'description': 'Controle de recebimento usando meios de pagamento cadastrados pelo usuário'
        }),
        ('Status e Controle', {
            'fields': ('status', 'ja_rateada', 'observacoes'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Otimizar consultas incluindo relacionamentos"""
        return super().get_queryset(request).select_related(
            'empresa_destinataria', 'meio_pagamento', 'conta'
        )
    
    def get_tipo_aliquota_display(self, obj):
        """Display service type with color coding"""
        colors = {
            1: '#28a745',  # Green - Consultas
            2: '#007bff',  # Blue - Plantão
            3: '#ffc107'   # Yellow - Outros
        }
        color = colors.get(obj.tipo_aliquota, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_aliquota_display()
        )
    get_tipo_aliquota_display.short_description = 'Tipo de Serviço'
    
    def get_status_recebimento_display(self, obj):
        """Display status with color coding"""
        colors = {
            'pendente': '#dc3545',     # Red
            'confirmado': '#28a745',   # Green
            'parcial': '#ffc107'       # Yellow
        }
        color = colors.get(obj.status_recebimento, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_recebimento_display()
        )
    get_status_recebimento_display.short_description = 'Status Recebimento'
    
    def get_meio_pagamento_display(self, obj):
        """Display meio de pagamento with info"""
        if obj.meio_pagamento:
            taxas_info = ""
            if obj.meio_pagamento.taxa_percentual > 0 or obj.meio_pagamento.taxa_fixa > 0:
                taxas_info = f" (taxa: {obj.meio_pagamento.taxa_percentual}%"
                if obj.meio_pagamento.taxa_fixa > 0:
                    taxas_info += f" + R${obj.meio_pagamento.taxa_fixa}"
                taxas_info += ")"
            
            return format_html(
                '<span title="{}"><strong>{}</strong>{}</span>',
                obj.meio_pagamento.descricao or 'Sem descrição',
                obj.meio_pagamento.nome,
                taxas_info
            )
        return format_html('<span style="color: #6c757d;">-</span>')
    get_meio_pagamento_display.short_description = 'Meio de Pagamento'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar meios de pagamento por conta do usuário"""
        if db_field.name == "meio_pagamento":
            # Aqui seria ideal filtrar por conta do usuário/nota fiscal
            # Por enquanto, mostrar apenas meios ativos que permitem crédito
            kwargs["queryset"] = MeioPagamento.objects.filter(
                ativo=True,
                tipo_movimentacao__in=['credito', 'ambos']
            ).select_related('conta')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Aliquotas)
class AliquotasAdmin(admin.ModelAdmin):
    list_display = ('conta', 'get_iss_rates', 'PIS', 'COFINS', 'IR', 'CSLL', 'data_vigencia_inicio', 'data_vigencia_fim')
    list_filter = ('data_vigencia_inicio', 'data_vigencia_fim', 'conta')
    search_fields = ('conta__empresa__name', 'observacoes')
    ordering = ('-data_vigencia_inicio',)
    
    fieldsets = (
        ('Conta', {
            'fields': ('conta',)
        }),
        ('ISS - Alíquotas por Tipo de Serviço', {
            'fields': ('ISS_CONSULTAS', 'ISS_PLANTAO', 'ISS_OUTROS'),
            'description': 'Alíquotas diferenciadas de ISS por tipo de serviço médico'
        }),
        ('Outros Impostos', {
            'fields': ('PIS', 'COFINS', 'IR', 'CSLL')
        }),
        ('Vigência', {
            'fields': ('data_vigencia_inicio', 'data_vigencia_fim')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    def get_iss_rates(self, obj):
        """Display ISS rates summary"""
        return format_html(
            'Consultas: {}% | Plantão: {}% | Outros: {}%',
            obj.ISS_CONSULTAS, obj.ISS_PLANTAO, obj.ISS_OUTROS
        )
    get_iss_rates.short_description = 'ISS por Tipo'

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('data', 'descricao', 'socio', 'tipo', 'valor')
    list_filter = ('tipo', 'data', 'socio')
    search_fields = ('descricao', 'socio__pessoa__name')
    ordering = ('-data',)

# Desc_movimentacao_financeiro admin removed - replaced by DescricaoMovimentacao

@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):
    list_display = ('data', 'socio', 'get_descricao_display', 'get_tipo_display', 'valor_formatado', 'status', 'origem_lancamento_manual')
    list_filter = ('tipo', 'status', 'transferencia_realizada', 'data', 'descricao__categoria')
    search_fields = ('socio__pessoa__name', 'descricao__descricao', 'observacoes')
    ordering = ('-data', '-created_at')
    
    fieldsets = (
        ('💰 SISTEMA FINANCEIRO MANUAL', {
            'fields': (),
            'description': 'Lançamentos manuais do fluxo de caixa individual com controle de meios de pagamento. '
                          'Receitas de notas fiscais são tratadas separadamente no sistema contábil.'
        }),
        ('Dados Básicos do Lançamento', {
            'fields': ('data', 'empresa', 'socio', 'tipo', 'descricao', 'valor')
        }),
        ('Meio de Pagamento e Taxas', {
            'fields': ('meio_pagamento', 'taxa_aplicada', 'valor_liquido_recebido'),
            'description': 'Informações sobre como o pagamento foi processado'
        }),
        ('Documentação', {
            'fields': ('numero_documento', 'observacoes'),
            'classes': ('collapse',)
        }),
        ('Referências (Opcional)', {
            'fields': ('notafiscal',),
            'description': 'Documentos de referência APENAS para auditoria',
            'classes': ('collapse',)
        }),
        ('Controle de Status', {
            'fields': ('status', 'lancado_por', 'aprovado_por', 'data_aprovacao'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'operacao_auto', 'ip_origem'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at', 'operacao_auto')
    
    def get_readonly_fields(self, request, obj=None):
        """Campo operacao_auto sempre readonly (sempre False)"""
        readonly = list(self.readonly_fields)
        readonly.append('operacao_auto')
        return readonly
    
    def get_descricao_display(self, obj):
        """Display da descrição com categoria"""
        if obj.descricao:
            return f"[{obj.descricao.get_categoria_display()}] {obj.descricao.nome}"
        elif obj.descricao_legacy:
            return f"[LEGACY] {obj.descricao_legacy.descricao}"
        return "Sem descrição"
    get_descricao_display.short_description = 'Descrição'
    
    def get_tipo_display(self, obj):
        """Display do tipo com cor"""
        if obj.tipo == obj.tipo_t.CREDITO:
            return format_html('<span style="color: green; font-weight: bold;">+ CRÉDITO</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">- DÉBITO</span>')
    get_tipo_display.short_description = 'Tipo'
    
    def valor_formatado(self, obj):
        """Valor formatado com sinal"""
        return obj.valor_formatado
    valor_formatado.short_description = 'Valor'
    
    def origem_lancamento_manual(self, obj):
        """Sempre mostra como manual"""
        return obj.origem_lancamento
    origem_lancamento_manual.short_description = 'Origem (Manual)'

@admin.register(SaldoMensalMedico)
class SaldoMensalMedicoAdmin(admin.ModelAdmin):
    list_display = ('mes_ano_formatado', 'socio', 'saldo_formatado', 'total_creditos', 'total_debitos', 'status')
    list_filter = ('mes_referencia', 'status', 'socio__empresa')
    search_fields = ('socio__pessoa__name',)
    ordering = ('-mes_referencia', 'socio__pessoa__name')
    
    fieldsets = (
        ('Identificação', {
            'fields': ('socio', 'mes_referencia', 'status')
        }),
        ('Resumo Financeiro', {
            'fields': ('saldo_inicial', 'total_creditos', 'total_debitos', 'saldo_final')
        }),
        ('Detalhamento de Créditos', {
            'fields': ('creditos_nf_consultas', 'creditos_nf_plantao', 'creditos_nf_outros', 'creditos_outros'),
            'classes': ('collapse',)
        }),
        ('Detalhamento de Débitos', {
            'fields': ('debitos_despesas_folha', 'debitos_despesas_gerais', 'debitos_despesas_individuais', 
                      'debitos_adiantamentos', 'debitos_impostos', 'debitos_outros'),
            'classes': ('collapse',)
        }),
        ('Controle de Transferências', {
            'fields': ('valor_disponivel_transferencia', 'valor_transferido'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('data_calculo', 'calculado_por'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('saldo_final', 'valor_disponivel_transferencia', 'data_calculo')
    
    actions = ['recalcular_saldos']
    
    def recalcular_saldos(self, request, queryset):
        """Action para recalcular saldos selecionados"""
        count = 0
        for saldo in queryset:
            saldo._recalcular_valores()
            count += 1
        
        self.message_user(request, f'{count} saldos recalculados com sucesso.')
    recalcular_saldos.short_description = "Recalcular saldos selecionados"

@admin.register(MeioPagamento)
class MeioPagamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo', 'categoria_display', 'taxa_info', 'prazo_compensacao_dias', 'disponivel_display', 'ativo')
    list_filter = ('ativo', 'tipo_movimentacao', 'data_inicio_vigencia', 'data_fim_vigencia')
    search_fields = ('nome', 'codigo', 'descricao')
    ordering = ('nome', 'codigo')
    
    fieldsets = (
        ('💳 MEIOS DE PAGAMENTO', {
            'fields': (),
            'description': 'Configuração dos meios de pagamento disponíveis para movimentações financeiras. '
                          'Estes meios controlam taxas, prazos e validações específicas para cada forma de pagamento.'
        }),
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao')
        }),
        ('Configurações Financeiras', {
            'fields': ('taxa_percentual', 'taxa_fixa', 'valor_minimo', 'valor_maximo')
        }),
        ('Prazos e Disponibilidade', {
            'fields': ('prazo_compensacao_dias', 'horario_limite', 'data_inicio_vigencia', 'data_fim_vigencia')
        }),
        ('Configurações de Uso', {
            'fields': ('tipo_movimentacao', 'exige_documento', 'exige_aprovacao')
        }),
        ('Status e Controle', {
            'fields': ('ativo', 'observacoes')
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def categoria_display(self, obj):
        """Mostra a categoria com base no tipo de movimentação"""
        if obj.tipo_movimentacao == 'credito':
            return format_html('<span style="color: green;">📈 Recebimentos</span>')
        elif obj.tipo_movimentacao == 'debito':
            return format_html('<span style="color: red;">📉 Pagamentos</span>')
        else:
            return format_html('<span style="color: blue;">🔄 Ambos</span>')
    categoria_display.short_description = 'Tipo'
    
    def taxa_info(self, obj):
        """Mostra informações sobre taxas"""
        partes = []
        if obj.taxa_percentual > 0:
            partes.append(f"{obj.taxa_percentual}%")
        if obj.taxa_fixa > 0:
            partes.append(f"R$ {obj.taxa_fixa}")
        
        if partes:
            return " + ".join(partes)
        return "Sem taxa"
    taxa_info.short_description = 'Taxas'
    
    def disponivel_display(self, obj):
        """Mostra se está disponível para uso"""
        if obj.disponivel_para_uso:
            return format_html('<span style="color: green;">✅ Sim</span>')
        else:
            return format_html('<span style="color: red;">❌ Não</span>')
    disponivel_display.short_description = 'Disponível'
    
    def save_model(self, request, obj, form, change):
        """Automaticamente definir o usuário criador"""
        if not change:  # Novo registro
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(DescricaoMovimentacao)
class DescricaoMovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria_display', 'tipo_movimentacao_display', 'uso_frequente_display', 'ativa_display', 'exige_documento', 'exige_aprovacao')
    list_filter = ('categoria', 'tipo_movimentacao', 'ativa', 'uso_frequente', 'exige_documento', 'exige_aprovacao')
    search_fields = ('nome', 'descricao', 'codigo_contabil')
    ordering = ('categoria', 'nome')
    
    fieldsets = (
        ('📝 DESCRIÇÕES DE MOVIMENTAÇÃO - GERENCIADAS PELO USUÁRIO', {
            'fields': (),
            'description': 'Descrições personalizadas criadas pelos usuários para categorizar movimentações financeiras. '
                          'Permite total flexibilidade na organização e classificação dos lançamentos.'
        }),
        ('Identificação', {
            'fields': ('nome', 'descricao', 'categoria')
        }),
        ('Configurações de Uso', {
            'fields': ('tipo_movimentacao', 'uso_frequente', 'ativa')
        }),
        ('Validações e Controles', {
            'fields': ('exige_documento', 'exige_aprovacao'),
            'classes': ('collapse',)
        }),
        ('Configurações Contábeis/Fiscais', {
            'fields': ('codigo_contabil', 'possui_retencao_ir', 'percentual_retencao_ir'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def categoria_display(self, obj):
        """Mostra a categoria com ícone"""
        categoria_icons = {
            'receita_servicos': '💼',
            'receita_outros': '💰',
            'adiantamento_recebido': '⬆️',
            'emprestimo_recebido': '🏦',
            'despesa_operacional': '🏢',
            'despesa_pessoal': '👤',
            'adiantamento_concedido': '⬇️',
            'emprestimo_concedido': '🏦',
            'transferencia_recebida': '📥',
            'transferencia_enviada': '📤',
            'ajuste_credito': '✅',
            'ajuste_debito': '❌',
            'taxa_encargo': '💳',
            'aplicacao_financeira': '📈',
            'resgate_aplicacao': '📉',
            'outros': '📋',
        }
        icon = categoria_icons.get(obj.categoria, '📋')
        return format_html(f'{icon} {obj.get_categoria_display()}')
    categoria_display.short_description = 'Categoria'
    
    def tipo_movimentacao_display(self, obj):
        """Mostra o tipo de movimentação com cor"""
        if obj.tipo_movimentacao == 'credito':
            return format_html('<span style="color: green; font-weight: bold;">📈 Créditos</span>')
        elif obj.tipo_movimentacao == 'debito':
            return format_html('<span style="color: red; font-weight: bold;">📉 Débitos</span>')
        else:
            return format_html('<span style="color: blue; font-weight: bold;">🔄 Ambos</span>')
    tipo_movimentacao_display.short_description = 'Tipo'
    
    def uso_frequente_display(self, obj):
        """Mostra se é uso frequente"""
        if obj.uso_frequente:
            return format_html('<span style="color: orange;">⭐ Sim</span>')
        return "Não"
    uso_frequente_display.short_description = 'Frequente'
    
    def ativa_display(self, obj):
        """Mostra se está ativa"""
        if obj.ativa:
            return format_html('<span style="color: green;">✅ Ativa</span>')
        else:
            return format_html('<span style="color: red;">❌ Inativa</span>')
    ativa_display.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Automaticamente definir o usuário criador"""
        if not change:  # Novo registro
            obj.criada_por = request.user
        super().save_model(request, obj, form, change)
