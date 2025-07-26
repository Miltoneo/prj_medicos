




# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

# Imports locais
from .models.base import ContaMembership, Conta, CustomUser
from .forms import CustomUserForm
from core.context_processors import empresa_context

User = get_user_model()

"""
Views e helpers para gestão de usuários multi-tenant.
Organização dos imports conforme padrão do projeto.
Fonte: .github/copilot-instructions.md, seção 1
"""


# Helpers / Mixins
class StaffRequiredMixin(UserPassesTestMixin):
    """Permite apenas staff/admin acessar a view."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para esta ação.")
        from django.shortcuts import redirect
        return redirect('medicos:index')  # Redireciona para a home ou página pública

# Views

def get_empresa_from_request(request):
    # Use apenas o context processor para obter a empresa
    return empresa_context(request).get('empresa')

class UserListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    
    def get_context_data(self, **kwargs):
        conta_id = self.kwargs.get('conta_id')
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Usuários'
        context['cenario_nome'] = 'Home'
        context['conta_id'] = conta_id
        return context
    
    model = User
    template_name = "usuarios/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        conta_id = self.kwargs.get('conta_id')
        return User.objects.filter(conta_memberships__conta_id=conta_id).distinct()


class UserCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    def get_context_data(self, **kwargs):
        conta_id = self.kwargs.get('conta_id')
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Novo Usuário'
        context['cenario_nome'] = 'Usuários'
        context['conta_id'] = conta_id
        return context
    model = User
    form_class = CustomUserForm
    template_name = "usuarios/user_form.html"
    success_url = None

    def form_valid(self, form):
        response = super().form_valid(form)
        conta_id = self.kwargs.get('conta_id')
        conta = Conta.objects.get(id=conta_id)
        ContaMembership.objects.create(
            conta=conta,
            user=self.object,
            role='readonly',
            is_active=True,
            created_by=self.request.user
        )
        user = self.object
        user.is_active = False
        user.save()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.SITE_URL}/medicos/auth/activate/{uid}/{token}/"
        send_mail(
            'Ative sua conta',
            f'Olá,\n\nVocê foi convidado para acessar o sistema. Clique no link para ativar sua conta e definir sua senha: {activation_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(self.request, "Usuário criado com sucesso! Convite enviado por e-mail.")
        # Redireciona para a lista de usuários da conta
        from django.urls import reverse
        return redirect(reverse('medicos:lista_usuarios_conta', kwargs={'conta_id': conta_id}))


class UserUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        conta_id = self.kwargs.get('conta_id')
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Usuário'
        context['cenario_nome'] = 'Usuários'
        context['conta_id'] = conta_id
        return context
    model = User
    form_class = CustomUserForm
    template_name = "usuarios/user_form.html"
    success_url = None
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        conta_id = self.kwargs.get('conta_id')
        return User.objects.filter(conta_memberships__conta_id=conta_id).distinct()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Usuário atualizado com sucesso!")
        from django.urls import reverse
        return redirect(reverse('medicos:lista_usuarios_conta', kwargs={'conta_id': self.kwargs.get('conta_id')}))


class UserDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    def get_context_data(self, **kwargs):
        conta_id = self.kwargs.get('conta_id')
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Excluir Usuário'
        context['cenario_nome'] = 'Usuários'
        context['conta_id'] = conta_id
        return context
    model = User
    template_name = "usuarios/user_confirm_delete.html"
    success_url = None

    def get_success_url(self):
        return reverse('medicos:lista_usuarios_conta', kwargs={'conta_id': self.kwargs.get('conta_id')})
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        conta_id = self.kwargs.get('conta_id')
        return User.objects.filter(conta_memberships__conta_id=conta_id).distinct()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Usuário removido com sucesso!")
        from django.urls import reverse
        response = super().delete(request, *args, **kwargs)
        return redirect(reverse('medicos:lista_usuarios_conta', kwargs={'conta_id': self.kwargs.get('conta_id')}))


class UserDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    def get_context_data(self, **kwargs):
        conta_id = self.kwargs.get('conta_id')
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Detalhes do Usuário'
        context['cenario_nome'] = 'Usuários'
        context['conta_id'] = conta_id
        return context
    model = User
    template_name = "usuarios/user_detail.html"
    context_object_name = "user_obj"
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        conta_id = self.kwargs.get('conta_id')
        return User.objects.filter(conta_memberships__conta_id=conta_id).distinct()