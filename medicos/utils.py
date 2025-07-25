import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def send_invite_email(email, uid, token):
    # Monta o link de ativação (ajuste domínio conforme produção)
    # Padronizado: utilize o fluxo /auth/activate/<uidb64>/<token>/ conforme views_user.py
    activation_link = f"{settings.SITE_URL}/medicos/auth/activate/{uid}/{token}/"
    subject = 'Convite para acessar o sistema Medicos'
    message = f"Você foi convidado para acessar o sistema. Clique no link para ativar seu acesso: {activation_link}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
