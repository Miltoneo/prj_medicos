from django.urls import path
# ...existing code...
from . import views_user
from . import views_main
from . import views_relatorios
from . import views_empresa
from . import views_faturamento
from . import views_meio_pagamento
from . import views_cenario
# from . import views_home_cenario  # Removido: arquivo não existe
# from . import views_dashboard_empresa  # Removido: arquivo não existe
from . import views_socio
from . import views_aliquota
from . import views_despesa
from django.contrib.auth import views as auth_views

app_name = 'medicos'

urlpatterns = [
    path('', views_main.main, name='index'),
path('dashboard/', views_main.main, name='dashboard'),
path('home/', views_main.main, name='home'),
    # path('cenario-home/', views_home_cenario.home_cenario, name='cenario_home'),  # Removido: views_home_cenario não existe
    # Dashboard SaaS (migrado de urls_dashboard.py)
    # path('', views_dashboard.dashboard_home, name='home'),
    # path('widgets/', views_dashboard.dashboard_widgets, name='widgets'),
    path('relatorio-executivo/', views_relatorios.relatorio_executivo, name='relatorio_executivo'),
    path('relatorio-executivo/pdf/<int:conta_id>/', views_relatorios.relatorio_executivo_pdf, name='relatorio_executivo_pdf'),
    path('usuarios/', views_user.UserListView.as_view(), name='user_list'),
    path('usuarios/novo/', views_user.UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:user_id>/editar/', views_user.UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<int:user_id>/excluir/', views_user.UserDeleteView.as_view(), name='user_delete'),
    path('usuarios/<int:user_id>/', views_user.UserDetailView.as_view(), name='user_detail'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/medicos/auth/login/'), name='logout'),
    path('empresas/', views_empresa.main, name='empresas'),
    path('empresas/nova/', views_empresa.empresa_create, name='empresa_create'),
    path('empresas/<int:empresa_id>/', views_empresa.empresa_detail, name='empresa_detail'),
    path('empresas/<int:empresa_id>/editar/', views_empresa.empresa_update, name='empresa_update'),
    path('empresas/<int:empresa_id>/excluir/', views_empresa.empresa_delete, name='empresa_delete'),
path('empresas/<int:empresa_id>/socios/', views_socio.lista_socios_empresa, name='lista_socios_empresa'),
    path('empresas/<int:empresa_id>/socios/novo/', views_socio.socio_create, name='socio_create'),
    path('empresas/<int:empresa_id>/socios/<int:socio_id>/editar/', views_socio.socio_edit, name='socio_edit'),
    path('empresas/<int:empresa_id>/socios/<int:socio_id>/desvincular/', views_socio.socio_unlink, name='socio_unlink'),
    path('empresas/<int:empresa_id>/aliquotas/', views_aliquota.ListaAliquotasView.as_view(), name='lista_aliquotas'),
    path('empresas/<int:empresa_id>/aliquotas/<int:aliquota_id>/editar/', views_aliquota.aliquota_edit, name='aliquota_edit'),
    path('empresas/<int:empresa_id>/grupos-despesa/', views_despesa.lista_grupos_despesa, name='lista_grupos_despesa'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/editar/', views_despesa.grupo_despesa_edit, name='grupo_despesa_edit'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/novo/', views_despesa.item_despesa_create, name='item_despesa_create'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/', views_despesa.ItemDespesaListView.as_view(), name='lista_itens_despesa'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/<int:item_id>/editar/', views_despesa.item_despesa_edit, name='item_despesa_edit'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/itens/<int:item_id>/excluir/', views_despesa.item_despesa_delete, name='item_despesa_delete'),
    path('empresas/<int:empresa_id>/grupos-despesa/<int:grupo_id>/excluir/', views_despesa.grupo_despesa_delete, name='grupo_despesa_delete'),
    path('notas-fiscais/', views_faturamento.NotaFiscalListView.as_view(), name='lista_notas_fiscais'),
    path('notas-fiscais/nova/', views_faturamento.NotaFiscalCreateView.as_view(), name='criar_nota_fiscal'),
    path('faturamento/', views_cenario.cenario_faturamento, name='cenario_faturamento'),
    path('notas-fiscais/<int:pk>/editar/', views_faturamento.NotaFiscalUpdateView.as_view(), name='editar_nota_fiscal'),
    path('notas-fiscais/<int:pk>/excluir/', views_faturamento.NotaFiscalDeleteView.as_view(), name='excluir_nota_fiscal'),

    # Meios de Pagamento
    path('empresas/<int:empresa_id>/meios-pagamento/',
         views_meio_pagamento.MeioPagamentoListView.as_view(), name='lista_meios_pagamento'),
    path('empresas/<int:empresa_id>/meios-pagamento/novo/',
         views_meio_pagamento.MeioPagamentoCreateView.as_view(), name='criar_meio_pagamento'),
    path('meios-pagamento/<int:pk>/editar/',
         views_meio_pagamento.MeioPagamentoUpdateView.as_view(), name='editar_meio_pagamento'),
    path('meios-pagamento/<int:pk>/excluir/',
         views_meio_pagamento.MeioPagamentoDeleteView.as_view(), name='excluir_meio_pagamento'),
]
