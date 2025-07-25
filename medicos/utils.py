import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def generate_invite_token(user):
    # Gera um token simples e salva no usuário (ajuste conforme modelo real)
    token = secrets.token_urlsafe(32)
    user.invite_token = token
    user.save()
    return token

def send_invite_email(email, uid, token):
    # Monta o link de ativação (ajuste domínio conforme produção)
    # Padronizado: utilize o fluxo /auth/activate/<uidb64>/<token>/ conforme views_user.py
    activation_link = f"{settings.SITE_URL}/medicos/auth/activate/{uid}/{token}/"
    subject = 'Convite para acessar o sistema Medicos'
    message = f"Você foi convidado para acessar o sistema. Clique no link para ativar seu acesso: {activation_link}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
