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
    list_display = ('numero', 'empresa_destinataria', 'tomador', 'get_tipo_aliquota_display', 'dtEmissao', 'val_bruto', 'val_liquido')
    list_filter = ('tipo_aliquota', 'dtEmissao', 'empresa_destinataria')
    search_fields = ('numero', 'tomador', 'empresa_destinataria__name')
    ordering = ('-dtEmissao', 'numero')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero', 'serie', 'empresa_destinataria', 'tomador')
        }),
        ('Tipo de Serviço', {
            'fields': ('tipo_aliquota',),
            'description': 'Selecione o tipo de serviço médico para aplicação das alíquotas corretas de ISS'
        }),
        ('Datas', {
            'fields': ('dtEmissao', 'dtRecebimento')
        }),
        ('Valores', {
            'fields': ('val_bruto', 'val_ISS', 'val_PIS', 'val_COFINS', 'val_IR', 'val_CSLL', 'val_liquido'),
            'classes': ('collapse',)
        })
    )
    
    def get_tipo_aliquota_display(self, obj):
        """Display service type with color coding"""
        colors = {
            'consultas': '#28a745',  # Green
            'plantao': '#007bff',    # Blue  
            'outros': '#ffc107'      # Yellow
        }
        color = colors.get(obj.tipo_aliquota, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_aliquota_display()
        )
    get_tipo_aliquota_display.short_description = 'Tipo de Serviço'

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

@admin.register(Desc_movimentacao_financeiro)
class DescMovimentacaoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'tipo_padrao', 'frequencia_uso', 'ativa')
    list_filter = ('categoria', 'tipo_padrao', 'ativa')
    search_fields = ('descricao', 'observacoes')
    ordering = ('categoria', 'descricao')
    
    fieldsets = (
        ('⚠️ DESCRIÇÕES PADRONIZADAS PARA SISTEMA MANUAL', {
            'fields': (),
            'description': 'Estas descrições são usadas EXCLUSIVAMENTE para lançamentos manuais no fluxo de caixa individual. '
                          'NÃO incluem rateio de notas fiscais, que são tratadas separadamente no sistema contábil.'
        }),
        ('Informações da Descrição', {
            'fields': ('descricao', 'categoria', 'tipo_padrao')
        }),
        ('Controle de Uso', {
            'fields': ('ativa', 'frequencia_uso')
        }),
        ('Orientações para Contabilidade', {
            'fields': ('observacoes',),
            'description': 'Instruções específicas sobre quando e como usar esta descrição',
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('frequencia_uso',)
    
    def save_model(self, request, obj, form, change):
        """Automaticamente definir o usuário criador"""
        if not change:  # Novo registro
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):
    list_display = ('data', 'socio', 'get_descricao_display', 'get_tipo_display', 'valor_formatado', 'status', 'origem_lancamento_manual')
    list_filter = ('tipo', 'status', 'transferencia_realizada', 'data', 'descricao__categoria')
    search_fields = ('socio__pessoa__name', 'descricao__descricao', 'observacoes')
    ordering = ('-data', '-created_at')
    
    fieldsets = (
        ('⚠️ SISTEMA MANUAL', {
            'fields': (),
            'description': 'IMPORTANTE: Todos os lançamentos neste sistema são MANUAIS e controlados pela contabilidade. '
                          'Receitas de notas fiscais são tratadas separadamente no sistema contábil.'
        }),
        ('Dados Básicos do Lançamento Manual', {
            'fields': ('data', 'empresa', 'socio', 'tipo', 'descricao', 'valor')
        }),
        ('Referências Documentais (Opcional)', {
            'fields': ('notafiscal', 'despesa'),
            'description': 'Documentos de referência APENAS para auditoria (não geram lançamentos automáticos)',
            'classes': ('collapse',)
        }),
        ('Documentação Comprobatória', {
            'fields': ('numero_documento', 'numero_autorizacao', 'banco_origem', 'forma_pagamento'),
            'classes': ('collapse',)
        }),
        ('Controle de Processamento Manual', {
            'fields': ('status', 'data_processamento', 'processado_por'),
            'classes': ('collapse',)
        }),
        ('Transferências Bancárias', {
            'fields': ('transferencia_realizada', 'data_transferencia', 'valor_transferido'),
            'classes': ('collapse',)
        }),
        ('Conciliação Bancária', {
            'fields': ('conciliado', 'data_conciliacao', 'conciliado_por'),
            'classes': ('collapse',)
        }),
        ('Observações e Auditoria', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('data_processamento', 'created_at', 'updated_at', 'operacao_auto')
    
    def get_readonly_fields(self, request, obj=None):
        """Campo operacao_auto sempre readonly (sempre False)"""
        readonly = list(self.readonly_fields)
        readonly.append('operacao_auto')
        return readonly
    
    def get_descricao_display(self, obj):
        """Display da descrição com categoria"""
        return f"[{obj.descricao.get_categoria_display()}] {obj.descricao.descricao}"
    get_descricao_display.short_description = 'Descrição Padronizada'
    
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
