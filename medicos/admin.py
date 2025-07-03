from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Pessoa)
admin.site.register(Empresa)  # Substitui Pjuridica/Cliente
admin.site.register(Socio)
admin.site.register(NotaFiscal)
admin.site.register(Despesa)
