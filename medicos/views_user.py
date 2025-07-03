from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserForm  # Certifique-se de ter esse formulário implementado

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

# -----------------------------------------------------------------------
class UserCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = User
    form_class = CustomUserForm
    template_name = "common/user_form.html"
    success_url = reverse_lazy('medicos:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Usuário criado com sucesso!")
        return response

# -----------------------------------------------------------------------
class UserUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserForm
    template_name = "common/user_form.html"
    success_url = reverse_lazy('medicos:user_list')
    pk_url_kwarg = "user_id"

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

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Usuário removido com sucesso!")
        return super().delete(request, *args, **kwargs)

# -----------------------------------------------------------------------
class UserDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = User
    template_name = "common/user_detail.html"
    context_object_name = "user_obj"
    pk_url_kwarg = "user_id"