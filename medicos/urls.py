from . import views_cenario
from .views_rateio import (
    NotaFiscalRateioListView,
    NotaFiscalRateioMedicoCreateView,
    NotaFiscalRateioMedicoUpdateView,
    NotaFiscalRateioMedicoDeleteView,
)
from .views_rateio_medico import NotaFiscalRateioMedicoListView
from .views_financeiro_lancamentos import FinanceiroListView, FinanceiroCreateView, FinanceiroUpdateView, FinanceiroDeleteView
from .views_descricao_movimentacao import (
    DescricaoMovimentacaoFinanceiraListView,
    DescricaoMovimentacaoFinanceiraCreateView,
    DescricaoMovimentacaoFinanceiraUpdateView,
    DescricaoMovimentacaoFinanceiraDeleteView,
)
from django.urls import path, include
from .views_cadastro_rateio import (
    CadastroRateioView,
    CadastroRateioCreateView,
    CadastroRateioUpdateView,
    CadastroRateioDeleteView,
    cadastro_rateio_list,
)
from . import views_user_invite
from . import views_user
from . import views_main
from . import views_relatorios
from . import views_empresa
from . import views_faturamento
from .views_import_xml import NotaFiscalImportXMLView
from .views_recebimento_notafiscal import NotaFiscalRecebimentoListView, NotaFiscalRecebimentoUpdateView
from . import views_meio_pagamento
from . import views_faturamento
# from . import views_home_cenario  # Removido: arquivo não existe
# from . import views_dashboard_empresa  # Removido: arquivo não existe
from . import views_socio
from . import views_aliquota
from . import views_despesa_cadastro
from . import views_despesas
from . import urls_despesas

from .views_aplicacoes_financeiras import (
    AplicacaoFinanceiraListView,
    AplicacaoFinanceiraCreateView,
    AplicacaoFinanceiraUpdateView,
)
from django.contrib.auth import views as auth_views
from .views_auth import tenant_login


app_name = 'medicos'

