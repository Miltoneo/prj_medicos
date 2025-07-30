from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from medicos.models.base import CustomUser  # Ajuste conforme o modelo real
from medicos.models import ContaMembership  # Ajuste conforme o modelo real
from medicos.forms_user_invite_form import UserInviteForm  # Corrigido: import do arquivo correto
from medicos.utils import send_invite_email  # Crie estes utilitários

class UserInviteView(CreateView):
    model = CustomUser
    form_class = UserInviteForm
    template_name = 'usuarios/invite_user.html'
    success_url = reverse_lazy('medicos:user_list')

    def form_valid(self, form):
        # Titulação obrigatória
        self.extra_context = getattr(self, 'extra_context', {})
        if not hasattr(self, 'extra_context') or self.extra_context is None:
            self.extra_context = {}
        self.extra_context['titulo_pagina'] = 'Convite de Usuário'

        email = form.cleaned_data.get('email')
        user_existente = CustomUser.objects.filter(email=email).first()

        if user_existente:
            if user_existente.is_active:
                messages.error(self.request, 'Já existe um usuário ativo com este endereço de e-mail.')
                return self.form_invalid(form)
            else:
                user = user_existente
                user.is_active = False
                user.save()
                messages.success(self.request, f"Convite reenviado para usuário inativo: {email}.")
                from django.contrib.auth.tokens import default_token_generator
                token = default_token_generator.make_token(user)
                convite_reenviado = True
        else:
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            from django.contrib.auth.tokens import default_token_generator
            token = default_token_generator.make_token(user)
            convite_reenviado = False

        conta_ativa = ContaMembership.objects.filter(user=self.request.user).first()
        if not conta_ativa:
            messages.error(self.request, 'Usuário autenticado não possui conta vinculada. Convite não pode ser realizado.')
            return self.form_invalid(form)

        if not ContaMembership.objects.filter(user=user, conta=conta_ativa.conta).exists():
            ContaMembership.objects.create(user=user, conta=conta_ativa.conta)

        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        try:
            send_invite_email(user.email, uid, token)
        except Exception as e:
            messages.error(self.request, f'Erro ao enviar e-mail: {str(e)}')
            return self.form_invalid(form)

        if convite_reenviado:
            messages.success(self.request, 'Convite reenviado para usuário inativo.')
        else:
            messages.success(self.request, 'Convite enviado com sucesso!')

        # Permanece na tela de convite após envio, renderizando o template com contexto atualizado
        return self.render_to_response(self.get_context_data(form=form))
