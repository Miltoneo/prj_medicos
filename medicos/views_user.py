from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from .models.base import ContaMembership, Conta
from .forms import CustomUserForm

User = get_user_model()

# -----------------------------------------------------------------------
class StaffRequiredMixin(UserPassesTestMixin):
    """Permite apenas staff/admin acessar a view."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para esta ação.")
        return reverse_lazy('medicos:user_list')

# -----------------------------------------------------------------------
class UserListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = User
    template_name = "common/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        # Filtra usuários do tenant (conta) atual
        conta_ids = ContaMembership.objects.filter(user=self.request.user, is_active=True).values_list('conta_id', flat=True)
        return User.objects.filter(conta_memberships__conta_id__in=conta_ids).distinct()

# -----------------------------------------------------------------------
class UserCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = User
    form_class = CustomUserForm
    template_name = "common/user_form.html"
    success_url = reverse_lazy('medicos:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Cria vínculo do novo usuário à mesma conta do usuário logado
        for membership in ContaMembership.objects.filter(user=self.request.user, is_active=True):
            ContaMembership.objects.create(
                conta=membership.conta,
                user=self.object,
                role='readonly',
                is_active=True,
                created_by=self.request.user
            )
        # Envia convite/ativação para o novo usuário
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.core.mail import send_mail
        from django.conf import settings
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
        return response

# -----------------------------------------------------------------------
class UserUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserForm
    template_name = "common/user_form.html"
    success_url = reverse_lazy('medicos:user_list')
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        conta_ids = ContaMembership.objects.filter(user=self.request.user, is_active=True).values_list('conta_id', flat=True)
        return User.objects.filter(conta_memberships__conta_id__in=conta_ids).distinct()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Usuário atualizado com sucesso!")
        return response

# -----------------------------------------------------------------------
class UserDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = User
    template_name = "common/user_confirm_delete.html"
    success_url = reverse_lazy('medicos:user_list')
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        conta_ids = ContaMembership.objects.filter(user=self.request.user, is_active=True).values_list('conta_id', flat=True)
        return User.objects.filter(conta_memberships__conta_id__in=conta_ids).distinct()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Usuário removido com sucesso!")
        return super().delete(request, *args, **kwargs)

# -----------------------------------------------------------------------
class UserDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = User
    template_name = "common/user_detail.html"
    context_object_name = "user_obj"
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        conta_ids = ContaMembership.objects.filter(user=self.request.user, is_active=True).values_list('conta_id', flat=True)
        return User.objects.filter(conta_memberships__conta_id__in=conta_ids).distinct()