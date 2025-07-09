from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from .models import Conta, ContaMembership, Licenca
from .forms import TenantLoginForm, AccountSelectionForm, EmailAuthenticationForm, CustomUserCreationForm

# ---------------------------------------------
def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect('medicos:index')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

# ---------------------------------------------
def tenant_login(request):
    """
    Login multi-tenant - usuário faz login e depois seleciona a conta
    """
    if request.method == 'POST':
        form = TenantLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                
                # Verifica quantas contas o usuário tem acesso
                memberships = ContaMembership.objects.filter(user=user)
                
                if memberships.count() == 1:
                    # Se tem apenas uma conta, seleciona automaticamente
                    conta = memberships.first().conta
                    if conta.licenca.is_valida():
                        request.session['conta_ativa_id'] = conta.id
                        messages.success(request, f'Bem-vindo à {conta.name}!')
                        return redirect('/medicos/dashboard/')
                    else:
                        messages.error(request, f'Licença da conta {conta.name} expirou.')
                        return redirect('/medicos/auth/license-expired/')
                        
                elif memberships.count() > 1:
                    # Múltiplas contas - redireciona para seleção
                    return redirect('/medicos/auth/select-account/')
                else:
                    # Usuário sem contas
                    logout(request)
                    messages.error(request, 'Usuário não possui acesso a nenhuma conta.')
            else:
                messages.error(request, 'Email ou senha inválidos.')
    else:
        form = TenantLoginForm()
    
    return render(request, 'auth/login_tenant.html', {'form': form})

# ---------------------------------------------
def logout_view(request):
    logout(request)
    return redirect('/medicos/auth/login/')

# ---------------------------------------------
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Já cria usuário, conta, vínculo e licença
            return redirect('/medicos/auth/login/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

# ---------------------------------------------
@login_required
def select_account(request):
    """
    Seleção de conta para usuários com acesso a múltiplas contas
    """
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
    
    # Prepara dados das contas com informações de licença
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
@login_required
def switch_account(request):
    """
    Troca rápida de conta via AJAX
    """
    if request.method == 'POST':
        conta_id = request.POST.get('conta_id')
        
        try:
            membership = ContaMembership.objects.get(
                user=request.user, 
                conta_id=conta_id
            )
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
    """
    Página exibida quando a licença está expirada
    """
    return render(request, 'auth/license_expired.html')

# ---------------------------------------------
@login_required
def logout_view(request):
    """
    Logout que limpa a sessão de conta ativa
    """
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
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.is_active = True
                user.save()
                messages.success(request, 'Conta ativada com sucesso! Você já pode fazer login.')
                return redirect('auth:login_tenant')
        else:
            form = SetPasswordForm(user)
        return render(request, 'auth/set_password.html', {'form': form})
    else:
        messages.error(request, 'Link de ativação inválido ou expirado.')
        return render(request, 'auth/activation_invalid.html')

# ---------------------------------------------
def index(request):
    """
    Tela inicial do sistema: registro, login e informações básicas.
    """
    return render(request, 'auth/index.html')

# ---------------------------------------------
def password_reset_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='auth/password_reset_email.html',
                subject_template_name='auth/password_reset_subject.txt',
            )
            messages.success(request, 'E-mail de recuperação enviado. Verifique sua caixa de entrada.')
            return redirect('auth:login_tenant')
    else:
        form = PasswordResetForm()
    return render(request, 'auth/password_reset.html', {'form': form})