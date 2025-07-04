from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.auth import views as auth_views
from django.urls import path, include

#from medicos import views_organization

from . import views_auth
from . import views, views_despesas, views_relatorios, views_cadastro, views_nota_fiscal, views_financeiro
from . import report, views_empresas, views_aplicacoes

from medicos import views_user

app_name='medicos'

urlpatterns = [
    
    # SaaS Authentication URLs
    path('auth/', include('medicos.urls_auth')),
    
    # SaaS Dashboard URLs  
    path('dashboard/', include('medicos.urls_dashboard')),
    path('', include('medicos.urls_dashboard')),  # Dashboard como página inicial

    #---------------------------------------
    path('main/', views.index, name='index_old'),  # Manter compatibilidade

    #---------------------------------------    
    # VIEWS
    # --------------------------------------
    path('start/<int:fornecedor_id>/', views.start, name='start'),

    #---------------------------------------    
    # VIEWS_NOTA FISCAL
    # --------------------------------------

    #path('apuracao_mes/<int:num_mes>/', views_nota_fiscal.apuracao_mes, name='apuracao_mes'),
    path('faturamento/<int:fornecedor_id>/', views_nota_fiscal.faturamento, name='faturamento'),
    path('nf_incluir/', views_nota_fiscal.nf_incluir, name='nf_incluir'), 
    path('nf_editar/<int:notaFiscal_pk>/', views_nota_fiscal.nf_editar, name='nf_editar'), 
    path('nf_excluir/<int:notaFiscal_pk>/', views_nota_fiscal.nf_excluir, name='nf_excluir'), 
    path('NFiscal_TableView/<int:fornecedor_id>,<str:periodo_fiscal>/', views_nota_fiscal.NFiscal_TableView.as_view(), name='NFiscal_TableView'),

    #---------------------------------------    
    # VIEWS_FINANCEIRO
    # --------------------------------------

    path('financeiro_transferencia_incluir/', views_financeiro.financeiro_transferencia_incluir, name='financeiro_transferencia_incluir'),
    path('financeiro_NF_editar/<int:notaFiscal_pk>/', views_financeiro.financeiro_NF_editar, name='financeiro_NF_editar'), 
    path('financeiro_transferencia_editar/<int:financeiro_id>/', views_financeiro.financeiro_transferencia_editar, name='financeiro_transferencia_editar'), 
    path('financeiro_transacao_excluir/<int:financeiro_id>/', views_financeiro.financeiro_transacao_excluir, name='financeiro_transacao_excluir'), 
    path('Financeiro_Transferencias_TableView/', views_financeiro.Financeiro_Transferencias_TableView.as_view(), name='Financeiro_Transferencias_TableView'),
    path('notafiscal/<dtRecebimento>/', views_financeiro.Financeiro_TableView_Teste.as_view(), name='Financeiro_TableView_Teste'),
    path('notafiscal/', views_financeiro.Financeiro_TableView_Teste.as_view(), name='Financeiro_TableView_Teste'),
    path('financeiro_main/<int:fornecedor_id>/', views_financeiro.financeiro_main, name='financeiro_main'),


    #------------------------------------------
    # views_cadastro
    #------------------------------------------
    path('cadastro_main/', views_cadastro.cadastro_main, name='cadastro_main'),

    # CADASTRO EMPRESA
    path('cadastro_empresa/', views_cadastro.cadastro_empresa, name='cadastro_empresa'),
    path('empresa_incluir/', views_cadastro.empresa_incluir, name='empresa_incluir'), 
    path('empresa_editar/<int:id_empresa>/', views_cadastro.empresa_editar, name='empresa_editar'), 
    path('empresa_excluir/<int:id_empresa>/', views_cadastro.empresa_excluir, name='empresa_excluir'), 

    # CADASTRO PESSOA
    path('cadastro_pessoa/', views_cadastro.cadastro_pessoa, name='cadastro_pessoa'),
    path('pessoa_incluir/', views_cadastro.pessoa_incluir, name='pessoa_incluir'), 
    path('pessoa_editar/<int:id_pessoa>/', views_cadastro.pessoa_editar, name='pessoa_editar'), 
    path('pessoa_excluir/<int:id_pessoa>/', views_cadastro.pessoa_excluir, name='pessoa_excluir'),
 
    # CADASTRO SOCIO
    path('cadastro_societario/', views_cadastro.cadastro_societario, name='cadastro_societario'),
    path('societario_empresa/<int:id_empresa>/', views_cadastro.societario_empresa, name='societario_empresa'),     
    path('socio_incluir/<int:id_empresa>/', views_cadastro.socio_incluir, name='socio_incluir'),     
    path('socio_excluir/<int:id_pessoa>,<int:id_empresa>/', views_cadastro.socio_excluir, name='socio_excluir'),     

    # CADASTRO ALICOTAS
    path('cadastro_alicotas/', views_cadastro.cadastro_alicotas, name='cadastro_alicotas'),

    # CADASTRO GRUPO DESPESAS
    path('cadastro_despesa_grupo/', views_cadastro.cadastro_despesa_grupo, name='cadastro_despesa_grupo'),
    path('despesa_grupo_incluir/', views_cadastro.despesa_grupo_incluir, name='despesa_grupo_incluir'), 
    path('despesa_grupo_excluir/<int:id>/', views_cadastro.despesa_grupo_excluir, name='despesa_grupo_excluir'),     
    path('despesa_grupo_editar/<int:id>/', views_cadastro.despesa_grupo_editar, name='despesa_grupo_editar'), 

    # CADASTRO ITEM DESPESA
    path('cadastro_despesa_item/', views_cadastro.cadastro_despesa_item, name='cadastro_despesa_item'),
    path('despesa_item_incluir/', views_cadastro.despesa_item_incluir, name='despesa_item_incluir'), 
    path('despesa_item_excluir/<int:id>/', views_cadastro.despesa_item_excluir, name='despesa_item_excluir'),     
    path('despesa_item_editar/<int:id>/', views_cadastro.despesa_item_editar, name='despesa_item_editar'), 

    # CADASTRO DESCRICAO MOVIMENTACAO FINANCEIRA
    path('Cadastro_Desc_Mov_Financeiras_TableView/', views_cadastro.Cadastro_Desc_Mov_Financeiras_TableView.as_view(), name='Cadastro_Desc_Mov_Financeiras_TableView'),
    path('desc_mov_transferencia_incluir/', views_cadastro.desc_mov_transferencia_incluir, name='desc_mov_transferencia_incluir'), 
    path('desc_mov_transferencia_editar/<int:desc_id>/', views_cadastro.desc_mov_financeira_editar, name='desc_mov_financeira_editar'), 
    path('desc_mov_transferencia_excluir/<int:desc_id>/', views_cadastro.desc_mov_transferencia_excluir, name='desc_mov_transferencia_excluir'), 


    # DESPESAS COLETIVA
    path('despesas/', views_despesas.despesas, name='despesas'),
    path('despesa_detalhe_grupo/<int:item>/', views_despesas.despesa_detalhe_grupo, name='despesa_detalhe_grupo'),
    path('despesa_incluir/', views_despesas.despesa_incluir, name='despesa_incluir'),
    path('despesa_excluir/<int:id>/', views_despesas.despesa_excluir, name='despesa_excluir'),
    path('despesa_coletiva_editar/<int:despesa_id>/', views_despesas.despesa_coletiva_editar, name='despesa_coletiva_editar'),
    path('Despesas_TableView/', views_despesas.Despesas_TableView.as_view(), name='Despesas_TableView'),

    # DESPESAS RATEIO
    path('despesa_rateio/<int:mes>/', views_despesas.despesa_rateio, name='despesa_rateio'),
    path('despesa_rateio_socio/<int:socio_id>/', views_despesas.despesa_rateio_socio, name='despesa_rateio_socio'),

    # DESPESAS SOCIO
    path('despesa_socio/', views_despesas.despesa_socio, name='despesa_socio'), 
    path('despesa_socio_detail/<int:socio_id>/', views_despesas.despesa_socio_detail, name='despesa_socio_detail'), 
    path('despesa_socio_incluir/<int:socio_id>', views_despesas.despesa_socio_incluir, name='despesa_socio_incluir'),
    path('despesa_socio_excluir/<int:despesa_id>,<int:socio_id>/', views_despesas.despesa_socio_excluir, name='despesa_socio_excluir'),
    path('despesa_copiar/', views_despesas.despesa_copiar, name='despesa_copiar'),
    path('despesa_socio_editar/<int:despesa_id>/', views_despesas.despesa_socio_editar, name='despesa_socio_editar'),
        path('Despesas_Socio_View/<socio_id>', views_despesas.Despesas_Socio_View.as_view(), name='Despesas_Socio_View'),

    # RELATORIOS
    path('relatorios/', views_relatorios.relatorios, name='relatorios'),
    #path('relatorio_mensal_lista_socios/', views_relatorios.relatorio_mensal_lista_socios, name='relatorio_mensal_lista_socios'),
    path('relatorio_socio_mes/<int:socio_id>/', views_relatorios.relatorio_socio_mes, name='relatorio_socio_mes'),
    path('Demonstrativo_View/', views_relatorios.Demonstrativo_View.as_view(), name='Demonstrativo_View'),

    # APURACAO
    path('apuracao_pis/', views_relatorios.apuracao_pis, name='apuracao_pis'),
    path('apuracao_cofins/', views_relatorios.apuracao_cofins, name='apuracao_cofins'),  
    path('apuracao_csll_irpj/', views_relatorios.apuracao_csll_irpj, name='apuracao_csll_irpj'),
    path('apuracao_issqn/', views_relatorios.apuracao_issqn, name='apuracao_issqn'),
    path('relatorio_socio_ano/<int:socio_id>/', views_relatorios.relatorio_socio_ano, name='relatorio_socio_ano'),

    #---------------------------------------    
    # report
    # --------------------------------------
    path('gerar_relatorio_socio/<int:socio_id>/', report.gerar_relatorio_socio, name='gerar_relatorio_socio'),

    #---------------------------------------    
    # empresas
    # --------------------------------------
    path('empresas_main/', views_empresas.empresas_main, name='empresas_main'),
    path('PJuridica/', views_empresas.Empresas_View.as_view(), name='Empresas_View'),

    #---------------------------------------    
    # aplicacoes financeiras
    # --------------------------------------
    path('aplicacoes_mes/<int:id>/', views_aplicacoes.aplicacoes_mes, name='aplicacoes_mes'),
    path('Aplic_financeiras_TableView/', views_aplicacoes.Aplic_financeiras_TableView.as_view(), name='Aplic_financeiras_TableView'),
    
    # Rotas para gestão de organizações e membros (CBV)
    #path('organizations/create/', views_organization.OrganizationCreateView.as_view(), name='organization_create'),
    #path('organizations/<int:org_id>/', views_organization.OrganizationDetailView.as_view(), name='organization_detail'),
    #path('organizations/<int:org_id>/invite/', views_organization.OrganizationInviteMemberView.as_view(), name='invite_member'),
    #path('organizations/<int:org_id>/member/<int:membership_id>/update/', views_organization.OrganizationUpdateMemberRoleView.as_view(), name='update_member_role'),
    #path('organizations/<int:org_id>/member/<int:membership_id>/remove/', views_organization.OrganizationRemoveMemberView.as_view(), name='remove_member'),

]

urlpatterns += [
    # Gestão de usuários
    path('users/', views_user.UserListView.as_view(), name='user_list'),
    path('users/create/', views_user.UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/', views_user.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/edit/', views_user.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:user_id>/delete/', views_user.UserDeleteView.as_view(), name='user_delete'),
]