# =====================
# Rateio Views
# =====================
urlpatterns = [
    # =====================
    # Configuração de Rateio Views
    # =====================
    path('cadastro/rateio/', cadastro_rateio_list, name='cadastro_rateio'),
    path('cadastro/rateio/novo/', CadastroRateioCreateView.as_view(), name='cadastro_rateio_create'),
    path('cadastro/rateio/<int:pk>/editar/', CadastroRateioUpdateView.as_view(), name='cadastro_rateio_update'),
    path('cadastro/rateio/<int:pk>/remover/', CadastroRateioDeleteView.as_view(), name='cadastro_rateio_delete'),
    # Rateio por Médico
    path('lista_rateio_medicos/<int:nota_id>/', NotaFiscalRateioMedicoListView.as_view(), name='lista_rateio_medicos'),
    path('novo_rateio_medico/<int:nota_id>/', NotaFiscalRateioMedicoCreateView.as_view(), name='novo_rateio_medico'),
    path('editar_rateio_medico/<int:nota_id>/<int:rateio_id>/', NotaFiscalRateioMedicoUpdateView.as_view(), name='editar_rateio_medico'),
    path('excluir_rateio_medico/<int:nota_id>/<int:rateio_id>/', NotaFiscalRateioMedicoDeleteView.as_view(), name='excluir_rateio_medico'),
    # Lista de Notas Rateio
    path('lista_notas_rateio/', NotaFiscalRateioListView.as_view(), name='lista_notas_rateio'),
    path('lista_notas_rateio_medicos/', NotaFiscalRateioMedicoListView.as_view(), name='lista_notas_rateio_medicos'),


    # =====================
    # Financeiro Views
    # =====================
    path('financeiro/lancamentos/', FinanceiroListView.as_view(), name='financeiro_lancamentos'),
    
    # Descrições de Movimentação Financeira
    path('empresas/<int:empresa_id>/descricoes-movimentacao/', DescricaoMovimentacaoFinanceiraListView.as_view(), name='lista_descricoes_movimentacao'),
    path('empresas/<int:empresa_id>/descricoes-movimentacao/novo/', DescricaoMovimentacaoFinanceiraCreateView.as_view(), name='descricao_movimentacao_create'),
    path('empresas/<int:empresa_id>/descricoes-movimentacao/<int:pk>/editar/', DescricaoMovimentacaoFinanceiraUpdateView.as_view(), name='descricao_movimentacao_edit'),
    path('empresas/<int:empresa_id>/descricoes-movimentacao/<int:pk>/excluir/', DescricaoMovimentacaoFinanceiraDeleteView.as_view(), name='descricao_movimentacao_delete'),
    
    # Lançamentos Financeiros CRUD
    path('empresas/<int:empresa_id>/lancamentos/novo/', FinanceiroCreateView.as_view(), name='financeiro_create'),
    path('empresas/<int:empresa_id>/lancamentos/<int:pk>/editar/', FinanceiroUpdateView.as_view(), name='financeiro_edit'),
    path('empresas/<int:empresa_id>/lancamentos/<int:pk>/excluir/', FinanceiroDeleteView.as_view(), name='financeiro_delete'),
    path('empresas/<int:empresa_id>/lancamentos/', FinanceiroListView.as_view(), name='lancamentos'),


    # =====================
    # Empresa Views
    # =====================
    path('lista_empresas/', views_empresa.EmpresaListView.as_view(), name='lista_empresas'),
    path('startempresa/<int:empresa_id>/', views_empresa.dashboard_empresa, name='startempresa'),
    path('empresa_create/nova/', views_empresa.empresa_create, name='empresa_create'),
    path('empresa_detail/<int:empresa_id>/detalhe/', views_empresa.empresa_detail, name='empresa_detail'),
    path('empresa_update/<int:empresa_id>/editar/', views_empresa.empresa_update, name='empresa_update'),
    path('empresa_delete/<int:empresa_id>/excluir/', views_empresa.empresa_delete, name='empresa_delete'),

    # =====================
    # Sócios da Empresa
    # =====================
    path('lista_socios_empresa/<int:empresa_id>/socios/', views_socio.SocioListView.as_view(), name='lista_socios_empresa'),
    path('socio_create/<int:empresa_id>/socios/novo/', views_socio.SocioCreateView.as_view(), name='socio_create'),

    # =====================
    # Usuário Views
    # =====================
    path('lista_usuarios_conta/<int:conta_id>/', views_user.UserListView.as_view(), name='lista_usuarios_conta'),
    path('usuarios/novo/', views_user.UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:user_id>/editar/', views_user.UserUpdateView.as_view(), name='user_update'),
path('usuarios/<int:conta_id>/<int:user_id>/excluir/', views_user.UserDeleteView.as_view(), name='user_delete'),
    path('usuarios/<int:user_id>/', views_user.UserDetailView.as_view(), name='user_detail'),
    path('usuarios/invite/', views_user_invite.UserInviteView.as_view(), name='user_invite'),

    # =====================
    # Sócio Views (Empresa)
    # =====================
    path('socio_edit/<int:empresa_id>/socios/<int:socio_id>/editar/', views_socio.SocioUpdateView.as_view(), name='socio_edit'),
    path('socio_unlink/<int:empresa_id>/socios/<int:socio_id>/desvincular/', views_socio.SocioDeleteView.as_view(), name='socio_unlink'),

    # =====================
    # Faturamento Views
    # =====================
    path('lista_notas_fiscais/', views_faturamento.NotaFiscalListView.as_view(), name='lista_notas_fiscais'),
    path('criar_nota_fiscal/nova/', views_faturamento.NotaFiscalCreateView.as_view(), name='criar_nota_fiscal'),
    path('importar_xml_nota_fiscal/', NotaFiscalImportXMLView.as_view(), name='importar_xml_nota_fiscal'),
    path('editar_nota_fiscal/<int:pk>/editar/', views_faturamento.NotaFiscalUpdateView.as_view(), name='editar_nota_fiscal'),
    path('excluir_nota_fiscal/<int:pk>/excluir/', views_faturamento.NotaFiscalDeleteView.as_view(), name='excluir_nota_fiscal'),
    path('cenario_faturamento/', views_cenario.cenario_faturamento, name='cenario_faturamento'),

    # Recebimento de Notas Fiscais (Fluxo Isolado do Financeiro)
    path('recebimento-notas/', NotaFiscalRecebimentoListView.as_view(), name='recebimento_notas_fiscais'),
    path('recebimento-notas/<int:pk>/editar/', NotaFiscalRecebimentoUpdateView.as_view(), name='editar_recebimento_nota_fiscal'),

    # =====================
    # Meios de Pagamento Views
    # =====================
    path('lista_meios_pagamento/<int:empresa_id>/meios-pagamento/', views_meio_pagamento.MeioPagamentoListView.as_view(), name='lista_meios_pagamento'),
    path('criar_meio_pagamento/<int:empresa_id>/meios-pagamento/novo/', views_meio_pagamento.MeioPagamentoCreateView.as_view(), name='criar_meio_pagamento'),
    path('editar_meio_pagamento/<int:pk>/editar/', views_meio_pagamento.MeioPagamentoUpdateView.as_view(), name='editar_meio_pagamento'),
    path('excluir_meio_pagamento/<int:pk>/excluir/', views_meio_pagamento.MeioPagamentoDeleteView.as_view(), name='excluir_meio_pagamento'),

    # =====================
    # Despesa Views
    # =====================

    # Cenário Despesas
    path('despesas/', include('medicos.urls_despesas')),

# Grupos de Despesa
path('empresas/<int:empresa_id>/grupos-despesa/', views_despesa_cadastro.lista_grupos_despesa, name='lista_grupos_despesa'),
path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/editar/', views_despesa_cadastro.grupo_despesa_edit, name='grupo_despesa_edit'),
path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/excluir/', views_despesa_cadastro.grupo_despesa_delete, name='grupo_despesa_delete'),

# Itens de Despesa (padronizado)
path('lista_itens_despesa/<int:empresa_id>/', views_despesa_cadastro.ItemDespesaListView.as_view(), name='lista_itens_despesa'),
path('item_despesa_create/<int:empresa_id>/', views_despesa_cadastro.ItemDespesaCreateView.as_view(), name='item_despesa_create'),
path('item_despesa_edit/<int:empresa_id>/<int:item_id>/', views_despesa_cadastro.ItemDespesaUpdateView.as_view(), name='item_despesa_edit'),
path('item_despesa_delete/<int:empresa_id>/<int:item_id>/', views_despesa_cadastro.ItemDespesaDeleteView.as_view(), name='item_despesa_delete'),

    # =====================
    # Aliquota Views
    # =====================
    path('aliquotas/<int:empresa_id>/', views_aliquota.ListaAliquotasView.as_view(), name='lista_aliquotas'),
    path('aliquotas/<int:empresa_id>/<int:aliquota_id>/editar/', views_aliquota.aliquota_edit, name='aliquota_edit'),

    # =====================
    # Cadastro e Cenário Views
    # =====================
    path('cenario_cadastro/', views_cenario.cenario_cadastro, name='cenario_cadastro'),
    path('', views_main.main, name='index'),
    path('dashboard/', views_main.main, name='dashboard'),
    path('home/', views_main.main, name='home'),

    # =====================
    # Relatórios Views
    # =====================
path('relatorio-executivo/<int:empresa_id>/', views_relatorios.relatorio_executivo, name='relatorio_executivo'),
    path('relatorio-mensal-empresa/<int:empresa_id>/', views_relatorios.relatorio_mensal_empresa, name='relatorio_mensal_empresa'),
    path('relatorio-mensal-socio/<int:empresa_id>/', views_relatorios.relatorio_mensal_socio, name='relatorio_mensal_socio'),
path('relatorio-issqn/<int:empresa_id>/', views_relatorios.relatorio_apuracao, name='relatorio_apuracao'),
    path('relatorio-outros/<int:empresa_id>/', views_relatorios.relatorio_outros, name='relatorio_outros'),

    # =====================
    # Autenticação
    # =====================
    path('logout/', auth_views.LogoutView.as_view(next_page='/medicos/auth/login/'), name='logout'),
    path('login/', tenant_login, name='login'),  # compatibilidade global para templates padrão Django
    # =====================
    # Aplicações Financeiras (Fluxo Isolado)
    # =====================
path('aplicacoes_financeiras/<int:empresa_id>/', AplicacaoFinanceiraListView.as_view(), name='aplicacoes_financeiras'),
path('aplicacao_financeira_add/<int:empresa_id>/', AplicacaoFinanceiraCreateView.as_view(), name='aplicacao_financeira_add'),
path('aplicacoes_financeiras_edit/<int:empresa_id>/<int:pk>/', AplicacaoFinanceiraUpdateView.as_view(), name='aplicacoes_financeiras_edit'),
]
