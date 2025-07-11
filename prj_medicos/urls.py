from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import redirect
#from sitemaps import StaticViewSitemap
from django.contrib.auth import views as auth_views

#sitemaps = {'static': StaticViewSitemap}

urlpatterns = [
    path('', lambda request: redirect('medicos/', permanent=False)),  # Redireciona raiz para medicos
    path('medicos/', include(('medicos.urls', 'medicos'), namespace='medicos')),
    path('medicos/auth/', include(('medicos.urls_auth', 'auth'), namespace='auth')),
    path('admin/', admin.site.urls), 
    path("select2/", include("django_select2.urls")), 
    path('financeiro/', include('medicos.urls_financeiro', namespace='financeiro')),

]
