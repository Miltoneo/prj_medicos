from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
# ---------------------------------------------
from django.views.decorators.csrf import csrf_protect
@csrf_protect
def resend_activation_view(request):
    message = error = email = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                message = 'Esta conta já está ativada. Faça login normalmente.'
            else:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                activation_link = f"{settings.SITE_URL}/medicos/auth/activate/{uid}/{token}/"
                from django.core.mail import send_mail
                send_mail(
                    'Ative sua conta',
                    f'Clique no link para ativar sua conta: {activation_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                message = 'E-mail de ativação reenviado! Verifique sua caixa de entrada e spam.'
        except User.DoesNotExist:
            error = 'E-mail não encontrado. Cadastre-se primeiro.'
        except Exception as e:
            error = f'Erro ao enviar e-mail: {e}'
    return render(request, 'auth/resend_activation.html', {'message': message, 'error': error, 'email': email})


# ---------------------------------------------
# IMPORTS NO TOPO (conforme guia de desenvolvimento)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.views.decorators.csrf import csrf_protect
from .models import Conta, ContaMembership, Licenca
from .forms import TenantLoginForm, AccountSelectionForm, EmailAuthenticationForm, CustomUserCreationForm

# ---------------------------------------------
@login_required
def select_account(request):
    memberships = ContaMembership.objects.filter(user=request.user).select_related('conta', 'conta__licenca')
    if request.method == 'POST':
        conta_id = request.POST.get('conta_id')
        try:
            membership = memberships.get(conta_id=conta_id)
            conta = membership.conta
            if conta.licenca.is_valida():
                request.session['conta_ativa_id'] = conta.id
                messages.success(request, f'Conta {conta.name} selecionada com sucesso!')
                return redirect('/medicos/dashboard/')
            else:
                messages.error(request, f'Licença da conta {conta.name} expirou em {conta.licenca.data_fim}.')
        except ContaMembership.DoesNotExist:
            messages.error(request, 'Acesso negado à conta selecionada.')
    contas_data = []
    for membership in memberships:
        conta = membership.conta
        licenca = conta.licenca
        contas_data.append({
            'conta': conta,
            'role': membership.get_role_display(),
            'licenca_valida': licenca.is_valida(),
            'licenca_expira': licenca.data_fim,
            'plano': licenca.plano,
            'membros_count': ContaMembership.objects.filter(conta=conta).count(),
            'limite_usuarios': licenca.limite_usuarios
        })
    return render(request, 'auth/select_account.html', {
        'contas_data': contas_data
    })

# ---------------------------------------------
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        print('DEBUG: POST recebido na view login_view')
        action = request.POST.get('action')
        print(f'DEBUG: action recebida = {action}')
        if action == 'login':
            print('DEBUG: processando login')
        elif action == 'register':
            print('DEBUG: processando registro')
    from .forms import CustomUserCreationForm
    from django.contrib.auth.forms import PasswordResetForm
    login_form = EmailAuthenticationForm()
    register_form = CustomUserCreationForm()
    password_reset_form = PasswordResetForm()
    show_register = False
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            login_form = EmailAuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = authenticate(
                    request,
                    username=login_form.cleaned_data['username'],
                    password=login_form.cleaned_data['password']
                )
                if user is not None:
                    login(request, user)
                    return redirect('medicos:index')
        elif action == 'register':
            register_form = CustomUserCreationForm(request.POST)
            show_register = True
            if register_form.is_valid():
                from django.contrib import messages
                import logging
                logger = logging.getLogger('auth.debug')
                try:
                    user = register_form.save(request=request)
                    logger.info(f"Novo registro de usuário: {user.email} (id={user.id}) - aguardando ativação.")
                    messages.success(request, 'Cadastro realizado! Verifique seu e-mail para ativar a conta.')
                    register_form = CustomUserCreationForm()  # Limpa o formulário
                except Exception as e:
                    logger.error(f"Erro no registro de usuário: {e}", exc_info=True)
                    messages.error(request, f'Erro ao enviar e-mail de ativação: {e}')
            else:
                import logging
                logger = logging.getLogger('auth.debug')
                logger.warning(f"Falha de validação no registro: {register_form.errors.as_json()}")
    return render(request, 'auth/login_register.html', {
        'login_form': login_form,
        'register_form': register_form,
        'password_reset_form': password_reset_form,
        'show_register': show_register,
    })

# ---------------------------------------------
@csrf_protect
def tenant_login(request):
    from .forms import CustomUserCreationForm
    from django.contrib.auth.forms import PasswordResetForm
    if request.method == 'POST':
        login_form = TenantLoginForm(request.POST)
        if login_form.is_valid():
            email = login_form.cleaned_data['email']
            password = login_form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                memberships = ContaMembership.objects.filter(user=user)
                if memberships.count() == 1:
                    conta = memberships.first().conta
                    if conta.licenca.is_valida():
                        request.session['conta_ativa_id'] = conta.id
                        messages.success(request, f'Bem-vindo à {conta.name}!')
                        return redirect('/medicos/dashboard/')
                    else:
                        messages.error(request, f'Licença da conta {conta.name} expirou.')
                        return redirect('/medicos/auth/license-expired/')
                elif memberships.count() > 1:
                    return redirect('/medicos/auth/select-account/')
                else:
                    logout(request)
                    messages.error(request, 'Usuário não possui acesso a nenhuma conta.')
            else:
                messages.error(request, 'Email ou senha inválidos.')
    else:
        login_form = TenantLoginForm()
    register_form = CustomUserCreationForm()
    password_reset_form = PasswordResetForm()
    return render(request, 'auth/login_register.html', {
        'login_form': login_form,
        'register_form': register_form,
        'password_reset_form': password_reset_form,
    })

# ---------------------------------------------
def logout_view(request):
    logout(request)
    return redirect('/medicos/auth/login/')

# ---------------------------------------------
import logging

@csrf_protect
def register_view(request):
    from .forms import EmailAuthenticationForm
    from django.contrib.auth.forms import PasswordResetForm
    logger = logging.getLogger('auth.debug')
    if request.method == 'POST' and request.POST.get('action') == 'register':
        login_form = EmailAuthenticationForm()
        register_form = CustomUserCreationForm(request.POST)
        password_reset_form = PasswordResetForm()
        if register_form.is_valid():
            from django.contrib import messages
            try:
                user = register_form.save(request=request)
                logger.info(f"Novo registro de usuário: {user.email} (id={user.id}) - aguardando ativação.")
                messages.success(request, 'Cadastro realizado! Verifique seu e-mail para ativar a conta.')
                register_form = CustomUserCreationForm()  # Limpa o formulário
            except Exception as e:
                logger.error(f"Erro no registro de usuário: {e}", exc_info=True)
                messages.error(request, f'Erro ao enviar e-mail de ativação: {e}')
        else:
            logger.warning(f"Falha de validação no registro: {register_form.errors.as_json()}")
    else:
        login_form = EmailAuthenticationForm()
        register_form = CustomUserCreationForm()
        password_reset_form = PasswordResetForm()
    return render(request, 'auth/login_register.html', {
        'login_form': login_form,
        'register_form': register_form,
        'password_reset_form': password_reset_form,
    })

# ---------------------------------------------
@csrf_protect
def password_reset_view(request):
    from .forms import EmailAuthenticationForm, CustomUserCreationForm
    login_form = EmailAuthenticationForm()
    register_form = CustomUserCreationForm()
    password_reset_form = PasswordResetForm(request.POST) if request.method == 'POST' else PasswordResetForm()
    if request.method == 'POST' and password_reset_form.is_valid():
        password_reset_form.save(
            request=request,
            use_https=request.is_secure(),
            email_template_name='auth/password_reset_email.html',
            subject_template_name='auth/password_reset_subject.txt',
        )
        messages.success(request, 'E-mail de recuperação enviado. Verifique sua caixa de entrada.')
        return redirect('/medicos/auth/login/')
    return render(request, 'auth/login_register.html', {
        'login_form': login_form,
        'register_form': register_form,
        'password_reset_form': password_reset_form,
    })

# ---------------------------------------------
@login_required
def switch_account(request):
    if request.method == 'POST':
        conta_id = request.POST.get('conta_id')
        try:
            membership = ContaMembership.objects.get(user=request.user, conta_id=conta_id)
            conta = membership.conta
            if conta.licenca.is_valida():
                request.session['conta_ativa_id'] = conta.id
                return JsonResponse({
                    'success': True,
                    'message': f'Conta alterada para {conta.name}',
                    'conta_name': conta.name
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Licença da conta {conta.name} expirou.'
                })
        except ContaMembership.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Acesso negado à conta selecionada.'
            })
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

# ---------------------------------------------
def license_expired(request):
    return render(request, 'auth/license_expired.html')

# ---------------------------------------------
@login_required
def logout_view(request):
    if 'conta_ativa_id' in request.session:
        del request.session['conta_ativa_id']
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('/medicos/auth/login/')

# ---------------------------------------------
def activate_account(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        from medicos.forms_set_password_with_name import SetPasswordWithNameForm
        if request.method == 'POST':
            form = SetPasswordWithNameForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.is_active = True
                user.save()
                messages.success(request, 'Conta ativada com sucesso! Você já pode fazer login.')
                return redirect('auth:login_tenant')
        else:
            form = SetPasswordWithNameForm(user)
        return render(request, 'auth/set_password.html', {'form': form})
    else:
        return render(request, 'auth/activation_invalid.html')

# ---------------------------------------------
def index(request):
    return render(request, 'auth/index.html')
