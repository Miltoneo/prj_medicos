from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from medicos.models import ContaMembership

class LicencaValidaMiddleware:
    """
    Middleware para garantir que a conta do usuário possui licença válida.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignora admin e páginas de login/logout
        if request.path.startswith(reverse('admin:index')) or request.path.startswith(reverse('medicos:login')):
            return self.get_response(request)

        if request.user.is_authenticated:
            membership = ContaMembership.objects.filter(user=request.user).first()
            if membership:
                conta = membership.conta
                licenca = getattr(conta, 'licenca', None)
                if not licenca or not licenca.is_valida():
                    messages.error(request, "Sua licença está expirada ou inativa. Entre em contato com o suporte.")
                    return redirect('medicos:logout')  # ou redirecione para uma página de renovação/licenciamento

        return self.get_response(request)