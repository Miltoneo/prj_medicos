from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import redirect
#from sitemaps import StaticViewSitemap
from django.contrib.auth import views as auth_views

#sitemaps = {'static': StaticViewSitemap}

urlpatterns = [
    path('', lambda request: redirect('medicos/', permanent=False)),  # Redireciona raiz para medicos
    path('medicos/', include('medicos.urls', namespace='medicos')),
    path('admin/', admin.site.urls), 
    path("select2/", include("django_select2.urls")), 
    #--sitemaps
    #path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
]
