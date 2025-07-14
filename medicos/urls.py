from . import views_cenario
from django.urls import path
# ...existing code...
from . import views_user
from . import views_main
from . import views_relatorios
from . import views_empresa
from . import views_faturamento
from . import views_meio_pagamento
from . import views_faturamento
# from . import views_home_cenario  # Removido: arquivo não existe
# from . import views_dashboard_empresa  # Removido: arquivo não existe
from . import views_socio
from . import views_aliquota
from . import views_despesa
from django.contrib.auth import views as auth_views

app_name = 'medicos'

urlpatterns = [
    path('cenario_cadastro/', views_cenario.cenario_cadastro, name='cenario_cadastro'),
    path('', views_main.main, name='index'),
     path('dashboard/', views_main.main, name='dashboard'),
     path('home/', views_main.main, name='home'),

    path('relatorio-executivo/', views_relatorios.relatorio_executivo, name='relatorio_executivo'),
    path('relatorio-executivo/pdf/<int:conta_id>/', views_relatorios.relatorio_executivo_pdf, name='relatorio_executivo_pdf'),
    path('usuarios/', views_user.UserListView.as_view(), name='user_list'),
    path('usuarios/novo/', views_user.UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:user_id>/editar/', views_user.UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<int:user_id>/excluir/', views_user.UserDeleteView.as_view(), name='user_delete'),
    path('usuarios/<int:user_id>/', views_user.UserDetailView.as_view(), name='user_detail'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/medicos/auth/login/'), name='logout'),
    path('startempresa/<int:empresa_id>/', views_empresa.dashboard_empresa, name='startempresa'),
    path('empresa_create/nova/', views_empresa.empresa_create, name='empresa_create'),
    path('empresa_detail/<int:empresa_id>/detalhe/', views_empresa.empresa_detail, name='empresa_detail'),
    path('empresa_update/<int:empresa_id>/editar/', views_empresa.empresa_update, name='empresa_update'),
    path('empresa_delete/<int:empresa_id>/excluir/', views_empresa.empresa_delete, name='empresa_delete'),
    path('lista_socios_empresa/<int:empresa_id>/socios/', views_socio.SocioListView.as_view(), name='lista_socios_empresa'),
    path('socio_create/<int:empresa_id>/socios/novo/', views_socio.SocioCreateView.as_view(), name='socio_create'),
    path('socio_edit/<int:empresa_id>/socios/<int:socio_id>/editar/', views_socio.SocioUpdateView.as_view(), name='socio_edit'),
    path('socio_unlink/<int:empresa_id>/socios/<int:socio_id>/desvincular/', views_socio.SocioDeleteView.as_view(), name='socio_unlink'),
    path('lista_aliquotas/<int:empresa_id>/aliquotas/', views_aliquota.ListaAliquotasView.as_view(), name='lista_aliquotas'),
    path('aliquota_edit/<int:empresa_id>/aliquotas/<int:aliquota_id>/editar/', views_aliquota.aliquota_edit, name='aliquota_edit'),
    path('lista_grupos_despesa/<int:empresa_id>/grupos-despesa/', views_despesa.lista_grupos_despesa, name='lista_grupos_despesa'),
    path('grupo_despesa_edit/<int:empresa_id>/grupos-despesa/<int:grupo_id>/editar/', views_despesa.grupo_despesa_edit, name='grupo_despesa_edit'),
    path('item_despesa_create/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/novo/', views_despesa.item_despesa_create, name='item_despesa_create'),
    path('lista_itens_despesa/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/', views_despesa.ItemDespesaListView.as_view(), name='lista_itens_despesa'),
    path('item_despesa_edit/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/<int:item_id>/editar/', views_despesa.item_despesa_edit, name='item_despesa_edit'),
    path('item_despesa_delete/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/<int:item_id>/excluir/', views_despesa.item_despesa_delete, name='item_despesa_delete'),
    path('grupo_despesa_delete/<int:empresa_id>/grupos-despesa/<int:grupo_id>/excluir/', views_despesa.grupo_despesa_delete, name='grupo_despesa_delete'),
    path('lista_notas_fiscais/', views_faturamento.NotaFiscalListView.as_view(), name='lista_notas_fiscais'),
    path('criar_nota_fiscal/nova/', views_faturamento.NotaFiscalCreateView.as_view(), name='criar_nota_fiscal'),
path('cenario_faturamento/', views_cenario.cenario_faturamento, name='cenario_faturamento'),
    path('editar_nota_fiscal/<int:pk>/editar/', views_faturamento.NotaFiscalUpdateView.as_view(), name='editar_nota_fiscal'),
    path('excluir_nota_fiscal/<int:pk>/excluir/', views_faturamento.NotaFiscalDeleteView.as_view(), name='excluir_nota_fiscal'),

    # Meios de Pagamento
    path('lista_meios_pagamento/<int:empresa_id>/meios-pagamento/',
         views_meio_pagamento.MeioPagamentoListView.as_view(), name='lista_meios_pagamento'),
    path('criar_meio_pagamento/<int:empresa_id>/meios-pagamento/novo/',
         views_meio_pagamento.MeioPagamentoCreateView.as_view(), name='criar_meio_pagamento'),
    path('editar_meio_pagamento/<int:pk>/editar/',
         views_meio_pagamento.MeioPagamentoUpdateView.as_view(), name='editar_meio_pagamento'),
    path('excluir_meio_pagamento/<int:pk>/excluir/',
         views_meio_pagamento.MeioPagamentoDeleteView.as_view(), name='excluir_meio_pagamento'),
]
