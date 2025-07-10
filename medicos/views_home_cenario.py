from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home_cenario(request):
    return render(request, 'layouts/base_cenario_home.html')
